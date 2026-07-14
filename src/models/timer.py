"""Timer and Pomodoro session models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, new_id, utc_now_iso


@dataclass
class TimerSession(JsonMixin):
    """A recorded focus / break session."""

    id: str = field(default_factory=lambda: new_id("session"))
    # focus | short_break | long_break | custom | task
    kind: str = "focus"
    task_id: str = ""
    started_at: str = field(default_factory=utc_now_iso)
    ended_at: str = ""
    planned_seconds: int = 25 * 60
    elapsed_seconds: int = 0
    completed: bool = False
    interrupted: bool = False
    notes: str = ""


@dataclass
class ActiveTimer(JsonMixin):
    """In-progress timer state persisted so crashes can recover."""

    task_id: str = ""
    kind: str = "focus"  # focus | short_break | long_break | custom | task
    status: str = "idle"  # idle | running | paused
    started_at: str = ""
    paused_at: str = ""
    planned_seconds: int = 25 * 60
    elapsed_seconds: int = 0
    pomodoro_count: int = 0  # completed focus sessions in current cycle
    # Focus slice preserved while a break is running
    suspended_kind: str = ""
    suspended_task_id: str = ""
    suspended_planned_seconds: int = 0
    suspended_elapsed_seconds: int = 0
    suspended_started_at: str = ""

    def is_running(self) -> bool:
        return self.status == "running"

    def is_paused(self) -> bool:
        return self.status == "paused"


@dataclass
class TimerStore(JsonMixin):
    """Root document for ``timers.json``."""

    version: int = 1
    active_timer: ActiveTimer | None = None
    sessions: list[TimerSession] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "active_timer": self.active_timer.to_dict() if self.active_timer else None,
            "sessions": [s.to_dict() for s in self.sessions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimerStore:
        raw_active = data.get("active_timer")
        active = ActiveTimer.from_dict(raw_active) if isinstance(raw_active, dict) else None
        sessions = [TimerSession.from_dict(s) for s in data.get("sessions", [])]
        return cls(
            version=int(data.get("version", 1)),
            active_timer=active,
            sessions=sessions,
        )
