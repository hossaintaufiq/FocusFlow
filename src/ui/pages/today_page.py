"""Today's tasks page with search, filters, and multi-actions."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
)

from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, PageHeader
from src.widgets.task_dialog import TaskDialog
from src.widgets.task_widgets import TaskList


class TodayPage(BasePage):
    page_id = "today"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader("Today's Tasks", "Capture, filter, and ship.", self.theme)
        )
        self._selected: str | None = None

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search title, tags, category…  (Ctrl+F)")
        self.search.setObjectName("globalSearch")
        self.search.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search, 2)

        self.filter_priority = QComboBox()
        self.filter_priority.addItem("All priorities", "")
        for p in ("low", "medium", "high", "urgent"):
            self.filter_priority.addItem(p.title(), p)
        self.filter_priority.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.filter_priority)

        self.sort_by = QComboBox()
        self.sort_by.addItem("Updated", "updated_at")
        self.sort_by.addItem("Priority", "priority")
        self.sort_by.addItem("Deadline", "deadline")
        self.sort_by.addItem("Title", "title")
        self.sort_by.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.sort_by)

        new_btn = QPushButton("+ New Task")
        new_btn.setObjectName("primaryBtn")
        new_btn.clicked.connect(self.new_task)
        toolbar.addWidget(new_btn)
        self.layout_main.addLayout(toolbar)

        actions = QHBoxLayout()
        for label, slot in (
            ("Duplicate", self._dup),
            ("Archive", self._archive),
            ("Delete", self._delete),
            ("Favorite", self._fav),
        ):
            b = QPushButton(label)
            b.clicked.connect(slot)
            actions.addWidget(b)
        actions.addStretch()
        self.selection_label = QLabel("Click a task to select")
        self.selection_label.setObjectName("muted")
        actions.addWidget(self.selection_label)
        self.count_label = QLabel()
        self.count_label.setObjectName("muted")
        actions.addWidget(self.count_label)
        self.layout_main.addLayout(actions)

        card = GlassCard(self.theme)
        self.list = TaskList(self.theme)
        self.list.toggled.connect(self._toggle)
        self.list.open_requested.connect(self.edit_task)
        self.list.timer_requested.connect(self._timer)
        self.list.selected.connect(self._on_selected)
        card.body.addWidget(self.list)
        self.layout_main.addWidget(card, 1)

    def refresh(self) -> None:
        q = self.search.text().strip()
        tasks = (
            self.ctx.tasks.search(q)
            if q
            else [t for t in self.ctx.tasks.tasks if not t.archived]
        )
        if not q:
            today = {t.id for t in self.ctx.tasks.today()}
            tasks = sorted(
                tasks,
                key=lambda t: (0 if t.id in today else 1, not t.favorite, t.completed),
            )

        pri = self.filter_priority.currentData()
        if pri:
            tasks = [t for t in tasks if t.priority == pri]

        key = self.sort_by.currentData() or "updated_at"
        if key == "priority":
            tasks = self.ctx.tasks.sort_tasks(tasks, "priority", reverse=False)
        else:
            tasks = self.ctx.tasks.sort_tasks(tasks, key, reverse=(key != "title"))

        if self._selected and self._selected not in {t.id for t in tasks}:
            self._selected = None

        self.list.set_selected(self._selected)
        self.list.set_tasks(tasks)
        self.count_label.setText(f"{len(tasks)} tasks")
        self._update_selection_label()

    def _on_selected(self, task_id: str) -> None:
        self._selected = task_id
        self._update_selection_label()

    def _update_selection_label(self) -> None:
        if not self._selected:
            self.selection_label.setText("Click a task to select")
            return
        task = self.ctx.tasks.get(self._selected)
        name = task.title if task else self._selected
        self.selection_label.setText(f"Selected: {name}")

    def _require_selection(self) -> str | None:
        if self._selected and self.ctx.tasks.get(self._selected):
            return self._selected
        QMessageBox.information(
            self, "No selection", "Click a task first, then use Duplicate / Archive / Delete."
        )
        return None

    def new_task(self) -> None:
        projects = [(p.id, p.name) for p in self.ctx.projects.projects]
        dlg = TaskDialog(self.theme, projects=projects, parent=self)
        if dlg.exec():
            data = dlg.result_data()
            task = self.ctx.tasks.add(**data)
            self._selected = task.id
            self.ctx.stats.record_task_created()
            self.ctx.projects.refresh_counts()
            self.ctx.emit_change("tasks")

    def edit_task(self, task_id: str) -> None:
        task = self.ctx.tasks.get(task_id)
        if not task:
            return
        self._selected = task_id
        projects = [(p.id, p.name) for p in self.ctx.projects.projects]
        dlg = TaskDialog(self.theme, task=task, projects=projects, parent=self)
        if dlg.exec():
            self.ctx.tasks.update(task_id, **dlg.result_data())
            self.ctx.projects.refresh_counts()
            self.ctx.emit_change("tasks")

    def _toggle(self, task_id: str, checked: bool) -> None:
        task = self.ctx.tasks.get(task_id)
        if task and checked != task.completed:
            self.ctx.tasks.toggle_complete(task_id)
            if checked:
                self.ctx.stats.record_task_completed(task.category)
                self.ctx.achievements.on_task_completed(
                    self.ctx.stats.store.lifetime_tasks_completed
                )
            self.ctx.projects.refresh_counts()
            self.ctx.emit_change("tasks")

    def _timer(self, task_id: str) -> None:
        mins = self.ctx.settings.focus_minutes
        # Prefer today's daily dedication as timer length when set
        task = self.ctx.tasks.get(task_id)
        if task and task.daily_minutes_total > 0:
            mins = min(task.daily_minutes_total, 180)
        self.ctx.timers.start(kind="task", planned_seconds=mins * 60, task_id=task_id)
        self.ctx.signals.navigate.emit("pomodoro")
        self.ctx.emit_change("timers")

    def _dup(self) -> None:
        tid = self._require_selection()
        if tid:
            copy = self.ctx.tasks.duplicate(tid)
            if copy:
                self._selected = copy.id
            self.ctx.emit_change("tasks")

    def _archive(self) -> None:
        tid = self._require_selection()
        if tid:
            self.ctx.tasks.archive(tid)
            self._selected = None
            self.ctx.emit_change("tasks")

    def _delete(self) -> None:
        tid = self._require_selection()
        if not tid:
            return
        if (
            QMessageBox.question(self, "Delete", "Delete the selected task?")
            == QMessageBox.StandardButton.Yes
        ):
            self.ctx.tasks.delete(tid)
            self._selected = None
            self.ctx.emit_change("tasks")

    def _fav(self) -> None:
        tid = self._require_selection()
        if tid:
            self.ctx.tasks.toggle_favorite(tid)
            self.ctx.emit_change("tasks")
