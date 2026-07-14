"""Task timer and Pomodoro engine with per-second persistence."""

from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from src.models.base import utc_now_iso
from src.models.timer import ActiveTimer, TimerSession, TimerStore
from src.services.history_service import HistoryService
from src.services.storage import JsonStorage

logger = logging.getLogger("FocusFlow.timer")


class TimerService(QObject):
    tick = Signal(int)  # elapsed seconds
    finished = Signal(str)  # kind
    state_changed = Signal(str)  # status

    def __init__(
        self,
        storage: JsonStorage,
        history: HistoryService,
        on_focus_second: Callable[[str, int], None] | None = None,
    ) -> None:
        super().__init__()
        self._storage = storage
        self._history = history
        self._on_focus_second = on_focus_second
        self._data = storage.load("timers", TimerStore.from_dict, TimerStore)
        if self._data.active_timer is None:
            self._data.active_timer = ActiveTimer()
        self._dirty = False
        self._ticks_since_save = 0
        self._persist_every_n = 10  # write timers.json every N seconds while running
        self._qtimer = QTimer(self)
        self._qtimer.setInterval(1000)
        self._qtimer.timeout.connect(self._on_tick)
        if self._data.active_timer.status == "running":
            self._qtimer.start()

    @property
    def active(self) -> ActiveTimer:
        assert self._data.active_timer is not None
        return self._data.active_timer

    @property
    def sessions(self) -> list[TimerSession]:
        return list(self._data.sessions)

    def save(self) -> None:
        self._storage.save("timers", self._data)
        self._dirty = False
        self._ticks_since_save = 0

    def start(
        self,
        *,
        kind: str = "focus",
        planned_seconds: int = 25 * 60,
        task_id: str = "",
    ) -> ActiveTimer:
        active = self.active
        if active.status in ("running", "paused") and active.elapsed_seconds > 0:
            self.stop()
        active = self.active
        active.kind = kind
        active.task_id = task_id if kind == "task" else ""
        active.planned_seconds = planned_seconds
        active.elapsed_seconds = 0
        active.status = "running"
        active.started_at = utc_now_iso()
        active.paused_at = ""
        self._qtimer.start()
        self.save()
        summary = f"Started {kind} timer"
        if task_id and kind == "task":
            summary = f"Started task focus ({planned_seconds // 60} min slice)"
        self._history.log(
            "timer_started",
            entity_type="timer",
            entity_id=task_id,
            summary=summary,
        )
        self.state_changed.emit("running")
        return active

    def start_task_session(
        self,
        task_id: str,
        planned_seconds: int,
    ) -> ActiveTimer:
        """Start a Pomodoro focus slice bound to a task."""
        return self.start(kind="task", planned_seconds=planned_seconds, task_id=task_id)

    def restart_task_session(self, planned_seconds: int) -> ActiveTimer | None:
        """Start another focus slice for the already-linked task."""
        if not self.active.task_id:
            return None
        return self.start(
            kind="task",
            planned_seconds=planned_seconds,
            task_id=self.active.task_id,
        )

    def pause(self) -> ActiveTimer:
        active = self.active
        if active.status != "running":
            return active
        active.status = "paused"
        active.paused_at = utc_now_iso()
        self._qtimer.stop()
        self.save()
        self._history.log("timer_paused", entity_type="timer", summary="Paused timer")
        self.state_changed.emit("paused")
        return active

    def resume(self) -> ActiveTimer:
        active = self.active
        if active.status != "paused":
            return active
        active.status = "running"
        active.paused_at = ""
        self._qtimer.start()
        self.save()
        self._history.log("timer_resumed", entity_type="timer", summary="Resumed timer")
        self.state_changed.emit("running")
        return active

    def stop(self) -> TimerSession | None:
        active = self.active
        session = TimerSession(
            kind=active.kind,
            task_id=active.task_id,
            started_at=active.started_at or utc_now_iso(),
            ended_at=utc_now_iso(),
            planned_seconds=active.planned_seconds,
            elapsed_seconds=active.elapsed_seconds,
            completed=False,
            interrupted=True,
        )
        self._data.sessions.insert(0, session)
        task_id = active.task_id
        kind = active.kind
        elapsed = active.elapsed_seconds
        self.reset(persist_session=False)
        self.save()
        self._history.log(
            "timer_stopped",
            entity_type="timer",
            entity_id=task_id,
            summary=f"Stopped {kind} ({elapsed}s)",
        )
        self.state_changed.emit("idle")
        return session

    def reset(self, persist_session: bool = True, *, clear_task: bool = True) -> None:
        active = self.active
        active.status = "idle"
        active.elapsed_seconds = 0
        active.started_at = ""
        active.paused_at = ""
        if clear_task:
            active.task_id = ""
            active.kind = "focus"
        self._qtimer.stop()
        self.save()
        if persist_session:
            self._history.log("timer_reset", entity_type="timer", summary="Reset timer")
        self.state_changed.emit("idle")

    def toggle(self) -> None:
        if self.active.status == "running":
            self.pause()
        elif self.active.status == "paused":
            self.resume()
        else:
            self.start()

    def remaining_seconds(self) -> int:
        active = self.active
        return max(0, active.planned_seconds - active.elapsed_seconds)

    def _on_tick(self) -> None:
        active = self.active
        if active.status != "running":
            return
        active.elapsed_seconds += 1
        self._dirty = True
        self._ticks_since_save += 1
        # Persist periodically (and always on pause/stop/complete)
        if self._ticks_since_save >= self._persist_every_n:
            self.save()
        self.tick.emit(active.elapsed_seconds)
        if self._on_focus_second and active.kind in ("focus", "task", "custom"):
            self._on_focus_second(active.task_id, 1)
        if active.elapsed_seconds >= active.planned_seconds:
            self._complete_session()

    def _complete_session(self) -> None:
        active = self.active
        session = TimerSession(
            kind=active.kind,
            task_id=active.task_id,
            started_at=active.started_at or utc_now_iso(),
            ended_at=utc_now_iso(),
            planned_seconds=active.planned_seconds,
            elapsed_seconds=active.elapsed_seconds,
            completed=True,
            interrupted=False,
        )
        self._data.sessions.insert(0, session)
        kind = active.kind
        elapsed = active.elapsed_seconds
        task_id = active.task_id
        if kind in ("focus", "task"):
            active.pomodoro_count += 1
            self._history.log(
                "pomodoro_completed",
                entity_type="timer",
                entity_id=task_id,
                summary="Task focus slice done" if kind == "task" else "Pomodoro completed",
            )
        self._qtimer.stop()
        active.status = "idle"
        active.elapsed_seconds = 0
        active.started_at = ""
        # Keep task linked after a slice so user can mark done or start another slice
        if kind != "task":
            active.task_id = ""
        self.save()
        self.state_changed.emit("idle")
        self.finished.emit(kind)
        self.last_completed_seconds = elapsed

    def focus_totals(self) -> dict[str, int]:
        """Return focus seconds: today, week, month, lifetime."""
        from datetime import date, timedelta

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        totals = {"today": 0, "week": 0, "month": 0, "lifetime": 0, "lifetime_all": 0}
        for s in self._data.sessions:
            if s.kind not in ("focus", "task", "custom"):
                continue
            totals["lifetime"] += s.elapsed_seconds
            try:
                d = date.fromisoformat(s.started_at[:10])
            except ValueError:
                continue
            if d == today:
                totals["today"] += s.elapsed_seconds
            if d >= week_start:
                totals["week"] += s.elapsed_seconds
            if d >= month_start:
                totals["month"] += s.elapsed_seconds
        totals["lifetime_all"] = totals["lifetime"]
        # include active running focus time
        if self.active.status in ("running", "paused") and self.active.kind in (
            "focus",
            "task",
            "custom",
        ):
            totals["today"] += self.active.elapsed_seconds
        return totals
