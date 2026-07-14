"""History / audit-log domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, new_id, utc_now_iso

# Canonical action names used across services
HISTORY_ACTIONS: tuple[str, ...] = (
    "task_created",
    "task_edited",
    "task_deleted",
    "task_completed",
    "task_uncompleted",
    "task_archived",
    "task_restored",
    "task_duplicated",
    "timer_started",
    "timer_paused",
    "timer_resumed",
    "timer_stopped",
    "timer_reset",
    "pomodoro_completed",
    "habit_completed",
    "habit_uncompleted",
    "habit_created",
    "habit_deleted",
    "project_created",
    "project_edited",
    "project_deleted",
    "note_created",
    "note_edited",
    "note_deleted",
    "settings_changed",
    "backup_created",
    "backup_restored",
    "app_started",
    "app_closed",
)


@dataclass
class HistoryEntry(JsonMixin):
    """A single auditable user or system action."""

    id: str = field(default_factory=lambda: new_id("hist"))
    action: str = ""
    entity_type: str = ""  # task | project | habit | note | timer | settings | system
    entity_id: str = ""
    summary: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass
class HistoryCollection(JsonMixin):
    """Root document for ``history.json``."""

    version: int = 1
    entries: list[HistoryEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryCollection:
        entries = [HistoryEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(version=int(data.get("version", 1)), entries=entries)
