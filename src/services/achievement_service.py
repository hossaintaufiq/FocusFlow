"""XP, levels, badges, and achievement unlocking."""

from __future__ import annotations

from src.models.achievements import AchievementsStore, BADGE_CATALOG
from src.services.storage import JsonStorage


class AchievementService:
    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage
        self._data = storage.load(
            "achievements", AchievementsStore.from_dict, AchievementsStore
        )

    @property
    def store(self) -> AchievementsStore:
        return self._data

    def save(self) -> None:
        self._storage.save("achievements", self._data)

    def on_task_completed(self, lifetime_completed: int) -> list[str]:
        unlocked: list[str] = []
        self._data.award_task_xp()
        if lifetime_completed >= 1 and self._data.unlock_badge("first_task"):
            unlocked.append("first_task")
        if lifetime_completed >= 10 and self._data.unlock_badge("tasks_10"):
            unlocked.append("tasks_10")
        if lifetime_completed >= 100 and self._data.unlock_badge("tasks_100"):
            unlocked.append("tasks_100")
        self.save()
        return unlocked

    def on_focus_seconds(self, lifetime_seconds: int, session_seconds: int = 0) -> list[str]:
        unlocked: list[str] = []
        if session_seconds:
            self._data.award_focus_minutes(session_seconds // 60)
        if lifetime_seconds >= 3600 and self._data.unlock_badge("focus_1h"):
            unlocked.append("focus_1h")
        if lifetime_seconds >= 36000 and self._data.unlock_badge("focus_10h"):
            unlocked.append("focus_10h")
        self.save()
        return unlocked

    def on_habit_completed(self) -> None:
        self._data.award_habit_xp()
        self.save()

    def on_pomodoro(self, total: int) -> list[str]:
        unlocked: list[str] = []
        if total >= 10 and self._data.unlock_badge("pomodoro_10"):
            unlocked.append("pomodoro_10")
        self.save()
        return unlocked

    def on_streak(self, current: int) -> list[str]:
        unlocked: list[str] = []
        if current > 0:
            self._data.award_streak_day()
        if current >= 7 and self._data.unlock_badge("streak_7"):
            unlocked.append("streak_7")
        if current >= 30 and self._data.unlock_badge("streak_30"):
            unlocked.append("streak_30")
        self.save()
        return unlocked

    def on_notes_created(self, count: int) -> list[str]:
        unlocked: list[str] = []
        if count >= 10 and self._data.unlock_badge("note_taker"):
            unlocked.append("note_taker")
        self.save()
        return unlocked

    def badge_meta(self, badge_id: str) -> dict[str, str]:
        return BADGE_CATALOG.get(badge_id, {"name": badge_id, "description": ""})
