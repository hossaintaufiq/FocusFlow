"""Task row / list widgets — clear selection and reliable completion check."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.models.task import Task
from src.utils.config import PRIORITY_COLORS, ThemeColors
from src.utils.helpers import format_duration, status_label
from src.widgets.common import AnimatedCheckBox


class TaskRow(QFrame):
    """Professional task row with unmistakable selection and completion check."""

    toggled = Signal(str, bool)
    open_requested = Signal(str)
    timer_requested = Signal(str)
    selected = Signal(str)

    def __init__(
        self,
        task: Task,
        theme: ThemeColors,
        *,
        selected: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.task_id = task.id
        self._theme = theme
        self._selected = selected
        self._task = task
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(64)
        self.setObjectName("taskRow")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 14, 0)
        root.setSpacing(0)

        # Left accent strip — bright when selected
        self._strip = QFrame()
        self._strip.setFixedWidth(5)
        root.addWidget(self._strip)

        inner = QHBoxLayout()
        inner.setContentsMargins(12, 12, 8, 12)
        inner.setSpacing(12)
        root.addLayout(inner, 1)

        self.check = AnimatedCheckBox(theme, checked=task.completed)
        self.check.toggled_custom.connect(self._on_check)
        inner.addWidget(self.check, 0, Qt.AlignmentFlag.AlignTop)

        mid = QVBoxLayout()
        mid.setSpacing(6)
        mid.setContentsMargins(0, 0, 0, 0)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.title = QLabel(task.title)
        title_row.addWidget(self.title, 1)

        self.sel_badge = QLabel("SELECTED")
        self.sel_badge.setFixedHeight(20)
        title_row.addWidget(self.sel_badge)
        mid.addLayout(title_row)

        # Meta chips row
        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.setContentsMargins(0, 0, 0, 0)

        pri_color = PRIORITY_COLORS.get(task.priority, theme.text_muted)
        chips.addWidget(self._chip(task.priority.upper(), pri_color))
        chips.addWidget(self._chip(status_label(task.status), theme.text_secondary))
        if task.category:
            chips.addWidget(self._chip(task.category, theme.text_muted))
        summary = task.estimate_summary()
        if summary:
            chips.addWidget(self._chip(summary, theme.info))
        if task.deadline:
            chips.addWidget(self._chip(f"Due {task.deadline[:10]}", theme.warning))
        if task.actual_seconds:
            chips.addWidget(self._chip(format_duration(task.actual_seconds), theme.text_muted))
        if task.favorite:
            chips.addWidget(self._chip("Favorite", theme.accent))
        chips.addStretch()
        mid.addLayout(chips)
        inner.addLayout(mid, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedHeight(34)
        edit_btn.setMinimumWidth(64)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self._edit_clicked)
        actions.addWidget(edit_btn)

        focus_btn = QPushButton("Focus")
        focus_btn.setFixedHeight(34)
        focus_btn.setMinimumWidth(72)
        focus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        focus_btn.setStyleSheet(
            f"QPushButton {{ background: {theme.accent}; color: #0B1220; border: none; "
            f"border-radius: 8px; font-weight: 700; padding: 0 12px; }}"
            f"QPushButton:hover {{ background: {theme.accent_hover}; }}"
        )
        focus_btn.clicked.connect(self._focus_clicked)
        actions.addWidget(focus_btn)
        inner.addLayout(actions)

        self._apply_chrome()

    def _chip(self, text: str, color: str) -> QLabel:
        lab = QLabel(text)
        lab.setStyleSheet(
            f"QLabel {{ color: {color}; background: rgba(148,163,184,0.10); "
            f"border: 1px solid rgba(148,163,184,0.18); border-radius: 6px; "
            f"padding: 2px 8px; font-size: 8.5pt; font-weight: 600; }}"
        )
        return lab

    def _on_check(self, checked: bool) -> None:
        self.selected.emit(self.task_id)
        self.toggled.emit(self.task_id, checked)

    def _edit_clicked(self) -> None:
        self.selected.emit(self.task_id)
        self.open_requested.emit(self.task_id)

    def _focus_clicked(self) -> None:
        self.selected.emit(self.task_id)
        self.timer_requested.emit(self.task_id)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_chrome()

    def _apply_chrome(self) -> None:
        t = self._theme
        completed = self._task.completed
        if self._selected:
            self._strip.setStyleSheet(f"background: {t.accent}; border: none;")
            self.setStyleSheet(
                f"QFrame#taskRow {{ background: {t.accent_dim}; "
                f"border: 2px solid {t.accent}; border-radius: 12px; }}"
            )
            self.sel_badge.setVisible(True)
            self.sel_badge.setStyleSheet(
                f"QLabel {{ color: #0B1220; background: {t.accent}; "
                f"border: none; border-radius: 6px; padding: 2px 8px; "
                f"font-size: 8pt; font-weight: 800; letter-spacing: 0.5px; }}"
            )
        else:
            self._strip.setStyleSheet(
                f"background: {PRIORITY_COLORS.get(self._task.priority, t.border)}; border: none;"
            )
            self.setStyleSheet(
                f"QFrame#taskRow {{ background: {t.bg_tertiary}; "
                f"border: 1px solid {t.border}; border-radius: 12px; }}"
                f"QFrame#taskRow:hover {{ border-color: {t.border_strong}; "
                f"background: {t.bg_elevated}; }}"
            )
            self.sel_badge.setVisible(False)

        if completed:
            self.title.setStyleSheet(
                f"font-weight: 600; font-size: 11pt; color: {t.text_muted}; "
                "text-decoration: line-through; background: transparent; border: none;"
            )
        else:
            self.title.setStyleSheet(
                f"font-weight: 650; font-size: 11pt; color: {t.text_primary}; "
                "background: transparent; border: none;"
            )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            # Ignore clicks that originated on child buttons/checkbox — those handle themselves
            child = self.childAt(event.position().toPoint())
            if child is self.check or (child and self.check.isAncestorOf(child)):
                return super().mousePressEvent(event)
            self.selected.emit(self.task_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.task_id)
        super().mouseDoubleClickEvent(event)


class TaskList(QWidget):
    toggled = Signal(str, bool)
    open_requested = Signal(str)
    timer_requested = Signal(str)
    selected = Signal(str)

    def __init__(self, theme: ThemeColors, parent=None) -> None:
        super().__init__(parent)
        self.theme = theme
        self._selected_id: str | None = None
        self._rows: dict[str, TaskRow] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

    def set_selected(self, task_id: str | None) -> None:
        self._selected_id = task_id
        for tid, row in self._rows.items():
            row.set_selected(tid == task_id)

    def set_tasks(self, tasks: list[Task]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()
        for task in tasks:
            row = TaskRow(task, self.theme, selected=task.id == self._selected_id)
            row.toggled.connect(self.toggled.emit)
            row.open_requested.connect(self.open_requested.emit)
            row.timer_requested.connect(self.timer_requested.emit)
            row.selected.connect(self._on_row_selected)
            self._rows[task.id] = row
            self._layout.addWidget(row)
        if not tasks:
            empty = QLabel("No tasks match — create one with + New Task")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {self.theme.text_muted}; padding: 48px; font-size: 11pt;"
            )
            self._layout.addWidget(empty)
        self._layout.addStretch()

    def _on_row_selected(self, task_id: str) -> None:
        self.set_selected(task_id)
        self.selected.emit(task_id)
