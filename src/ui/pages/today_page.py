"""Today's tasks page with clear selection and professional task list."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, PageHeader
from src.widgets.task_dialog import TaskDialog
from src.widgets.task_widgets import TaskList


class TodayPage(BasePage):
    page_id = "today"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader(
                "Today's Tasks",
                "Click a task to select it — then Edit, Delete, Archive, or Focus.",
                self.theme,
            )
        )
        self._selected: str | None = None

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search title, tags, category…  (Ctrl+F)")
        self.search.setObjectName("globalSearch")
        self.search.setMinimumHeight(36)
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
        new_btn.setMinimumHeight(36)
        new_btn.clicked.connect(self.new_task)
        toolbar.addWidget(new_btn)
        self.layout_main.addLayout(toolbar)

        # Selection banner — always visible so user knows the target of actions
        self.selection_banner = QFrame()
        banner_lay = QHBoxLayout(self.selection_banner)
        banner_lay.setContentsMargins(14, 10, 14, 10)
        banner_lay.setSpacing(12)
        self.selection_dot = QLabel("")
        self.selection_dot.setFixedSize(10, 10)
        self.selection_label = QLabel("No task selected — click a row to select")
        self.selection_label.setWordWrap(True)
        self.count_label = QLabel()
        self.count_label.setObjectName("muted")
        banner_lay.addWidget(self.selection_dot)
        banner_lay.addWidget(self.selection_label, 1)
        banner_lay.addWidget(self.count_label)
        self._style_banner(active=False)
        self.layout_main.addWidget(self.selection_banner)

        # Action toolbar
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.btn_edit = QPushButton("Edit")
        self.btn_dup = QPushButton("Duplicate")
        self.btn_fav = QPushButton("Favorite")
        self.btn_focus = QPushButton("Start Focus")
        self.btn_focus.setObjectName("primaryBtn")
        self.btn_archive = QPushButton("Archive")
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("dangerBtn")

        self.btn_edit.clicked.connect(self._edit_selected)
        self.btn_dup.clicked.connect(self._dup)
        self.btn_fav.clicked.connect(self._fav)
        self.btn_focus.clicked.connect(self._focus_selected)
        self.btn_archive.clicked.connect(self._archive)
        self.btn_delete.clicked.connect(self._delete)

        for b in (
            self.btn_edit,
            self.btn_dup,
            self.btn_fav,
            self.btn_focus,
            self.btn_archive,
            self.btn_delete,
        ):
            b.setMinimumHeight(34)
            b.setEnabled(False)
            actions.addWidget(b)
        actions.addStretch()
        hint = QLabel("Tip: click the checkbox to complete · double-click row to edit")
        hint.setObjectName("muted")
        actions.addWidget(hint)
        self.layout_main.addLayout(actions)

        card = GlassCard(self.theme)
        self.list = TaskList(self.theme)
        self.list.toggled.connect(self._toggle)
        self.list.open_requested.connect(self.edit_task)
        self.list.timer_requested.connect(self._timer)
        self.list.selected.connect(self._on_selected)
        card.body.addWidget(self.list)
        self.layout_main.addWidget(card, 1)

    def _style_banner(self, *, active: bool) -> None:
        t = self.theme
        if active:
            self.selection_banner.setStyleSheet(
                f"QFrame {{ background: {t.accent_dim}; border: 1px solid {t.accent}; "
                f"border-radius: 12px; }}"
            )
            self.selection_dot.setStyleSheet(
                f"background: {t.accent}; border-radius: 5px; border: none;"
            )
            self.selection_label.setStyleSheet(
                f"color: {t.text_primary}; font-weight: 650; font-size: 10.5pt; "
                "background: transparent; border: none;"
            )
        else:
            self.selection_banner.setStyleSheet(
                f"QFrame {{ background: {t.bg_tertiary}; border: 1px solid {t.border}; "
                f"border-radius: 12px; }}"
            )
            self.selection_dot.setStyleSheet(
                f"background: {t.text_muted}; border-radius: 5px; border: none;"
            )
            self.selection_label.setStyleSheet(
                f"color: {t.text_muted}; font-weight: 500; font-size: 10pt; "
                "background: transparent; border: none;"
            )

    def _set_actions_enabled(self, enabled: bool) -> None:
        for b in (
            self.btn_edit,
            self.btn_dup,
            self.btn_fav,
            self.btn_focus,
            self.btn_archive,
            self.btn_delete,
        ):
            b.setEnabled(enabled)

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
        done = sum(1 for t in tasks if t.completed)
        self.count_label.setText(f"{done}/{len(tasks)} done")
        self._update_selection_ui()

    def _on_selected(self, task_id: str) -> None:
        self._selected = task_id
        self._update_selection_ui()

    def _update_selection_ui(self) -> None:
        task = self.ctx.tasks.get(self._selected) if self._selected else None
        if not task:
            self._selected = None
            self._style_banner(active=False)
            self.selection_label.setText("No task selected — click a row to select")
            self._set_actions_enabled(False)
            return

        self._style_banner(active=True)
        status = "completed" if task.completed else task.status.replace("_", " ")
        extras = []
        if task.priority:
            extras.append(task.priority)
        if task.estimate_summary():
            extras.append(task.estimate_summary())
        extra = f"  ·  {' · '.join(extras)}" if extras else ""
        self.selection_label.setText(
            f"Selected:  {task.title}    ({status}{extra})"
        )
        self._set_actions_enabled(True)
        self.btn_fav.setText("Unfavorite" if task.favorite else "Favorite")
        self.list.set_selected(self._selected)

    def _require_selection(self) -> str | None:
        if self._selected and self.ctx.tasks.get(self._selected):
            return self._selected
        QMessageBox.information(
            self,
            "No selection",
            "Click a task row first so it shows the SELECTED badge,\n"
            "then use Edit / Delete / Archive / Focus.",
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
        self._update_selection_ui()
        projects = [(p.id, p.name) for p in self.ctx.projects.projects]
        dlg = TaskDialog(self.theme, task=task, projects=projects, parent=self)
        if dlg.exec():
            self.ctx.tasks.update(task_id, **dlg.result_data())
            self.ctx.projects.refresh_counts()
            self.ctx.emit_change("tasks")

    def _edit_selected(self) -> None:
        tid = self._require_selection()
        if tid:
            self.edit_task(tid)

    def _focus_selected(self) -> None:
        tid = self._require_selection()
        if tid:
            self.ctx.start_task_focus(tid, navigate=True)

    def _toggle(self, task_id: str, checked: bool) -> None:
        task = self.ctx.tasks.get(task_id)
        if not task:
            return
        self._selected = task_id
        if checked != task.completed:
            self.ctx.tasks.toggle_complete(task_id)
            if checked:
                self.ctx.stats.record_task_completed(task.category)
                self.ctx.achievements.on_task_completed(
                    self.ctx.stats.store.lifetime_tasks_completed
                )
            self.ctx.projects.refresh_counts()
            self.ctx.emit_change("tasks")
        else:
            self._update_selection_ui()

    def _timer(self, task_id: str) -> None:
        self._selected = task_id
        self.ctx.start_task_focus(task_id, navigate=True)

    def _dup(self) -> None:
        tid = self._require_selection()
        if tid:
            copy = self.ctx.tasks.duplicate(tid)
            if copy:
                self._selected = copy.id
            self.ctx.emit_change("tasks")

    def _archive(self) -> None:
        tid = self._require_selection()
        if not tid:
            return
        task = self.ctx.tasks.get(tid)
        name = task.title if task else "this task"
        if (
            QMessageBox.question(self, "Archive", f"Archive “{name}”?")
            == QMessageBox.StandardButton.Yes
        ):
            self.ctx.tasks.archive(tid)
            self._selected = None
            self.ctx.emit_change("tasks")

    def _delete(self) -> None:
        tid = self._require_selection()
        if not tid:
            return
        task = self.ctx.tasks.get(tid)
        name = task.title if task else "this task"
        if (
            QMessageBox.question(self, "Delete", f"Permanently delete “{name}”?")
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
