"""Extras trackers — journal, mood, water, workout, and related models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, new_id, today_iso, utc_now_iso


@dataclass
class JournalEntry(JsonMixin):
    id: str = field(default_factory=lambda: new_id("journal"))
    date: str = field(default_factory=today_iso)
    title: str = ""
    content: str = ""
    mood: int = 3  # 1–5
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass
class MoodEntry(JsonMixin):
    id: str = field(default_factory=lambda: new_id("mood"))
    date: str = field(default_factory=today_iso)
    score: int = 3  # 1–5
    note: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class WaterDay(JsonMixin):
    date: str = field(default_factory=today_iso)
    ml: int = 0
    goal_ml: int = 2500


@dataclass
class WorkoutEntry(JsonMixin):
    id: str = field(default_factory=lambda: new_id("workout"))
    date: str = field(default_factory=today_iso)
    activity: str = ""
    duration_minutes: int = 0
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class ReadingEntry(JsonMixin):
    id: str = field(default_factory=lambda: new_id("read"))
    date: str = field(default_factory=today_iso)
    title: str = ""
    pages: int = 0
    minutes: int = 0
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CodingEntry(JsonMixin):
    id: str = field(default_factory=lambda: new_id("code"))
    date: str = field(default_factory=today_iso)
    project: str = ""
    hours: float = 0.0
    language: str = ""
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class LeetCodeEntry(JsonMixin):
    id: str = field(default_factory=lambda: new_id("lc"))
    date: str = field(default_factory=today_iso)
    problem: str = ""
    difficulty: str = "medium"  # easy | medium | hard
    solved: bool = True
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class GitHubEntry(JsonMixin):
    """Manual GitHub commit tracker (offline — user enters count)."""

    id: str = field(default_factory=lambda: new_id("gh"))
    date: str = field(default_factory=today_iso)
    commits: int = 0
    repo: str = ""
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class StudyEntry(JsonMixin):
    id: str = field(default_factory=lambda: new_id("study"))
    date: str = field(default_factory=today_iso)
    subject: str = ""
    hours: float = 0.0
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class PrayerDay(JsonMixin):
    """Daily prayer checklist (generic labels — user configurable later)."""

    date: str = field(default_factory=today_iso)
    items: dict[str, bool] = field(
        default_factory=lambda: {
            "fajr": False,
            "dhuhr": False,
            "asr": False,
            "maghrib": False,
            "isha": False,
        }
    )


@dataclass
class FinanceNote(JsonMixin):
    id: str = field(default_factory=lambda: new_id("fin"))
    date: str = field(default_factory=today_iso)
    title: str = ""
    amount: float = 0.0
    kind: str = "expense"  # expense | income | note
    category: str = ""
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class StickyNote(JsonMixin):
    id: str = field(default_factory=lambda: new_id("sticky"))
    content: str = ""
    color: str = "#FBBF24"
    x: int = 40
    y: int = 40
    pinned: bool = False
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass
class Countdown(JsonMixin):
    id: str = field(default_factory=lambda: new_id("cd"))
    title: str = ""
    target_date: str = ""  # ISO date or datetime
    color: str = "#38BDF8"
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class ExtrasStore(JsonMixin):
    """Root document for ``extras.json``."""

    version: int = 1
    journal: list[JournalEntry] = field(default_factory=list)
    mood: list[MoodEntry] = field(default_factory=list)
    water: dict[str, WaterDay] = field(default_factory=dict)  # date -> WaterDay
    workout: list[WorkoutEntry] = field(default_factory=list)
    reading: list[ReadingEntry] = field(default_factory=list)
    coding: list[CodingEntry] = field(default_factory=list)
    leetcode: list[LeetCodeEntry] = field(default_factory=list)
    github: list[GitHubEntry] = field(default_factory=list)
    study: list[StudyEntry] = field(default_factory=list)
    prayer: dict[str, PrayerDay] = field(default_factory=dict)
    finance: list[FinanceNote] = field(default_factory=list)
    scratchpad: str = ""
    sticky_notes: list[StickyNote] = field(default_factory=list)
    countdowns: list[Countdown] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "journal": [j.to_dict() for j in self.journal],
            "mood": [m.to_dict() for m in self.mood],
            "water": {k: v.to_dict() for k, v in self.water.items()},
            "workout": [w.to_dict() for w in self.workout],
            "reading": [r.to_dict() for r in self.reading],
            "coding": [c.to_dict() for c in self.coding],
            "leetcode": [l.to_dict() for l in self.leetcode],
            "github": [g.to_dict() for g in self.github],
            "study": [s.to_dict() for s in self.study],
            "prayer": {k: v.to_dict() for k, v in self.prayer.items()},
            "finance": [f.to_dict() for f in self.finance],
            "scratchpad": self.scratchpad,
            "sticky_notes": [s.to_dict() for s in self.sticky_notes],
            "countdowns": [c.to_dict() for c in self.countdowns],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtrasStore:
        def _list(key: str, model: type) -> list:
            return [model.from_dict(item) for item in data.get(key, []) if isinstance(item, dict)]

        water_raw = data.get("water", {})
        water = {
            k: WaterDay.from_dict(v) for k, v in water_raw.items() if isinstance(v, dict)
        }
        prayer_raw = data.get("prayer", {})
        prayer = {
            k: PrayerDay.from_dict(v) for k, v in prayer_raw.items() if isinstance(v, dict)
        }
        return cls(
            version=int(data.get("version", 1)),
            journal=_list("journal", JournalEntry),
            mood=_list("mood", MoodEntry),
            water=water,
            workout=_list("workout", WorkoutEntry),
            reading=_list("reading", ReadingEntry),
            coding=_list("coding", CodingEntry),
            leetcode=_list("leetcode", LeetCodeEntry),
            github=_list("github", GitHubEntry),
            study=_list("study", StudyEntry),
            prayer=prayer,
            finance=_list("finance", FinanceNote),
            scratchpad=str(data.get("scratchpad", "")),
            sticky_notes=_list("sticky_notes", StickyNote),
            countdowns=_list("countdowns", Countdown),
        )
