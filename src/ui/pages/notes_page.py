"""Markdown notes page with folders, pin, autosave."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.widgets.common import PageHeader


class NotesPage(BasePage):
    page_id = "notes"

    def build(self) -> None:
        self.layout_main.addWidget(PageHeader("Notes", "Markdown notes · auto-save", self.theme))
        self._current_id: str | None = None

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search notes…")
        self.search.textChanged.connect(self._reload_list)
        new_btn = QPushButton("+ Note")
        new_btn.setObjectName("primaryBtn")
        new_btn.clicked.connect(self._new)
        folder_btn = QPushButton("+ Folder")
        folder_btn.clicked.connect(self._new_folder)
        pin_btn = QPushButton("Pin")
        pin_btn.clicked.connect(self._pin)
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete)
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(new_btn)
        toolbar.addWidget(folder_btn)
        toolbar.addWidget(pin_btn)
        toolbar.addWidget(del_btn)
        self.layout_main.addLayout(toolbar)

        split = QSplitter()
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._select)
        left_lay.addWidget(self.list)
        split.addWidget(left)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        self.title = QLineEdit()
        self.title.setPlaceholderText("Title")
        self.title.textChanged.connect(self._schedule_save)
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("# Markdown supported\nWrite freely…")
        self.editor.textChanged.connect(self._schedule_save)
        self.save_hint = QLabel("Auto-save on")
        self.save_hint.setObjectName("muted")
        right_lay.addWidget(self.title)
        right_lay.addWidget(self.editor, 1)
        right_lay.addWidget(self.save_hint)
        split.addWidget(right)
        split.setStretchFactor(1, 2)
        self.layout_main.addWidget(split, 1)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._autosave)

    def refresh(self) -> None:
        self._reload_list()

    def _reload_list(self) -> None:
        current = self._current_id
        self.list.blockSignals(True)
        self.list.clear()
        for note in self.ctx.notes.search(self.search.text()):
            prefix = "📌 " if note.pinned else ""
            item = QListWidgetItem(f"{prefix}{note.title}")
            item.setData(256, note.id)
            self.list.addItem(item)
            if note.id == current:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)

    def _select(self, current: QListWidgetItem | None, _prev=None) -> None:
        if not current:
            return
        self._autosave()
        note_id = current.data(256)
        note = self.ctx.notes.get(note_id)
        if not note:
            return
        self._current_id = note_id
        self.title.blockSignals(True)
        self.editor.blockSignals(True)
        self.title.setText(note.title)
        self.editor.setPlainText(note.content)
        self.title.blockSignals(False)
        self.editor.blockSignals(False)

    def _schedule_save(self) -> None:
        self.save_hint.setText("Saving…")
        self._save_timer.start()

    def _autosave(self) -> None:
        if not self._current_id:
            self.save_hint.setText("Auto-save on")
            return
        self.ctx.notes.autosave(
            self._current_id,
            self.editor.toPlainText(),
            title=self.title.text().strip() or "Untitled",
        )
        self.save_hint.setText("Saved")
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(256) == self._current_id:
                note = self.ctx.notes.get(self._current_id)
                if note:
                    item.setText(("📌 " if note.pinned else "") + note.title)
                break

    def _new(self) -> None:
        note = self.ctx.notes.add(title="Untitled", content="")
        self.ctx.achievements.on_notes_created(len(self.ctx.notes.notes))
        self._current_id = note.id
        self.ctx.emit_change("notes")
        self._reload_list()

    def _new_folder(self) -> None:
        name, ok = QInputDialog.getText(self, "Folder", "Folder name:")
        if ok and name.strip():
            self.ctx.notes.add_folder(name.strip())
            self.ctx.signals.toast.emit(f"Folder '{name}' created")

    def _pin(self) -> None:
        if self._current_id:
            self.ctx.notes.toggle_pin(self._current_id)
            self.ctx.emit_change("notes")

    def _delete(self) -> None:
        if not self._current_id:
            return
        if QMessageBox.question(self, "Delete", "Delete note?") == QMessageBox.StandardButton.Yes:
            self.ctx.notes.delete(self._current_id)
            self._current_id = None
            self.title.clear()
            self.editor.clear()
            self.ctx.emit_change("notes")
