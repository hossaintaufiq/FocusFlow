"""Extras trackers service (journal, mood, water, etc.)."""

from __future__ import annotations

from src.models.base import today_iso, utc_now_iso
from src.models.extras import (
    CodingEntry,
    Countdown,
    ExtrasStore,
    FinanceNote,
    GitHubEntry,
    JournalEntry,
    LeetCodeEntry,
    MoodEntry,
    PrayerDay,
    ReadingEntry,
    StickyNote,
    StudyEntry,
    WaterDay,
    WorkoutEntry,
)
from src.services.storage import JsonStorage


class ExtrasService:
    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage
        self._data = storage.load("extras", ExtrasStore.from_dict, ExtrasStore)

    @property
    def data(self) -> ExtrasStore:
        return self._data

    def save(self) -> None:
        self._storage.save("extras", self._data)

    # --- Journal ---
    def add_journal(self, title: str, content: str, mood: int = 3) -> JournalEntry:
        entry = JournalEntry(title=title, content=content, mood=mood)
        self._data.journal.insert(0, entry)
        self.save()
        return entry

    # --- Mood ---
    def set_mood(self, score: int, note: str = "") -> MoodEntry:
        entry = MoodEntry(score=max(1, min(5, score)), note=note)
        self._data.mood = [m for m in self._data.mood if m.date != entry.date]
        self._data.mood.insert(0, entry)
        self.save()
        return entry

    # --- Water ---
    def add_water(self, ml: int, goal_ml: int = 2500) -> WaterDay:
        day = today_iso()
        water = self._data.water.get(day) or WaterDay(date=day, goal_ml=goal_ml)
        water.ml += ml
        water.goal_ml = goal_ml
        self._data.water[day] = water
        self.save()
        return water

    def water_today(self, goal_ml: int = 2500) -> WaterDay:
        day = today_iso()
        if day not in self._data.water:
            self._data.water[day] = WaterDay(date=day, goal_ml=goal_ml)
        return self._data.water[day]

    # --- Workout / reading / coding / etc. ---
    def add_workout(self, **kwargs) -> WorkoutEntry:
        e = WorkoutEntry(**kwargs)
        self._data.workout.insert(0, e)
        self.save()
        return e

    def add_reading(self, **kwargs) -> ReadingEntry:
        e = ReadingEntry(**kwargs)
        self._data.reading.insert(0, e)
        self.save()
        return e

    def add_coding(self, **kwargs) -> CodingEntry:
        e = CodingEntry(**kwargs)
        self._data.coding.insert(0, e)
        self.save()
        return e

    def add_leetcode(self, **kwargs) -> LeetCodeEntry:
        e = LeetCodeEntry(**kwargs)
        self._data.leetcode.insert(0, e)
        self.save()
        return e

    def add_github(self, **kwargs) -> GitHubEntry:
        e = GitHubEntry(**kwargs)
        self._data.github.insert(0, e)
        self.save()
        return e

    def add_study(self, **kwargs) -> StudyEntry:
        e = StudyEntry(**kwargs)
        self._data.study.insert(0, e)
        self.save()
        return e

    def add_finance(self, **kwargs) -> FinanceNote:
        e = FinanceNote(**kwargs)
        self._data.finance.insert(0, e)
        self.save()
        return e

    # --- Prayer ---
    def toggle_prayer(self, item: str) -> PrayerDay:
        day = today_iso()
        prayer = self._data.prayer.get(day) or PrayerDay(date=day)
        if item in prayer.items:
            prayer.items[item] = not prayer.items[item]
        self._data.prayer[day] = prayer
        self.save()
        return prayer

    def prayer_today(self) -> PrayerDay:
        day = today_iso()
        if day not in self._data.prayer:
            self._data.prayer[day] = PrayerDay(date=day)
        return self._data.prayer[day]

    # --- Scratch / sticky / countdown ---
    def set_scratchpad(self, text: str) -> None:
        self._data.scratchpad = text
        self.save()

    def add_sticky(self, content: str, color: str = "#FBBF24") -> StickyNote:
        note = StickyNote(content=content, color=color)
        self._data.sticky_notes.append(note)
        self.save()
        return note

    def update_sticky(self, note_id: str, **kwargs) -> StickyNote | None:
        for n in self._data.sticky_notes:
            if n.id == note_id:
                for k, v in kwargs.items():
                    if hasattr(n, k):
                        setattr(n, k, v)
                n.updated_at = utc_now_iso()
                self.save()
                return n
        return None

    def delete_sticky(self, note_id: str) -> bool:
        before = len(self._data.sticky_notes)
        self._data.sticky_notes = [n for n in self._data.sticky_notes if n.id != note_id]
        if len(self._data.sticky_notes) < before:
            self.save()
            return True
        return False

    def add_countdown(self, title: str, target_date: str, color: str = "#38BDF8") -> Countdown:
        cd = Countdown(title=title, target_date=target_date, color=color)
        self._data.countdowns.append(cd)
        self.save()
        return cd

    def delete_countdown(self, cd_id: str) -> bool:
        before = len(self._data.countdowns)
        self._data.countdowns = [c for c in self._data.countdowns if c.id != cd_id]
        if len(self._data.countdowns) < before:
            self.save()
            return True
        return False
