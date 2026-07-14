"""Statistics and productivity-score models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, today_iso


@dataclass
class DayStats(JsonMixin):
    """Aggregated metrics for a single calendar day."""

    date: str = field(default_factory=today_iso)
    tasks_completed: int = 0
    tasks_created: int = 0
    focus_seconds: int = 0
    pomodoro_count: int = 0
    habits_completed: int = 0
    habits_total: int = 0
    productivity_score: float = 0.0
    longest_session_seconds: int = 0
    category_minutes: dict[str, float] = field(default_factory=dict)
    project_minutes: dict[str, float] = field(default_factory=dict)


@dataclass
class StatsStore(JsonMixin):
    """Root document for ``stats.json``."""

    version: int = 1
    daily: dict[str, DayStats] = field(default_factory=dict)  # date -> DayStats
    weekly: dict[str, dict[str, Any]] = field(default_factory=dict)
    monthly: dict[str, dict[str, Any]] = field(default_factory=dict)
    yearly: dict[str, dict[str, Any]] = field(default_factory=dict)
    lifetime_focus_seconds: int = 0
    lifetime_tasks_completed: int = 0
    productivity_scores: dict[str, float] = field(default_factory=dict)
    current_streak: int = 0
    longest_streak: int = 0

    def get_or_create_day(self, day: str | None = None) -> DayStats:
        day = day or today_iso()
        if day not in self.daily:
            self.daily[day] = DayStats(date=day)
        return self.daily[day]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "daily": {k: v.to_dict() for k, v in self.daily.items()},
            "weekly": self.weekly,
            "monthly": self.monthly,
            "yearly": self.yearly,
            "lifetime_focus_seconds": self.lifetime_focus_seconds,
            "lifetime_tasks_completed": self.lifetime_tasks_completed,
            "productivity_scores": self.productivity_scores,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatsStore:
        raw_daily = data.get("daily", {})
        daily: dict[str, DayStats] = {}
        for key, value in raw_daily.items():
            if isinstance(value, dict):
                daily[key] = DayStats.from_dict(value)
        return cls(
            version=int(data.get("version", 1)),
            daily=daily,
            weekly=dict(data.get("weekly", {})),
            monthly=dict(data.get("monthly", {})),
            yearly=dict(data.get("yearly", {})),
            lifetime_focus_seconds=int(data.get("lifetime_focus_seconds", 0)),
            lifetime_tasks_completed=int(data.get("lifetime_tasks_completed", 0)),
            productivity_scores={
                str(k): float(v) for k, v in data.get("productivity_scores", {}).items()
            },
            current_streak=int(data.get("current_streak", 0)),
            longest_streak=int(data.get("longest_streak", 0)),
        )
