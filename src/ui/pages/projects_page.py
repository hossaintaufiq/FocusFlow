"""Projects page."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QColorDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, GradientBar, PageHeader


class ProjectsPage(BasePage):
    page_id = "projects"

    def build(self) -> None:
        self.layout_main.addWidget(PageHeader("Projects", "Organize work by colored projects.", self.theme))
        bar = QHBoxLayout()
        add = QPushButton("+ New Project")
        add.setObjectName("primaryBtn")
        add.clicked.connect(self._add)
        bar.addWidget(add)
        bar.addStretch()
        self.layout_main.addLayout(bar)
        self.list_host = QVBoxLayout()
        self.layout_main.addLayout(self.list_host)
        self.layout_main.addStretch()

    def refresh(self) -> None:
        self.ctx.projects.refresh_counts()
        while self.list_host.count():
            item = self.list_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for project in self.ctx.projects.projects:
            card = GlassCard(self.theme)
            row = QHBoxLayout()
            swatch = QLabel("●")
            swatch.setStyleSheet(f"color: {project.color}; font-size: 18pt; border: none;")
            row.addWidget(swatch)
            col = QVBoxLayout()
            name = QLabel(project.name)
            name.setStyleSheet("font-weight: 700; font-size: 12pt; border: none;")
            meta = QLabel(
                f"{project.completed_count}/{project.task_count} tasks · "
                f"{project.progress_percent}% · deadline {project.deadline or '—'}"
            )
            meta.setObjectName("muted")
            col.addWidget(name)
            col.addWidget(meta)
            bar = GradientBar(self.theme)
            bar.set_value(project.progress_percent)
            col.addWidget(bar)
            row.addLayout(col, 1)
            edit = QPushButton("Edit")
            edit.clicked.connect(lambda _, p=project.id: self._edit(p))
            delete = QPushButton("Delete")
            delete.setObjectName("dangerBtn")
            delete.clicked.connect(lambda _, p=project.id: self._delete(p))
            row.addWidget(edit)
            row.addWidget(delete)
            card.body.addLayout(row)
            self.list_host.addWidget(card)
        if not self.ctx.projects.projects:
            self.list_host.addWidget(QLabel("No projects yet. Create one to group your tasks."))

    def _add(self) -> None:
        name, ok = QInputDialog.getText(self, "New Project", "Project name:")
        if ok and name.strip():
            color = QColorDialog.getColor(parent=self)
            self.ctx.projects.add(
                name=name.strip(),
                color=color.name() if color.isValid() else "#38BDF8",
            )
            self.ctx.emit_change("projects")

    def _edit(self, project_id: str) -> None:
        project = self.ctx.projects.get(project_id)
        if not project:
            return
        name, ok = QInputDialog.getText(self, "Edit Project", "Name:", text=project.name)
        if ok and name.strip():
            self.ctx.projects.update(project_id, name=name.strip())
            self.ctx.emit_change("projects")

    def _delete(self, project_id: str) -> None:
        if QMessageBox.question(self, "Delete", "Delete this project?") == QMessageBox.StandardButton.Yes:
            self.ctx.projects.delete(project_id)
            self.ctx.emit_change("projects")
