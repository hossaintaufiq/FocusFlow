"""Pomodoro timer page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.ui.pages.base_page import BasePage
from src.utils.helpers import format_clock, format_duration
from src.widgets.common import GlassCard, PageHeader, ProgressRing


class PomodoroPage(BasePage):
    page_id = "pomodoro"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader("Pomodoro", "Focus · Break · Repeat", self.theme)
        )
        card = GlassCard(self.theme)
        self.mode_label = QLabel("Focus Session")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setStyleSheet("font-size: 12pt; font-weight: 600; border: none;")
        self.clock = QLabel("25:00")
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock.setStyleSheet(
            f"font-size: 48pt; font-weight: 700; color: {self.theme.accent}; border: none;"
        )
        self.ring = ProgressRing(self.theme, size=140)
        ring_row = QHBoxLayout()
        ring_row.addStretch()
        ring_row.addWidget(self.ring)
        ring_row.addStretch()
        card.body.addWidget(self.mode_label)
        card.body.addWidget(self.clock)
        card.body.addLayout(ring_row)
        self.layout_main.addWidget(card)

        controls = QHBoxLayout()
        for text, slot, oid in (
            ("Start Focus", self._start_focus, "primaryBtn"),
            ("Short Break", self._short, ""),
            ("Long Break", self._long, ""),
            ("Pause", self.ctx.timers.pause, ""),
            ("Resume", self.ctx.timers.resume, ""),
            ("Stop", self.ctx.timers.stop, "dangerBtn"),
            ("Reset", self.ctx.timers.reset, ""),
        ):
            btn = QPushButton(text)
            if oid:
                btn.setObjectName(oid)
            btn.clicked.connect(slot)
            btn.clicked.connect(lambda: self.ctx.emit_change("timers"))
            controls.addWidget(btn)
        self.layout_main.addLayout(controls)

        custom = QHBoxLayout()
        custom.addWidget(QLabel("Custom minutes:"))
        self.custom_mins = QSpinBox()
        self.custom_mins.setRange(1, 180)
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

    def _start_focus(self) -> None:
        mins = self.ctx.settings.focus_minutes
        self.ctx.timers.start(kind="focus", planned_seconds=mins * 60)

    def _short(self) -> None:
        mins = self.ctx.settings.short_break_minutes
        self.ctx.timers.start(kind="short_break", planned_seconds=mins * 60)

    def _long(self) -> None:
        mins = self.ctx.settings.long_break_minutes
        self.ctx.timers.start(kind="long_break", planned_seconds=mins * 60)

    def _custom(self) -> None:
        self.ctx.timers.start(
            kind="custom", planned_seconds=self.custom_mins.value() * 60
        )
        self.ctx.emit_change("timers")

    def refresh(self) -> None:
        active = self.ctx.timers.active
        rem = self.ctx.timers.remaining_seconds()
        if active.status == "idle" and active.elapsed_seconds == 0:
            rem = active.planned_seconds or self.ctx.settings.focus_minutes * 60
        self.clock.setText(format_clock(rem))
        planned = max(1, active.planned_seconds)
        pct = 100.0 * active.elapsed_seconds / planned
        self.ring.set_value(pct)
        self.mode_label.setText(f"{active.kind.replace('_', ' ').title()} · {active.status}")
        totals = self.ctx.timers.focus_totals()
        self.stats_label.setText(
            f"Today: {format_duration(totals['today'])}\n"
            f"Week: {format_duration(totals['week'])}\n"
            f"Month: {format_duration(totals['month'])}\n"
            f"Lifetime: {format_duration(totals['lifetime'])}\n"
            f"Pomodoros done this cycle: {active.pomodoro_count}"
        )
