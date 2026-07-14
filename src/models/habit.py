"""Habit domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, new_id, today_iso, utc_now_iso


@dataclass
class Habit(JsonMixin):
    """Trackable habit with frequency and completion log."""

    id: str = field(default_factory=lambda: new_id("habit"))
    name: str = ""
    description: str = ""
    # daily | weekly | monthly
    frequency: str = "daily"
    color: str = "#34D399"
    icon: str = "flame"
    target_count: int = 1  # times per period
    # ISO date strings when the habit was completed
    completions: list[str] = field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    archived: bool = False
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def is_completed_on(self, day: str | None = None) -> bool:
        day = day or today_iso()
        return day in self.completions

    def mark_done(self, day: str | None = None) -> None:
        day = day or today_iso()
        if day not in self.completions:
            self.completions.append(day)
            self.completions.sort()
            self.updated_at = utc_now_iso()

    def mark_undone(self, day: str | None = None) -> None:
        day = day or today_iso()
        if day in self.completions:
            self.completions.remove(day)
            self.updated_at = utc_now_iso()

    @property
    def completion_rate(self) -> float:
        """Rough lifetime completion % based on days since creation (capped)."""
        if not self.completions:
            return 0.0
        try:
            created = self.created_at[:10]
            from datetime import date as _date

            start = _date.fromisoformat(created)
            days = max(1, (_date.today() - start).days + 1)
            return round(100.0 * len(self.completions) / days, 1)
        except ValueError:
            return 0.0


@dataclass
class HabitCollection(JsonMixin):
    """Root document for ``habits.json``."""

    version: int = 1
    habits: list[Habit] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "habits": [h.to_dict() for h in self.habits],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HabitCollection:
        habits = [Habit.from_dict(h) for h in data.get("habits", [])]
        return cls(version=int(data.get("version", 1)), habits=habits)
