"""Domain models — typed dataclasses for all FocusFlow entities."""

from src.models.achievements import (
    BADGE_CATALOG,
    Achievement,
    AchievementsStore,
    level_for_xp,
    xp_for_next_level,
)
from src.models.base import JsonMixin, new_id, today_iso, utc_now_iso
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
from src.models.habit import Habit, HabitCollection
from src.models.history import HISTORY_ACTIONS, HistoryCollection, HistoryEntry
from src.models.note import Note, NoteCollection, NoteFolder
from src.models.project import Project, ProjectCollection
from src.models.settings import Settings
from src.models.stats import DayStats, StatsStore
from src.models.task import Task, TaskCollection
from src.models.timer import ActiveTimer, TimerSession, TimerStore

__all__ = [
    "JsonMixin",
    "new_id",
    "today_iso",
    "utc_now_iso",
    "Task",
    "TaskCollection",
    "Project",
    "ProjectCollection",
    "Habit",
    "HabitCollection",
    "Note",
    "NoteFolder",
    "NoteCollection",
    "ActiveTimer",
    "TimerSession",
    "TimerStore",
    "HistoryEntry",
    "HistoryCollection",
    "HISTORY_ACTIONS",
    "Settings",
    "DayStats",
    "StatsStore",
    "ExtrasStore",
    "JournalEntry",
    "MoodEntry",
    "WaterDay",
    "WorkoutEntry",
    "ReadingEntry",
    "CodingEntry",
    "LeetCodeEntry",
    "GitHubEntry",
    "StudyEntry",
    "PrayerDay",
    "FinanceNote",
    "StickyNote",
    "Countdown",
    "Achievement",
    "AchievementsStore",
    "BADGE_CATALOG",
    "level_for_xp",
    "xp_for_next_level",
]
