"""Statistics aggregation and productivity score (0–100)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.models.base import today_iso
from src.models.stats import DayStats, StatsStore
from src.services.storage import JsonStorage


class StatsService:
    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage
        self._data = storage.load("stats", StatsStore.from_dict, StatsStore)

    @property
    def store(self) -> StatsStore:
        return self._data

    def save(self) -> None:
        self._storage.save("stats", self._data)

    def day(self, day: str | None = None) -> DayStats:
        return self._data.get_or_create_day(day)

    def record_task_completed(self, category: str = "") -> None:
        d = self.day()
        d.tasks_completed += 1
        self._data.lifetime_tasks_completed += 1
        if category:
            d.category_minutes[category] = d.category_minutes.get(category, 0) + 0
        self._recompute_score(d)
        self.save()

    def record_task_created(self) -> None:
        d = self.day()
        d.tasks_created += 1
        self.save()

    def record_focus_seconds(
        self,
        seconds: int,
        category: str = "",
        project_id: str = "",
        *,
        persist: bool = True,
    ) -> None:
        d = self.day()
        d.focus_seconds += seconds
        self._data.lifetime_focus_seconds += seconds
        if category:
            d.category_minutes[category] = d.category_minutes.get(category, 0) + seconds / 60.0
        if project_id:
            d.project_minutes[project_id] = d.project_minutes.get(project_id, 0) + seconds / 60.0
        self._recompute_score(d)
        if persist:
            self.save()

    def flush(self) -> None:
        self.save()

    def record_pomodoro(self) -> None:
        d = self.day()
        d.pomodoro_count += 1
        self.save()

    def record_habit(self, completed: int, total: int) -> None:
        d = self.day()
        d.habits_completed = completed
        d.habits_total = total
        self._recompute_score(d)
        self.save()

    def set_longest_session(self, seconds: int) -> None:
        d = self.day()
        d.longest_session_seconds = max(d.longest_session_seconds, int(seconds))
        self.save()

    def update_streaks(self, current: int, longest: int) -> None:
        self._data.current_streak = current
        self._data.longest_streak = max(self._data.longest_streak, longest)
        self.save()

    def _recompute_score(self, d: DayStats) -> None:
        # Weighted productivity score 0–100
        task_score = min(40.0, d.tasks_completed * 8)
        focus_score = min(30.0, (d.focus_seconds / 3600.0) * 15)
        habit_score = 0.0
        if d.habits_total:
            habit_score = 20.0 * (d.habits_completed / d.habits_total)
        streak_score = min(10.0, self._data.current_streak * 1.5)
        score = round(task_score + focus_score + habit_score + streak_score, 1)
        d.productivity_score = min(100.0, score)
        self._data.productivity_scores[d.date] = d.productivity_score

    def productivity_today(self) -> float:
        return self.day().productivity_score

    def series(
        self,
        metric: str = "tasks_completed",
        days: int = 7,
    ) -> tuple[list[str], list[float]]:
        labels: list[str] = []
        values: list[float] = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            labels.append(d[5:])  # MM-DD
            day = self._data.daily.get(d)
            if not day:
                values.append(0.0)
                continue
            if metric == "focus_hours":
                values.append(round(day.focus_seconds / 3600.0, 2))
            elif metric == "productivity_score":
                values.append(day.productivity_score)
            elif metric == "habits":
                values.append(float(day.habits_completed))
            else:
                values.append(float(getattr(day, metric, 0)))
        return labels, values

    def category_distribution(self, days: int = 30) -> dict[str, float]:
        today = date.today()
        dist: dict[str, float] = {}
        for i in range(days):
            d = (today - timedelta(days=i)).isoformat()
            day = self._data.daily.get(d)
            if not day:
                continue
            for cat, mins in day.category_minutes.items():
                dist[cat] = dist.get(cat, 0.0) + mins
        return dist

    def summary(self) -> dict[str, Any]:
        d = self.day()
        return {
            "tasks_completed_today": d.tasks_completed,
            "focus_seconds_today": d.focus_seconds,
            "productivity_score": d.productivity_score,
            "lifetime_focus_seconds": self._data.lifetime_focus_seconds,
            "lifetime_tasks_completed": self._data.lifetime_tasks_completed,
            "current_streak": self._data.current_streak,
            "longest_streak": self._data.longest_streak,
            "longest_session_seconds": d.longest_session_seconds,
            "average_focus_today": (
                d.focus_seconds / max(1, d.pomodoro_count) if d.pomodoro_count else d.focus_seconds
            ),
        }
