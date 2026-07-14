"""Note domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, new_id, utc_now_iso


@dataclass
class NoteFolder(JsonMixin):
    """Organizational folder for markdown notes."""

    id: str = field(default_factory=lambda: new_id("folder"))
    name: str = "Inbox"
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class Note(JsonMixin):
    """Markdown note with pin and folder support."""

    id: str = field(default_factory=lambda: new_id("note"))
    title: str = "Untitled"
    content: str = ""
    folder_id: str = "inbox"
    pinned: bool = False
    tags: list[str] = field(default_factory=list)
    color: str = "#1E293B"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def touch(self) -> None:
        self.updated_at = utc_now_iso()


@dataclass
class NoteCollection(JsonMixin):
    """Root document for ``notes.json``."""

    version: int = 1
    folders: list[NoteFolder] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "folders": [f.to_dict() for f in self.folders],
            "notes": [n.to_dict() for n in self.notes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NoteCollection:
        folders = [NoteFolder.from_dict(f) for f in data.get("folders", [])]
        notes = [Note.from_dict(n) for n in data.get("notes", [])]
        if not folders:
            folders = [NoteFolder(id="inbox", name="Inbox")]
        return cls(
            version=int(data.get("version", 1)),
            folders=folders,
            notes=notes,
        )
