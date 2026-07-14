"""Task domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, new_id, utc_now_iso


def split_minutes(total: int) -> tuple[int, int, int]:
    """Split total minutes into (days, hours, mins)."""
    total = max(0, int(total))
    days, rem = divmod(total, 24 * 60)
    hours, mins = divmod(rem, 60)
    return days, hours, mins


def combine_duration(days: int, hours: int, mins: int) -> int:
    """Combine days/hours/mins into total minutes."""
    return max(0, int(days)) * 24 * 60 + max(0, int(hours)) * 60 + max(0, int(mins))


@dataclass
class Task(JsonMixin):
    """A single work item with status, timer fields, and metadata."""

    id: str = field(default_factory=lambda: new_id("task"))
    title: str = ""
    description: str = ""
    category: str = "general"
    priority: str = "medium"  # low | medium | high | urgent
    status: str = "not_started"  # not_started | in_progress | paused | completed | cancelled
    project_id: str = ""
    tags: list[str] = field(default_factory=list)
    date: str = ""  # planned date YYYY-MM-DD
    deadline: str = ""  # deadline datetime or date ISO
    # Duration estimate — e.g. "this task needs 7 days"
    estimate_days: int = 0
    estimate_hours: int = 0
    estimate_mins: int = 0
    # Daily dedication — e.g. "each day I will give it 3 hours"
    daily_hours: int = 0
    daily_mins: int = 0
    # Derived / legacy total minutes
    estimated_minutes: int = 0
    actual_seconds: int = 0
    completed: bool = False
    completion_time: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    favorite: bool = False
    archived: bool = False
    color: str = "#2DD4BF"
    icon: str = "check"
    notes: str = ""
    order: int = 0
    parent_id: str = ""  # for subtasks (optional)

    def sync_estimated_minutes(self) -> None:
        """
        Refresh ``estimated_minutes``.

        Prefer days × daily dedication when both are set (e.g. 7d × 3h/day).
        Otherwise use the duration breakdown.
        """
        daily = self.daily_hours * 60 + self.daily_mins
        if self.estimate_days > 0 and daily > 0:
            # Plus any extra hours/mins on top of the multi-day plan
            self.estimated_minutes = (
                self.estimate_days * daily
                + self.estimate_hours * 60
                + self.estimate_mins
            )
        else:
            self.estimated_minutes = combine_duration(
                self.estimate_days, self.estimate_hours, self.estimate_mins
            )

    def ensure_estimate_fields(self) -> None:
        """Backfill structured fields from legacy ``estimated_minutes`` if empty."""
        has_breakdown = (
            self.estimate_days
            or self.estimate_hours
            or self.estimate_mins
            or self.daily_hours
            or self.daily_mins
        )
        if not has_breakdown and self.estimated_minutes > 0:
            d, h, m = split_minutes(self.estimated_minutes)
            self.estimate_days = d
            self.estimate_hours = h
            self.estimate_mins = m

    @property
    def daily_minutes_total(self) -> int:
        return max(0, self.daily_hours * 60 + self.daily_mins)

    def estimate_summary(self) -> str:
        """Human-readable estimate, e.g. ``7d · 3h/day ≈ 21h``."""
        self.ensure_estimate_fields()
        parts: list[str] = []
        if self.estimate_days:
            parts.append(f"{self.estimate_days}d")
        if self.estimate_hours:
            parts.append(f"{self.estimate_hours}h")
        if self.estimate_mins:
            parts.append(f"{self.estimate_mins}m")
        duration = " ".join(parts)

        daily = self.daily_minutes_total
        daily_bit = ""
        if daily:
            dh, dm = divmod(daily, 60)
            if dh and dm:
                daily_bit = f"{dh}h {dm}m/day"
            elif dh:
                daily_bit = f"{dh}h/day"
            else:
                daily_bit = f"{dm}m/day"

        if duration and daily_bit and self.estimate_days > 0:
            total = self.estimate_days * daily + self.estimate_hours * 60 + self.estimate_mins
            th, tm = divmod(total, 60)
            total_bit = f"{th}h" if not tm else f"{th}h {tm}m"
            return f"{duration} · {daily_bit} ≈ {total_bit}"
        if duration and daily_bit:
            return f"{duration} · {daily_bit}"
        if duration:
            return duration
        if daily_bit:
            return daily_bit
        return ""

    def touch(self) -> None:
        """Bump ``updated_at`` to now."""
        self.updated_at = utc_now_iso()

    def mark_completed(self) -> None:
        self.completed = True
        self.status = "completed"
        self.completion_time = utc_now_iso()
        self.touch()

    def mark_incomplete(self) -> None:
        self.completed = False
        self.status = "not_started"
        self.completion_time = ""
        self.touch()

    def duplicate(self) -> Task:
        """Return a new Task cloning content fields with a fresh ID."""
        data = self.to_dict()
        data["id"] = new_id("task")
        data["completed"] = False
        data["status"] = "not_started"
        data["completion_time"] = ""
        data["actual_seconds"] = 0
        data["created_at"] = utc_now_iso()
        data["updated_at"] = utc_now_iso()
        data["title"] = f"{self.title} (copy)"
        return Task.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        from dataclasses import fields as dc_fields

        valid = {f.name for f in dc_fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid}
        task = cls(**filtered)
        task.ensure_estimate_fields()
        return task


@dataclass
class TaskCollection(JsonMixin):
    """Root document for ``tasks.json``."""

    version: int = 1
    tasks: list[Task] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskCollection:
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(version=int(data.get("version", 1)), tasks=tasks)
