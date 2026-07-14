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

    def daily_quote(self) -> str:
        if not self.settings.daily_quote_enabled:
            return ""
        from datetime import date

        idx = date.today().toordinal() % len(QUOTES)
        return QUOTES[idx]

    def manual_save(self) -> None:
        """Force-persist every store."""
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

        def on_focus_second(task_id: str, seconds: int) -> None:
            stats.record_focus_seconds(seconds)
            if task_id:
                tasks.add_time(task_id, seconds)
            achievements.on_focus_seconds(stats.store.lifetime_focus_seconds, 0)

        timers = TimerService(storage, history, on_focus_second=on_focus_second)

        def on_timer_finished(kind: str) -> None:
            if kind == "focus":
                stats.record_pomodoro()
                notifications.focus_complete()
                pomodoros = sum(
                    1 for s in timers.sessions if s.kind == "focus" and s.completed
                )
                achievements.on_pomodoro(pomodoros)
            elif kind in ("short_break", "long_break"):
                notifications.break_reminder()

        timers.finished.connect(on_timer_finished)

        signals = AppSignals()
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
