"""Task row / list widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.task import Task
from src.utils.config import PRIORITY_COLORS, ThemeColors
from src.utils.helpers import format_duration
from src.widgets.common import AnimatedCheckBox


class TaskRow(QFrame):
    """Single task row with checkbox, meta, and actions."""

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
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_chrome()
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(12)

        self.check = AnimatedCheckBox(theme, checked=task.completed)
        self.check.toggled_custom.connect(lambda c: self.toggled.emit(task.id, c))
        root.addWidget(self.check)

        mid = QVBoxLayout()
        mid.setSpacing(2)
        title = QLabel(task.title)
        title.setStyleSheet(
            f"font-weight: 600; color: {theme.text_primary}; background: transparent; border: none;"
            + (" text-decoration: line-through; color: #64748B;" if task.completed else "")
        )
        mid.addWidget(title)

        bits = []
        if task.priority:
            color = PRIORITY_COLORS.get(task.priority, theme.text_muted)
            bits.append(f'<span style="color:{color}">{task.priority}</span>')
        if task.category:
            bits.append(task.category)
        summary = task.estimate_summary()
        if summary:
            bits.append(summary)
        if task.deadline:
            bits.append(f"due {task.deadline[:10]}")
        if task.actual_seconds:
            bits.append(format_duration(task.actual_seconds))
        if task.favorite:
            bits.append("★")
        meta = QLabel(" · ".join(bits) if bits else "No details")
        meta.setTextFormat(Qt.TextFormat.RichText)
        meta.setStyleSheet(
            f"color: {theme.text_muted}; font-size: 9pt; background: transparent; border: none;"
        )
        mid.addWidget(meta)
        root.addLayout(mid, 1)

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedHeight(32)
        edit_btn.setToolTip("Edit task")
        edit_btn.clicked.connect(lambda: self.open_requested.emit(task.id))
        root.addWidget(edit_btn)

        timer_btn = QPushButton("Focus")
        timer_btn.setFixedHeight(32)
        timer_btn.setToolTip("Start Pomodoro for this task")
        timer_btn.setStyleSheet(
            f"QPushButton {{ background: {theme.accent_dim}; color: {theme.accent}; "
            f"border: none; border-radius: 8px; font-weight: 700; }}"
        )
        timer_btn.clicked.connect(lambda: self.timer_requested.emit(task.id))
        root.addWidget(timer_btn)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_chrome()

    def _apply_chrome(self) -> None:
        t = self._theme
        if self._selected:
            self.setStyleSheet(
                f"QFrame {{ background: {t.accent_dim}; border: 1px solid {t.accent}; "
                f"border-radius: 12px; }}"
            )
        else:
            self.setStyleSheet(
                f"QFrame {{ background: {t.bg_tertiary}; border: 1px solid {t.border}; "
                f"border-radius: 12px; }}"
                f"QFrame:hover {{ border-color: {t.border_strong}; }}"
            )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
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
        self._layout.setSpacing(8)

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
        self._layout.addStretch()

    def _on_row_selected(self, task_id: str) -> None:
        self.set_selected(task_id)
        self.selected.emit(task_id)
