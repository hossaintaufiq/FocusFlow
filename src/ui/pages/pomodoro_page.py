"""Pomodoro timer page — task-linked focus with dual clocks."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.utils.helpers import format_clock, format_duration
from src.widgets.common import GlassCard, GradientBar, PageHeader, ProgressRing


class PomodoroPage(BasePage):
    page_id = "pomodoro"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader(
                "Pomodoro",
                "Start a task to run a focus slice — session clock + task budget.",
                self.theme,
            )
        )

        # --- Pick a task ---
        pick = GlassCard(self.theme)
        pick.body.addWidget(QLabel("Start focus on a task"))
        pick_row = QHBoxLayout()
        self.task_picker = QComboBox()
        self.task_picker.setMinimumWidth(280)
        start_task_btn = QPushButton("Start Task Focus")
        start_task_btn.setObjectName("primaryBtn")
        start_task_btn.clicked.connect(self._start_selected_task)
        pick_row.addWidget(self.task_picker, 1)
        pick_row.addWidget(start_task_btn)
        pick.body.addLayout(pick_row)
        self.layout_main.addWidget(pick)

        # --- Active task panel (dual clocks) ---
        self.task_card = GlassCard(self.theme)
        self.task_title = QLabel("No task selected")
        self.task_title.setStyleSheet(
            f"font-size: 14pt; font-weight: 700; color: {self.theme.text_primary}; border: none;"
        )
        self.task_plan = QLabel("")
        self.task_plan.setWordWrap(True)
        self.task_plan.setStyleSheet(
            f"color: {self.theme.text_secondary}; font-size: 10pt; border: none;"
        )
        self.task_card.body.addWidget(self.task_title)
        self.task_card.body.addWidget(self.task_plan)

        clocks = QHBoxLayout()
        # Session clock (this Pomodoro slice)
        session_col = QVBoxLayout()
        session_lbl = QLabel("This focus slice")
        session_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        session_lbl.setObjectName("muted")
        self.session_clock = QLabel("25:00")
        self.session_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_clock.setStyleSheet(
            f"font-size: 40pt; font-weight: 700; color: {self.theme.accent}; border: none;"
        )
        self.session_ring = ProgressRing(self.theme, size=120)
        sr = QHBoxLayout()
        sr.addStretch()
        sr.addWidget(self.session_ring)
        sr.addStretch()
        session_col.addWidget(session_lbl)
        session_col.addWidget(self.session_clock)
        session_col.addLayout(sr)

        # Task budget clock (remaining for whole task)
        budget_col = QVBoxLayout()
        budget_lbl = QLabel("Time left for task")
        budget_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        budget_lbl.setObjectName("muted")
        self.budget_clock = QLabel("--:--")
        self.budget_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.budget_clock.setStyleSheet(
            f"font-size: 40pt; font-weight: 700; color: {self.theme.info}; border: none;"
        )
        self.budget_bar = GradientBar(self.theme)
        self.budget_spent = QLabel("")
        self.budget_spent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.budget_spent.setObjectName("muted")
        budget_col.addWidget(budget_lbl)
        budget_col.addWidget(self.budget_clock)
        budget_col.addWidget(self.budget_bar)
        budget_col.addWidget(self.budget_spent)

        clocks.addLayout(session_col, 1)
        clocks.addLayout(budget_col, 1)
        self.task_card.body.addLayout(clocks)

        self.mode_label = QLabel("Idle")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setStyleSheet("font-weight: 600; border: none;")
        self.task_card.body.addWidget(self.mode_label)

        done_row = QHBoxLayout()
        self.mark_done_btn = QPushButton("Mark task done")
        self.mark_done_btn.setObjectName("primaryBtn")
        self.mark_done_btn.clicked.connect(self._toggle_task_done)
        self.another_slice_btn = QPushButton("Another slice")
        self.another_slice_btn.clicked.connect(self._another_slice)
        self.clear_task_btn = QPushButton("Clear task")
        self.clear_task_btn.setObjectName("ghostBtn")
        self.clear_task_btn.clicked.connect(self._clear_task)
        done_row.addWidget(self.mark_done_btn)
        done_row.addWidget(self.another_slice_btn)
        done_row.addWidget(self.clear_task_btn)
        self.task_card.body.addLayout(done_row)
        self.layout_main.addWidget(self.task_card)

        # --- Generic Pomodoro controls ---
        card = GlassCard(self.theme)
        card.body.addWidget(QLabel("Standard Pomodoro (no task)"))
        controls = QHBoxLayout()
        for text, slot, oid in (
            ("Start Focus", self._start_focus, "primaryBtn"),
            ("Short Break", self._short, ""),
            ("Long Break", self._long, ""),
            ("Pause", self._pause, ""),
            ("Resume", self._resume, ""),
            ("Stop", self._stop, "dangerBtn"),
        ):
            btn = QPushButton(text)
            if oid:
                btn.setObjectName(oid)
            btn.clicked.connect(slot)
            controls.addWidget(btn)
        card.body.addLayout(controls)
        self.layout_main.addWidget(card)

        custom = QHBoxLayout()
        custom.addWidget(QLabel("Custom minutes:"))
        self.custom_mins = QSpinBox()
        self.custom_mins.setRange(1, 480)
        self.custom_mins.setValue(25)
        custom_btn = QPushButton("Start Custom")
        custom_btn.clicked.connect(self._custom)
        custom.addWidget(self.custom_mins)
        custom.addWidget(custom_btn)
        custom.addStretch()
        self.layout_main.addLayout(custom)

        stats = GlassCard(self.theme)
        self.stats_label = QLabel()
        self.stats_label.setObjectName("muted")
        stats.body.addWidget(QLabel("Focus Totals"))
        stats.body.addWidget(self.stats_label)
        self.layout_main.addWidget(stats)
        self.layout_main.addStretch()

        self.ctx.timers.tick.connect(lambda *_: self.refresh())
        self.ctx.timers.state_changed.connect(lambda *_: self.refresh())
        self.ctx.timers.finished.connect(lambda *_: self.refresh())

    def _pause(self) -> None:
        self.ctx.timers.pause()
        self.ctx.emit_change("timers")

    def _resume(self) -> None:
        self.ctx.timers.resume()
        self.ctx.emit_change("timers")

    def _stop(self) -> None:
        self.ctx.timers.stop()
        self.ctx.emit_change("timers")

    def _start_selected_task(self) -> None:
        task_id = self.task_picker.currentData()
        if task_id:
            self.ctx.start_task_focus(str(task_id), navigate=False)

    def _start_focus(self) -> None:
        mins = self.ctx.settings.focus_minutes
        self.ctx.timers.start(kind="focus", planned_seconds=mins * 60)
        self.ctx.emit_change("timers")

    def _short(self) -> None:
        mins = self.ctx.settings.short_break_minutes
        self.ctx.timers.start(kind="short_break", planned_seconds=mins * 60)
        self.ctx.emit_change("timers")

    def _long(self) -> None:
        mins = self.ctx.settings.long_break_minutes
        self.ctx.timers.start(kind="long_break", planned_seconds=mins * 60)
        self.ctx.emit_change("timers")

    def _custom(self) -> None:
        self.ctx.timers.start(
            kind="custom", planned_seconds=self.custom_mins.value() * 60
        )
        self.ctx.emit_change("timers")

    def _toggle_task_done(self) -> None:
        self.ctx.toggle_task_done()
        self.refresh()

    def _another_slice(self) -> None:
        task = self.ctx.active_task()
        if not task or task.completed:
            self.ctx.signals.toast.emit("Select a task first")
            return
        secs = task.pomodoro_session_seconds(self.ctx.settings.focus_minutes)
        self.ctx.timers.start_task_session(task.id, secs)
        self.ctx.emit_change("timers")

    def _clear_task(self) -> None:
        self.ctx.timers.reset(clear_task=True)
        self.ctx.emit_change("timers")

    def _reload_task_picker(self) -> None:
        current = self.task_picker.currentData()
        self.task_picker.blockSignals(True)
        self.task_picker.clear()
        self.task_picker.addItem("— Choose a task —", "")
        for task in self.ctx.tasks.tasks:
            if task.archived or task.completed:
                continue
            label = task.title
            if task.estimate_summary():
                label = f"{task.title}  ({task.estimate_summary()})"
            self.task_picker.addItem(label, task.id)
        if current:
            idx = self.task_picker.findData(current)
            if idx >= 0:
                self.task_picker.setCurrentIndex(idx)
        self.task_picker.blockSignals(False)

    def refresh(self) -> None:
        self._reload_task_picker()
        active = self.ctx.timers.active
        task = self.ctx.active_task()

        # Session clock
        rem_session = self.ctx.timers.remaining_seconds()
        if active.status == "idle" and active.elapsed_seconds == 0 and not task:
            rem_session = self.ctx.settings.focus_minutes * 60
        elif active.status == "idle" and task and active.kind == "task":
            rem_session = task.pomodoro_session_seconds(self.ctx.settings.focus_minutes)
        self.session_clock.setText(format_clock(rem_session))
        planned_slice = max(1, active.planned_seconds if active.status != "idle" else rem_session)
        if active.status in ("running", "paused"):
            self.session_ring.set_value(100.0 * active.elapsed_seconds / planned_slice)
        else:
            self.session_ring.set_value(0)

        # Task panel
        if task:
            self.task_card.show()
            self.task_title.setText(task.title)
            self.task_plan.setText(f"You planned: {task.planned_time_label()}")
            live_extra = active.elapsed_seconds if active.status in ("running", "paused") else 0
            remaining = task.remaining_budget_seconds(live_extra)
            budget = task.budget_seconds()
            spent = budget - remaining if budget else task.actual_seconds + live_extra

            if budget > 0:
                self.budget_clock.setText(format_clock(remaining))
                pct_used = min(100.0, 100.0 * spent / budget)
                self.budget_bar.set_value(pct_used)
                self.budget_spent.setText(
                    f"{format_duration(spent)} used of {format_duration(budget)}"
                )
            elif task.daily_minutes_total:
                self.budget_clock.setText(format_clock(live_extra))
                self.budget_bar.set_value(0)
                self.budget_spent.setText(
                    f"Today slice: {format_duration(task.daily_minutes_total * 60)} · "
                    f"logged {format_duration(task.actual_seconds)}"
                )
            else:
                self.budget_clock.setText(format_duration(task.actual_seconds + live_extra))
                self.budget_bar.set_value(0)
                self.budget_spent.setText("No total budget — time logged accumulates")

            if task.completed:
                self.mark_done_btn.setText("Reopen task")
            else:
                self.mark_done_btn.setText("Mark task done")

            status = active.status
            if active.kind == "task":
                self.mode_label.setText(
                    f"Task focus · {status} · slice {format_clock(planned_slice)}"
                )
            else:
                self.mode_label.setText(f"Task linked · timer {status}")
        else:
            self.task_title.setText("No task selected")
            self.task_plan.setText("Pick a task above or start focus from Today's Tasks.")
            self.budget_clock.setText("--:--")
            self.budget_bar.set_value(0)
            self.budget_spent.setText("")
            self.mark_done_btn.setText("Mark task done")
            self.mode_label.setText(
                f"{active.kind.replace('_', ' ').title()} · {active.status}"
            )

        totals = self.ctx.timers.focus_totals()
        self.stats_label.setText(
            f"Today: {format_duration(totals['today'])}\n"
            f"Week: {format_duration(totals['week'])}\n"
            f"Month: {format_duration(totals['month'])}\n"
            f"Lifetime: {format_duration(totals['lifetime'])}\n"
            f"Pomodoros this cycle: {active.pomodoro_count}"
        )

    def on_show(self) -> None:
        self.refresh()
        tid = self.ctx.timers.active.task_id
        if tid:
            idx = self.task_picker.findData(tid)
            if idx >= 0:
                self.task_picker.setCurrentIndex(idx)
