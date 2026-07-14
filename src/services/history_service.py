"""History / audit log service."""

from __future__ import annotations

import logging
from typing import Any

from src.models.history import HistoryCollection, HistoryEntry
from src.services.storage import JsonStorage
from src.utils.config import MAX_HISTORY_ENTRIES

logger = logging.getLogger("FocusFlow.history")


class HistoryService:
    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage
        self._data = storage.load(
            "history",
            HistoryCollection.from_dict,
            HistoryCollection,
        )

    @property
    def entries(self) -> list[HistoryEntry]:
        return list(self._data.entries)

    def log(
        self,
        action: str,
        *,
        entity_type: str = "",
        entity_id: str = "",
        summary: str = "",
        details: dict[str, Any] | None = None,
    ) -> HistoryEntry:
        entry = HistoryEntry(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary or action.replace("_", " ").title(),
            details=details or {},
        )
        self._data.entries.insert(0, entry)
        if len(self._data.entries) > MAX_HISTORY_ENTRIES:
            self._data.entries = self._data.entries[:MAX_HISTORY_ENTRIES]
        self.save()
        return entry

    def recent(self, limit: int = 50) -> list[HistoryEntry]:
        return self._data.entries[:limit]

    def search(self, query: str) -> list[HistoryEntry]:
        q = query.lower().strip()
        if not q:
            return self.entries
        return [
            e
            for e in self._data.entries
            if q in e.summary.lower()
            or q in e.action.lower()
            or q in e.entity_type.lower()
        ]

    def save(self) -> None:
        self._storage.save("history", self._data)

    def clear(self) -> None:
        self._data.entries.clear()
        self.save()
