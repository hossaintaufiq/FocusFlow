"""Habit tracking service with streak calculation."""

from __future__ import annotations

from datetime import date, timedelta

from src.models.base import today_iso
from src.models.habit import Habit, HabitCollection
from src.services.history_service import HistoryService
from src.services.storage import JsonStorage


def _calc_streak(completions: list[str], frequency: str = "daily") -> tuple[int, int]:
    """Return (current_streak, longest_streak) for daily habits."""
    if not completions:
        return 0, 0
    days = sorted({c[:10] for c in completions})
    day_set = set(days)
    # longest
    longest = 1
    run = 1
    for i in range(1, len(days)):
        prev = date.fromisoformat(days[i - 1])
        cur = date.fromisoformat(days[i])
        if (cur - prev).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    # current — count back from today or yesterday
    today = date.today()
    current = 0
    cursor = today
    if today.isoformat() not in day_set:
        cursor = today - timedelta(days=1)
    while cursor.isoformat() in day_set:
        current += 1
        cursor -= timedelta(days=1)
    return current, max(longest, current)


class HabitService:
    def __init__(self, storage: JsonStorage, history: HistoryService) -> None:
        self._storage = storage
        self._history = history
        self._data = storage.load("habits", HabitCollection.from_dict, HabitCollection)
        self.recalculate_streaks()

    @property
    def habits(self) -> list[Habit]:
        return [h for h in self._data.habits if not h.archived]

    def save(self) -> None:
        self._storage.save("habits", self._data)

    def get(self, habit_id: str) -> Habit | None:
        for h in self._data.habits:
            if h.id == habit_id:
                return h
        return None

    def add(self, **kwargs) -> Habit:
        habit = Habit(**kwargs)
        self._data.habits.append(habit)
        self.save()
        self._history.log(
            "habit_created",
            entity_type="habit",
            entity_id=habit.id,
            summary=f"Created habit: {habit.name}",
        )
        return habit

    def update(self, habit_id: str, **kwargs) -> Habit | None:
        habit = self.get(habit_id)
        if not habit:
            return None
        for key, value in kwargs.items():
            if hasattr(habit, key) and key != "id":
                setattr(habit, key, value)
        habit.updated_at = habit.updated_at  # noop keep
        from src.models.base import utc_now_iso

        habit.updated_at = utc_now_iso()
        self.recalculate_streaks()
        self.save()
        return habit

    def delete(self, habit_id: str) -> bool:
        habit = self.get(habit_id)
        if not habit:
            return False
        self._data.habits = [h for h in self._data.habits if h.id != habit_id]
        self.save()
        self._history.log(
            "habit_deleted",
            entity_type="habit",
            entity_id=habit_id,
            summary=f"Deleted habit: {habit.name}",
        )
        return True

    def toggle_today(self, habit_id: str) -> Habit | None:
        habit = self.get(habit_id)
        if not habit:
            return None
        day = today_iso()
        if habit.is_completed_on(day):
            habit.mark_undone(day)
            action = "habit_uncompleted"
        else:
            habit.mark_done(day)
            action = "habit_completed"
        self.recalculate_streaks()
        self.save()
        self._history.log(
            action,
            entity_type="habit",
            entity_id=habit.id,
            summary=f"{'Completed' if action == 'habit_completed' else 'Unchecked'} habit: {habit.name}",
        )
        return habit

    def recalculate_streaks(self) -> None:
        for habit in self._data.habits:
            cur, longest = _calc_streak(habit.completions, habit.frequency)
            habit.current_streak = cur
            habit.longest_streak = max(habit.longest_streak, longest)

    def today_completion_rate(self) -> float:
        habits = self.habits
        if not habits:
            return 0.0
        done = sum(1 for h in habits if h.is_completed_on())
        return round(100.0 * done / len(habits), 1)

    def heatmap_data(self, days: int = 84) -> dict[str, int]:
        """Map date -> completion count for calendar heatmap."""
        counts: dict[str, int] = {}
        start = date.today() - timedelta(days=days - 1)
        for i in range(days):
            d = (start + timedelta(days=i)).isoformat()
            counts[d] = 0
        for habit in self.habits:
            for c in habit.completions:
                day = c[:10]
                if day in counts:
                    counts[day] += 1
        return counts

    def best_streaks(self) -> tuple[int, int]:
        current = max((h.current_streak for h in self.habits), default=0)
        longest = max((h.longest_streak for h in self.habits), default=0)
        return current, longest
