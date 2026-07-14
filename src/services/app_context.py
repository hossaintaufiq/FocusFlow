"""
Application context — wires storage, services, and shared state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

from src.models.settings import Settings
from src.services.achievement_service import AchievementService
from src.services.backup import BackupService
from src.services.extras_service import ExtrasService
from src.services.habit_service import HabitService
from src.services.history_service import HistoryService
from src.services.note_service import NoteService
from src.services.notification_service import NotificationService
from src.services.project_service import ProjectService
from src.services.settings_service import SettingsService
from src.services.stats_service import StatsService
from src.services.storage import JsonStorage
from src.services.task_service import TaskService
from src.services.timer_service import TimerService
from src.utils.config import APP_VERSION, QUOTES, ThemeColors
from src.utils.paths import ensure_directories

logger = logging.getLogger("FocusFlow.context")


class AppSignals(QObject):
    """Cross-page refresh bus."""

    data_changed = Signal(str)  # entity type hint
    navigate = Signal(str)  # page id
    toast = Signal(str)


@dataclass
class AppContext:
    """Central dependency container passed to the UI layer."""

    storage: JsonStorage
    backup: BackupService
    history: HistoryService
    settings_svc: SettingsService
    tasks: TaskService
    projects: ProjectService
    habits: HabitService
    notes: NoteService
    timers: TimerService
    stats: StatsService
    extras: ExtrasService
    achievements: AchievementService
    notifications: NotificationService
    signals: AppSignals
    version: str = APP_VERSION
    _reminder_timer: Any = field(default=None, repr=False)

    @property
    def settings(self) -> Settings:
        return self.settings_svc.settings

    @property
    def theme(self) -> ThemeColors:
        return self.settings_svc.theme_colors()

    def emit_change(self, kind: str = "all") -> None:
        self.signals.data_changed.emit(kind)

    def active_task(self):
        """Task currently linked to the Pomodoro timer, if any."""
        active = self.timers.active
        tid = active.task_id or active.suspended_task_id
        return self.tasks.get(tid) if tid else None

    def start_task_focus(self, task_id: str, *, navigate: bool = True) -> bool:
        """
        Start a Pomodoro slice for a task using its planned daily/total time.
        Returns False if the task is missing or already completed.
        """
        task = self.tasks.get(task_id)
        if not task or task.completed:
            self.signals.toast.emit("Task not available for focus")
            return False

        seconds = task.pomodoro_session_seconds(self.settings.focus_minutes)
        if task.status == "not_started":
            self.tasks.update(task_id, status="in_progress")

        was_suspended = (
            self.timers.active.suspended_kind == "task"
            and self.timers.active.suspended_task_id == task_id
        )
        self.timers.start_task_session(task_id, seconds)
        if was_suspended:
            self.signals.toast.emit(f"Focus resumed: {task.title}")
        else:
            self.signals.toast.emit(f"Focus started: {task.title}")
        self.emit_change("timers")
        if navigate:
            self.signals.navigate.emit("pomodoro")
        return True

    def toggle_task_done(self, task_id: str | None = None) -> bool:
        """Mark linked task complete/incomplete without stopping the timer."""
        tid = task_id or self.timers.active.task_id or self.timers.active.suspended_task_id
        if not tid:
            return False
        task = self.tasks.get(tid)
        if not task:
            return False
        was_done = task.completed
        self.tasks.toggle_complete(tid)
        if not was_done:
            self.stats.record_task_completed(task.category)
            self.achievements.on_task_completed(
                self.stats.store.lifetime_tasks_completed
            )
        self.projects.refresh_counts()
        self.emit_change("tasks")
        msg = "Task marked done" if not was_done else "Task reopened"
        self.signals.toast.emit(msg)
        return True

    def daily_quote(self) -> str:
        if not self.settings.daily_quote_enabled:
            return ""
        from datetime import date

        idx = date.today().toordinal() % len(QUOTES)
        return QUOTES[idx]

    def manual_save(self) -> None:
        """Force-persist every store."""
        flush = getattr(self, "_flush_focus_buffer", None)
        if callable(flush):
            flush()
        self.tasks.save()
        self.projects.save()
        self.habits.save()
        self.notes.save()
        self.timers.save()
        self.stats.save()
        self.extras.save()
        self.achievements.save()
        self.settings_svc.save()
        self.history.save()
        self.signals.toast.emit("All data saved")

    def save_all(self) -> None:
        self.manual_save()

    def reload_from_disk(self) -> None:
        """Reload all service stores from JSON (e.g. after backup restore)."""
        from src.models.achievements import AchievementsStore
        from src.models.extras import ExtrasStore
        from src.models.habit import HabitCollection
        from src.models.history import HistoryCollection
        from src.models.note import NoteCollection
        from src.models.project import ProjectCollection
        from src.models.settings import Settings
        from src.models.stats import StatsStore
        from src.models.task import TaskCollection
        from src.models.timer import TimerStore

        self.tasks._data = self.storage.load(
            "tasks", TaskCollection.from_dict, TaskCollection
        )
        self.projects._data = self.storage.load(
            "projects", ProjectCollection.from_dict, ProjectCollection
        )
        self.projects.set_task_service(self.tasks)
        self.projects.refresh_counts()
        self.habits._data = self.storage.load(
            "habits", HabitCollection.from_dict, HabitCollection
        )
        self.habits.recalculate_streaks()
        self.notes._data = self.storage.load(
            "notes", NoteCollection.from_dict, NoteCollection
        )
        self.timers._data = self.storage.load(
            "timers", TimerStore.from_dict, TimerStore
        )
        if self.timers._data.active_timer is None:
            from src.models.timer import ActiveTimer

            self.timers._data.active_timer = ActiveTimer()
        self.stats._data = self.storage.load(
            "stats", StatsStore.from_dict, StatsStore
        )
        self.extras._data = self.storage.load(
            "extras", ExtrasStore.from_dict, ExtrasStore
        )
        self.achievements._data = self.storage.load(
            "achievements", AchievementsStore.from_dict, AchievementsStore
        )
        self.history._data = self.storage.load(
            "history", HistoryCollection.from_dict, HistoryCollection
        )
        self.settings_svc.settings = self.storage.load(
            "settings", Settings.from_dict, Settings
        )
        self.notifications.enabled = self.settings.notifications_enabled
        self.notifications.sound_enabled = self.settings.sound_enabled
        self.emit_change("all")

    @classmethod
    def create(cls) -> "AppContext":
        ensure_directories()
        storage = JsonStorage()
        backup = BackupService()
        history = HistoryService(storage)
        settings_svc = SettingsService(storage)
        tasks = TaskService(storage, history)
        projects = ProjectService(storage, history, tasks)
        projects.set_task_service(tasks)
        projects.refresh_counts()
        habits = HabitService(storage, history)
        notes = NoteService(storage, history)
        stats = StatsService(storage)
        extras = ExtrasService(storage)
        achievements = AchievementService(storage)
        notifications = NotificationService(
            enabled=settings_svc.settings.notifications_enabled,
            sound_enabled=settings_svc.settings.sound_enabled,
        )

        focus_buffer = {"secs": 0, "task_id": ""}

        def flush_focus_buffer() -> None:
            if focus_buffer["secs"] <= 0:
                return
            # Stats already updated in-memory each second; just persist
            stats.flush()
            if focus_buffer["task_id"]:
                tasks.save()
            achievements.flush_focus_xp()
            focus_buffer["secs"] = 0

        def on_focus_second(task_id: str, seconds: int) -> None:
            category = ""
            project_id = ""
            if task_id:
                task = tasks.get(task_id)
                if task:
                    category = task.category
                    project_id = task.project_id
            stats.record_focus_seconds(
                seconds, category=category, project_id=project_id, persist=False
            )
            if task_id:
                tasks.add_time(task_id, seconds, persist=False)
                focus_buffer["task_id"] = task_id
            focus_buffer["secs"] += seconds
            achievements.on_focus_seconds(stats.store.lifetime_focus_seconds, seconds)
            # Flush dependent stores every 10 focus seconds
            if focus_buffer["secs"] >= 10:
                flush_focus_buffer()

        timers = TimerService(storage, history, on_focus_second=on_focus_second)
        timers.last_completed_seconds = 0

        signals = AppSignals()

        def on_timer_finished(kind: str) -> None:
            flush_focus_buffer()
            elapsed = int(getattr(timers, "last_completed_seconds", 0) or 0)
            if elapsed:
                stats.set_longest_session(elapsed)
            if kind in ("focus", "task", "custom"):
                if kind == "focus":
                    stats.record_pomodoro()
                notifications.focus_complete()
                pomodoros = sum(
                    1
                    for s in timers.sessions
                    if s.kind in ("focus", "task") and s.completed
                )
                achievements.on_pomodoro(pomodoros)
                if kind == "task" and timers.active.task_id:
                    notifications.notify(
                        "Focus slice done",
                        "You can mark the task done or start another slice.",
                    )
            elif kind in ("short_break", "long_break"):
                notifications.break_reminder()
                if timers.has_suspended_focus():
                    timers.resume_suspended_focus()
                    notifications.notify(
                        "Break over",
                        "Resuming your focus session.",
                    )
            signals.data_changed.emit("timers")

        timers.finished.connect(on_timer_finished)

        ctx = cls(
            storage=storage,
            backup=backup,
            history=history,
            settings_svc=settings_svc,
            tasks=tasks,
            projects=projects,
            habits=habits,
            notes=notes,
            timers=timers,
            stats=stats,
            extras=extras,
            achievements=achievements,
            notifications=notifications,
            signals=signals,
        )
        ctx._flush_focus_buffer = flush_focus_buffer

        # Daily backup + history boot mark
        if settings_svc.settings.auto_backup:
            try:
                backup.ensure_daily_backup()
            except Exception as exc:
                logger.warning("Daily backup failed: %s", exc)
        history.log("app_started", entity_type="system", summary="FocusFlow started")

        # Sync habit/streak stats
        cur, longest = habits.best_streaks()
        stats.update_streaks(cur, longest)
        stats.record_habit(
            sum(1 for h in habits.habits if h.is_completed_on()),
            len(habits.habits),
        )

        # Periodic reminders (check every 15 min)
        reminder = QTimer()
        reminder.setInterval(15 * 60 * 1000)
        reminder.timeout.connect(ctx._check_reminders)
        reminder.start()
        ctx._reminder_timer = reminder

        # Apply startup registry if configured
        if settings_svc.settings.launch_on_startup:
            settings_svc.apply_startup(True)

        return ctx

    def _check_reminders(self) -> None:
        from datetime import datetime

        now = datetime.now()
        # Morning reminder once around 8–9
        if (
            self.settings.morning_reminder
            and now.hour == 8
            and now.minute < 15
        ):
            self.notifications.morning_reminder()
        # Evening summary around 20:00
        if (
            self.settings.evening_summary
            and now.hour == 20
            and now.minute < 15
        ):
            counts = self.tasks.counts_today()
            focus = self.timers.focus_totals()["today"] // 60
            self.notifications.evening_summary(counts["completed"], focus)
        # Deadline reminders
        for task in self.tasks.upcoming(20):
            if task.deadline and task.deadline[:10] == now.date().isoformat():
                if now.hour in (9, 12, 17) and now.minute < 15:
                    self.notifications.deadline_reminder(task.title)
