"""Markdown notes service with folders and auto-save."""

from __future__ import annotations

from src.models.base import utc_now_iso
from src.models.note import Note, NoteCollection, NoteFolder
from src.services.history_service import HistoryService
from src.services.storage import JsonStorage


class NoteService:
    def __init__(self, storage: JsonStorage, history: HistoryService) -> None:
        self._storage = storage
        self._history = history
        self._data = storage.load("notes", NoteCollection.from_dict, NoteCollection)

    @property
    def notes(self) -> list[Note]:
        return list(self._data.notes)

    @property
    def folders(self) -> list[NoteFolder]:
        return list(self._data.folders)

    def save(self) -> None:
        self._storage.save("notes", self._data)

    def get(self, note_id: str) -> Note | None:
        for n in self._data.notes:
            if n.id == note_id:
                return n
        return None

    def add(self, **kwargs) -> Note:
        note = Note(**kwargs)
        self._data.notes.insert(0, note)
        self.save()
        self._history.log(
            "note_created",
            entity_type="note",
            entity_id=note.id,
            summary=f"Created note: {note.title}",
        )
        return note

    def update(self, note_id: str, **kwargs) -> Note | None:
        note = self.get(note_id)
        if not note:
            return None
        for key, value in kwargs.items():
            if hasattr(note, key) and key != "id":
                setattr(note, key, value)
        note.touch()
        self.save()
        return note

    def autosave(self, note_id: str, content: str, title: str | None = None) -> Note | None:
        kwargs: dict = {"content": content}
        if title is not None:
            kwargs["title"] = title
        note = self.update(note_id, **kwargs)
        return note

    def delete(self, note_id: str) -> bool:
        note = self.get(note_id)
        if not note:
            return False
        self._data.notes = [n for n in self._data.notes if n.id != note_id]
        self.save()
        self._history.log(
            "note_deleted",
            entity_type="note",
            entity_id=note_id,
            summary=f"Deleted note: {note.title}",
        )
        return True

    def toggle_pin(self, note_id: str) -> Note | None:
        note = self.get(note_id)
        if not note:
            return None
        return self.update(note_id, pinned=not note.pinned)

    def add_folder(self, name: str) -> NoteFolder:
        folder = NoteFolder(name=name)
        self._data.folders.append(folder)
        self.save()
        return folder

    def search(self, query: str) -> list[Note]:
        q = query.lower().strip()
        notes = sorted(
            self._data.notes,
            key=lambda n: (n.pinned, n.updated_at),
            reverse=True,
        )
        if not q:
            return notes
        return [
            n
            for n in notes
            if q in n.title.lower()
            or q in n.content.lower()
            or any(q in t.lower() for t in n.tags)
        ]
