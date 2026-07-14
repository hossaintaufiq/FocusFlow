"""Task create/edit dialog."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.models.task import Task
from src.utils.config import TASK_PRIORITIES, TASK_STATUSES, ThemeColors


def _unit_spin(maximum: int, suffix: str, value: int = 0) -> QSpinBox:
    box = QSpinBox()
    box.setRange(0, maximum)
    box.setSuffix(f" {suffix}")
    box.setValue(max(0, value))
    box.setMinimumWidth(90)
    return box


class TaskDialog(QDialog):
    def __init__(
        self,
        theme: ThemeColors,
        task: Task | None = None,
        projects: list[tuple[str, str]] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Task" if task else "New Task")
        self.resize(520, 640)
        self._theme = theme
        self._task = task
        if task:
            task.ensure_estimate_fields()

        lay = QVBoxLayout(self)
        form = QFormLayout()

        self.title = QLineEdit(task.title if task else "")
        self.title.setPlaceholderText("What needs doing?")
        form.addRow("Title", self.title)

        self.description = QTextEdit(task.description if task else "")
        self.description.setPlaceholderText("Description")
        self.description.setFixedHeight(70)
        form.addRow("Description", self.description)

        self.category = QLineEdit(task.category if task else "general")
        form.addRow("Category", self.category)

        self.priority = QComboBox()
        self.priority.addItems(list(TASK_PRIORITIES))
        if task:
            self.priority.setCurrentText(task.priority)
        form.addRow("Priority", self.priority)

        self.status = QComboBox()
        self.status.addItems(list(TASK_STATUSES))
        if task:
            self.status.setCurrentText(task.status)
        form.addRow("Status", self.status)

        self.project = QComboBox()
        self.project.addItem("— None —", "")
        for pid, name in projects or []:
            self.project.addItem(name, pid)
        if task and task.project_id:
            idx = self.project.findData(task.project_id)
            if idx >= 0:
                self.project.setCurrentIndex(idx)
        form.addRow("Project", self.project)

        self.tags = QLineEdit(", ".join(task.tags) if task else "")
        self.tags.setPlaceholderText("tag1, tag2")
        form.addRow("Tags", self.tags)

        dates = QHBoxLayout()
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        if task and task.date:
            self.date.setDate(QDate.fromString(task.date[:10], "yyyy-MM-dd"))
        else:
            self.date.setDate(QDate.currentDate())

        self.deadline_enabled = QCheckBox("Set deadline")
        self.deadline = QDateEdit()
        self.deadline.setCalendarPopup(True)
        self.deadline.setDisplayFormat("yyyy-MM-dd")
        if task and task.deadline:
            self.deadline_enabled.setChecked(True)
            self.deadline.setDate(QDate.fromString(task.deadline[:10], "yyyy-MM-dd"))
        else:
            self.deadline_enabled.setChecked(False)
            self.deadline.setDate(QDate.currentDate().addDays(7))
        self.deadline.setEnabled(self.deadline_enabled.isChecked())
        self.deadline_enabled.toggled.connect(self.deadline.setEnabled)

        dates.addWidget(self.date)
        dates.addWidget(self.deadline_enabled)
        dates.addWidget(self.deadline)
        form.addRow("Start date", dates)

        # --- Duration estimate: Days / Hours / Mins ---
        est_wrap = QWidget()
        est_lay = QVBoxLayout(est_wrap)
        est_lay.setContentsMargins(0, 0, 0, 0)
        est_lay.setSpacing(6)

        est_hint = QLabel("How long does this task take overall?")
        est_hint.setStyleSheet(f"color: {theme.text_muted}; font-size: 9pt; border: none;")
        est_lay.addWidget(est_hint)

        est_row = QHBoxLayout()
        self.est_days = _unit_spin(365, "days", task.estimate_days if task else 0)
        self.est_hours = _unit_spin(23, "hrs", task.estimate_hours if task else 0)
        self.est_mins = _unit_spin(59, "min", task.estimate_mins if task else 0)
        est_row.addWidget(self.est_days)
        est_row.addWidget(self.est_hours)
        est_row.addWidget(self.est_mins)
        est_row.addStretch()
        est_lay.addLayout(est_row)
        form.addRow("Estimate", est_wrap)

        # --- Daily dedication ---
        daily_wrap = QWidget()
        daily_lay = QVBoxLayout(daily_wrap)
        daily_lay.setContentsMargins(0, 0, 0, 0)
        daily_lay.setSpacing(6)

        daily_hint = QLabel(
            "How much time will you give it each day?\n"
            "Example: task needs 7 days, but you’ll work 3 hours daily."
        )
        daily_hint.setWordWrap(True)
        daily_hint.setStyleSheet(f"color: {theme.text_muted}; font-size: 9pt; border: none;")
        daily_lay.addWidget(daily_hint)

        daily_row = QHBoxLayout()
        self.daily_hours = _unit_spin(24, "hrs/day", task.daily_hours if task else 0)
        self.daily_mins = _unit_spin(59, "min/day", task.daily_mins if task else 0)
        daily_row.addWidget(self.daily_hours)
        daily_row.addWidget(self.daily_mins)
        daily_row.addStretch()
        daily_lay.addLayout(daily_row)

        self.estimate_preview = QLabel()
        self.estimate_preview.setWordWrap(True)
        self.estimate_preview.setStyleSheet(
            f"color: {theme.accent}; font-weight: 600; font-size: 10pt; border: none;"
        )
        daily_lay.addWidget(self.estimate_preview)
        form.addRow("Daily focus", daily_wrap)

        for spin in (
            self.est_days,
            self.est_hours,
            self.est_mins,
            self.daily_hours,
            self.daily_mins,
        ):
            spin.valueChanged.connect(self._update_preview)
        self._update_preview()

        self.notes = QTextEdit(task.notes if task else "")
        self.notes.setFixedHeight(56)
        form.addRow("Notes", self.notes)

        lay.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _update_preview(self) -> None:
        days = self.est_days.value()
        hours = self.est_hours.value()
        mins = self.est_mins.value()
        dh = self.daily_hours.value()
        dm = self.daily_mins.value()
        daily = dh * 60 + dm

        bits: list[str] = []
        if days:
            bits.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            bits.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if mins:
            bits.append(f"{mins} minute{'s' if mins != 1 else ''}")
        duration = ", ".join(bits) if bits else "no duration set"

        if daily and days:
            total = days * daily + hours * 60 + mins
            th, tm = divmod(total, 60)
            daily_label = f"{dh}h/day" if not dm else (f"{dh}h {dm}m/day" if dh else f"{dm}m/day")
            total_label = f"{th}h" if not tm else f"{th}h {tm}m"
            self.estimate_preview.setText(
                f"Plan: {duration} · {daily_label}  ->  about {total_label} total work"
            )
        elif daily:
            daily_label = f"{dh}h/day" if not dm else (f"{dh}h {dm}m/day" if dh else f"{dm}m/day")
            self.estimate_preview.setText(f"Plan: {duration} · {daily_label}")
        elif bits:
            self.estimate_preview.setText(f"Plan: {duration}")
        else:
            self.estimate_preview.setText("Plan: set an estimate and/or daily focus above")

    def result_data(self) -> dict:
        tags = [t.strip() for t in self.tags.text().split(",") if t.strip()]
        data = {
            "title": self.title.text().strip() or "Untitled",
            "description": self.description.toPlainText().strip(),
            "category": self.category.text().strip() or "general",
            "priority": self.priority.currentText(),
            "status": self.status.currentText(),
            "project_id": self.project.currentData() or "",
            "tags": tags,
            "date": self.date.date().toString("yyyy-MM-dd"),
            "deadline": (
                self.deadline.date().toString("yyyy-MM-dd")
                if self.deadline_enabled.isChecked()
                else ""
            ),
            "estimate_days": self.est_days.value(),
            "estimate_hours": self.est_hours.value(),
            "estimate_mins": self.est_mins.value(),
            "daily_hours": self.daily_hours.value(),
            "daily_mins": self.daily_mins.value(),
            "notes": self.notes.toPlainText().strip(),
        }
        # Sync derived total
        tmp = Task(**{k: v for k, v in data.items() if k in Task.__dataclass_fields__})
        tmp.sync_estimated_minutes()
        data["estimated_minutes"] = tmp.estimated_minutes
        # Keep status/completed in sync when user picks completed in dialog
        if data["status"] == "completed":
            data["completed"] = True
        elif data["status"] != "completed":
            # Don't force-uncomplete if only editing other fields while already done?
            # If they explicitly change away from completed, clear it.
            if self._task and self._task.status == "completed" and data["status"] != "completed":
                data["completed"] = False
            elif not self._task:
                data["completed"] = False
        return data
