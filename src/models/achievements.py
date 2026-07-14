"""Achievements, XP, levels, and badges."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, utc_now_iso
from src.utils.config import XP_PER_FOCUS_MINUTE, XP_PER_HABIT, XP_PER_STREAK_DAY, XP_PER_TASK

# XP required to reach level N (simple curve: 100 * n^1.5 approx via table)
LEVEL_XP_THRESHOLDS: tuple[int, ...] = tuple(
    int(100 * (n ** 1.5)) for n in range(1, 51)
)


def level_for_xp(xp: int) -> int:
    """Compute level (1-based) from total XP."""
    level = 1
    for idx, threshold in enumerate(LEVEL_XP_THRESHOLDS, start=1):
        if xp >= threshold:
            level = idx
        else:
            break
    return max(1, level)


def xp_for_next_level(xp: int) -> tuple[int, int]:
    """Return ``(current_level_floor, next_level_threshold)``."""
    level = level_for_xp(xp)
    floor = LEVEL_XP_THRESHOLDS[level - 1] if level >= 1 else 0
    nxt = (
        LEVEL_XP_THRESHOLDS[level]
        if level < len(LEVEL_XP_THRESHOLDS)
        else LEVEL_XP_THRESHOLDS[-1]
    )
    return floor, nxt


# Catalog of unlockable badges (id -> metadata)
BADGE_CATALOG: dict[str, dict[str, str]] = {
    "first_task": {"name": "Getting Started", "description": "Complete your first task"},
    "tasks_10": {"name": "Task Rookie", "description": "Complete 10 tasks"},
    "tasks_100": {"name": "Task Master", "description": "Complete 100 tasks"},
    "focus_1h": {"name": "Deep Worker", "description": "Log 1 hour of focus time"},
    "focus_10h": {"name": "Flow State", "description": "Log 10 hours of focus time"},
    "streak_7": {"name": "Week Warrior", "description": "Maintain a 7-day streak"},
    "streak_30": {"name": "Monthly Momentum", "description": "Maintain a 30-day streak"},
    "pomodoro_10": {"name": "Pomodoro Pro", "description": "Finish 10 pomodoros"},
    "habit_week": {"name": "Habit Builder", "description": "Complete habits 7 days in a row"},
    "early_bird": {"name": "Early Bird", "description": "Complete a task before 8 AM"},
    "night_owl": {"name": "Night Owl", "description": "Complete a task after 10 PM"},
    "note_taker": {"name": "Scribe", "description": "Create 10 notes"},
}


@dataclass
class Achievement(JsonMixin):
    """A single unlocked achievement record."""

    id: str = ""
    name: str = ""
    description: str = ""
    unlocked_at: str = field(default_factory=utc_now_iso)
    xp_reward: int = 0


@dataclass
class AchievementsStore(JsonMixin):
    """Root document for ``achievements.json``."""

    version: int = 1
    xp: int = 0
    level: int = 1
    badges: list[str] = field(default_factory=list)
    achievements: list[Achievement] = field(default_factory=list)
    unlocked_at: dict[str, str] = field(default_factory=dict)

    def add_xp(self, amount: int) -> int:
        """Add XP, recalculate level, return new level."""
        self.xp = max(0, self.xp + amount)
        self.level = level_for_xp(self.xp)
        return self.level

    def unlock_badge(self, badge_id: str) -> bool:
        """Unlock a badge if not already owned. Returns True if newly unlocked."""
        if badge_id in self.badges:
            return False
        meta = BADGE_CATALOG.get(badge_id, {"name": badge_id, "description": ""})
        self.badges.append(badge_id)
        stamp = utc_now_iso()
        self.unlocked_at[badge_id] = stamp
        self.achievements.append(
            Achievement(
                id=badge_id,
                name=meta["name"],
                description=meta["description"],
                unlocked_at=stamp,
                xp_reward=50,
            )
        )
        self.add_xp(50)
        return True

    def award_task_xp(self) -> None:
        self.add_xp(XP_PER_TASK)

    def award_habit_xp(self) -> None:
        self.add_xp(XP_PER_HABIT)

    def award_focus_minutes(self, minutes: int) -> None:
        self.add_xp(max(0, minutes) * XP_PER_FOCUS_MINUTE)

    def award_streak_day(self) -> None:
        self.add_xp(XP_PER_STREAK_DAY)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "xp": self.xp,
            "level": self.level,
            "badges": list(self.badges),
            "achievements": [a.to_dict() for a in self.achievements],
            "unlocked_at": dict(self.unlocked_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AchievementsStore:
        achievements = [
            Achievement.from_dict(a)
            for a in data.get("achievements", [])
            if isinstance(a, dict)
        ]
        return cls(
            version=int(data.get("version", 1)),
            xp=int(data.get("xp", 0)),
            level=int(data.get("level", 1)),
            badges=list(data.get("badges", [])),
            achievements=achievements,
            unlocked_at={str(k): str(v) for k, v in data.get("unlocked_at", {}).items()},
        )
