"""Dashboard page — greeting, progress, charts, quick add."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.utils.helpers import format_clock, format_date_long, format_duration, greeting_for_hour
from src.widgets.charts import ChartWidget
from src.widgets.common import GlassCard, PageHeader, ProgressRing, StatChip
from src.widgets.task_widgets import TaskList


class DashboardPage(BasePage):
    page_id = "dashboard"

    def build(self) -> None:
        self.header = PageHeader("Dashboard", theme=self.theme)
        self.layout_main.addWidget(self.header)

        # Greeting row
        top = QHBoxLayout()
        greet_card = GlassCard(self.theme)
        self.greet_label = QLabel()
        self.greet_label.setStyleSheet("font-size: 22pt; font-weight: 700; border: none;")
        self.date_label = QLabel()
        self.date_label.setObjectName("muted")
        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            f"font-size: 18pt; font-weight: 600; color: {self.theme.accent}; border: none;"
        )
        greet_card.body.addWidget(self.greet_label)
        greet_card.body.addWidget(self.date_label)
        greet_card.body.addWidget(self.time_label)
        top.addWidget(greet_card, 2)

        ring_card = GlassCard(self.theme)
        ring_row = QHBoxLayout()
        self.ring = ProgressRing(self.theme, size=110)
        ring_row.addWidget(self.ring)
        ring_meta = QVBoxLayout()
        self.progress_caption = QLabel("Today's Progress")
        self.progress_caption.setStyleSheet("font-weight: 600; border: none;")
        self.progress_detail = QLabel()
        self.progress_detail.setObjectName("muted")
        ring_meta.addStretch()
        ring_meta.addWidget(self.progress_caption)
        ring_meta.addWidget(self.progress_detail)
        ring_meta.addStretch()
        ring_row.addLayout(ring_meta)
        ring_card.body.addLayout(ring_row)
        top.addWidget(ring_card, 2)
        self.layout_main.addLayout(top)

        # Stats chips
        chips = QHBoxLayout()
        self.chip_completed = StatChip(self.theme, "Completed")
        self.chip_pending = StatChip(self.theme, "Pending", accent=self.theme.warning)
        self.chip_focus = StatChip(self.theme, "Focus Today", accent=self.theme.info)
        self.chip_streak = StatChip(self.theme, "Current Streak", accent=self.theme.success)
        self.chip_score = StatChip(self.theme, "Productivity", accent=self.theme.accent)
        for c in (
            self.chip_completed,
            self.chip_pending,
            self.chip_focus,
            self.chip_streak,
            self.chip_score,
        ):
            chips.addWidget(c)
        self.layout_main.addLayout(chips)

        # Quote + active timer
        mid = QHBoxLayout()
        quote_card = GlassCard(self.theme)
        qtitle = QLabel("Daily Quote")
        qtitle.setObjectName("sectionTitle")
        self.quote_label = QLabel()
        self.quote_label.setWordWrap(True)
        self.quote_label.setStyleSheet(
            f"color: {self.theme.text_secondary}; font-style: italic; border: none;"
        )
        quote_card.body.addWidget(qtitle)
        quote_card.body.addWidget(self.quote_label)
        mid.addWidget(quote_card, 2)

        timer_card = GlassCard(self.theme)
        ttitle = QLabel("Active Timer")
        ttitle.setObjectName("sectionTitle")
        self.active_timer_label = QLabel("Idle")
        self.active_timer_label.setStyleSheet(
            f"font-size: 20pt; font-weight: 700; color: {self.theme.accent}; border: none;"
        )
        self.active_timer_meta = QLabel()
        self.active_timer_meta.setObjectName("muted")
        timer_card.body.addWidget(ttitle)
        timer_card.body.addWidget(self.active_timer_label)
        timer_card.body.addWidget(self.active_timer_meta)
        mid.addWidget(timer_card, 1)
        self.layout_main.addLayout(mid)

        # Quick add
        quick = GlassCard(self.theme)
        qh = QLabel("Quick Add Task")
        qh.setObjectName("sectionTitle")
        quick.body.addWidget(qh)
        row = QHBoxLayout()
        self.quick_input = QLineEdit()
        self.quick_input.setPlaceholderText("Capture a task and press Enter…")
        self.quick_input.returnPressed.connect(self._quick_add)
        add_btn = QPushButton("Add")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._quick_add)
        row.addWidget(self.quick_input, 1)
        row.addWidget(add_btn)
        quick.body.addLayout(row)
        self.layout_main.addWidget(quick)

        # Upcoming + recent
        bottom = QHBoxLayout()
        up_card = GlassCard(self.theme)
        up_card.body.addWidget(QLabel("Upcoming / Today's Focus"))
        self.upcoming_list = TaskList(self.theme)
        self.upcoming_list.toggled.connect(self._toggle_task)
        self.upcoming_list.timer_requested.connect(self._start_task_timer)
        up_card.body.addWidget(self.upcoming_list)
        bottom.addWidget(up_card, 2)

        act_card = GlassCard(self.theme)
        act_card.body.addWidget(QLabel("Recent Activity"))
        self.activity_label = QLabel()
        self.activity_label.setWordWrap(True)
        self.activity_label.setObjectName("muted")
        self.activity_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        act_card.body.addWidget(self.activity_label)
        streak_info = QLabel()
        self.streak_info = streak_info
        act_card.body.addWidget(self.streak_info)
        bottom.addWidget(act_card, 1)
        self.layout_main.addLayout(bottom)

        # Charts
        charts = QHBoxLayout()
        self.week_chart = ChartWidget(self.theme)
        self.cat_chart = ChartWidget(self.theme)
        charts.addWidget(self._wrap_chart("Weekly Progress", self.week_chart))
        charts.addWidget(self._wrap_chart("Categories", self.cat_chart))
        self.layout_main.addLayout(charts)

        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self.ctx.timers.tick.connect(lambda *_: self._refresh_timer())

    def _wrap_chart(self, title: str, chart: ChartWidget) -> QWidget:
        card = GlassCard(self.theme)
        lab = QLabel(title)
        lab.setObjectName("sectionTitle")
        card.body.addWidget(lab)
        card.body.addWidget(chart)
        return card

    def _tick_clock(self) -> None:
        from datetime import datetime

        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(format_date_long())
        self.greet_label.setText(greeting_for_hour())

    def _refresh_timer(self) -> None:
        active = self.ctx.timers.active
        task = self.ctx.active_task()
        suspended = active.suspended_kind == "task"
        if active.status == "idle" and not task and not suspended:
            self.active_timer_label.setText("Idle")
            self.active_timer_meta.setText("No timer running")
        elif task:
            if active.status in ("running", "paused") and active.kind in (
                "short_break",
                "long_break",
            ):
                rem_slice = self.ctx.timers.remaining_seconds()
            elif suspended:
                rem_slice = max(
                    0,
                    active.suspended_planned_seconds - active.suspended_elapsed_seconds,
                )
            else:
                rem_slice = self.ctx.timers.remaining_seconds()
            if active.status == "idle" and not suspended:
                rem_slice = task.pomodoro_session_seconds(self.ctx.settings.focus_minutes)
            if active.status in ("running", "paused") and active.kind in (
                "focus",
                "task",
                "custom",
            ):
                live = active.elapsed_seconds
            elif suspended:
                live = active.suspended_elapsed_seconds
            else:
                live = 0
            rem_task = task.remaining_budget_seconds(live)
            self.active_timer_label.setText(format_clock(rem_slice))
            lines = [f"{task.title} · slice {format_clock(rem_slice)}"]
            if task.has_time_budget():
                lines.append(f"Task left: {format_clock(rem_task)}")
            if suspended and active.kind in ("short_break", "long_break"):
                lines.append(f"on break · focus paused")
            else:
                lines.append(f"{active.kind} · {active.status}")
            self.active_timer_meta.setText(" · ".join(lines))
        else:
            rem = self.ctx.timers.remaining_seconds()
            self.active_timer_label.setText(format_clock(rem))
            self.active_timer_meta.setText(
                f"{active.kind} · {active.status} · elapsed {format_clock(active.elapsed_seconds)}"
            )

    def refresh(self) -> None:
        self._tick_clock()
        self.quote_label.setText(f'"{self.ctx.daily_quote()}"')
        counts = self.ctx.tasks.counts_today()
        pct = (100.0 * counts["completed"] / counts["total"]) if counts["total"] else 0.0
        self.ring.animate_to(pct)
        self.progress_detail.setText(
            f"{counts['completed']} / {counts['total']} tasks completed"
        )
        self.chip_completed.set_value(str(counts["completed"]))
        self.chip_pending.set_value(str(counts["pending"]))
        focus = self.ctx.timers.focus_totals()
        self.chip_focus.set_value(format_duration(focus["today"]))
        cur, longest = self.ctx.habits.best_streaks()
        self.chip_streak.set_value(str(cur))
        self.chip_score.set_value(str(int(self.ctx.stats.productivity_today())))
        self.streak_info.setText(f"Longest streak: {longest} days · Level {self.ctx.achievements.store.level} · XP {self.ctx.achievements.store.xp}")
        self._refresh_timer()

        focus_tasks = self.ctx.tasks.today()[:8] or self.ctx.tasks.upcoming(8)
        self.upcoming_list.set_tasks(focus_tasks)

        lines = []
        for e in self.ctx.history.recent(8):
            lines.append(f"• {e.timestamp[11:16]}  {e.summary}")
        self.activity_label.setText("\n".join(lines) or "No recent activity")

        labels, values = self.ctx.stats.series("tasks_completed", 7)
        self.week_chart.plot_bar(labels, values, "Tasks Completed")
        dist = self.ctx.stats.category_distribution(30)
        if dist:
            self.cat_chart.plot_pie(list(dist.keys()), list(dist.values()), "Time by Category")
        else:
            # fallback from task categories
            cats: dict[str, float] = {}
            for t in self.ctx.tasks.tasks:
                if t.completed:
                    cats[t.category] = cats.get(t.category, 0) + 1
            self.cat_chart.plot_pie(list(cats.keys()) or ["—"], list(cats.values()) or [1], "Tasks by Category")

    def _quick_add(self) -> None:
        text = self.quick_input.text().strip()
        if not text:
            return
        self.ctx.tasks.add(title=text)
        self.ctx.stats.record_task_created()
        self.quick_input.clear()
        self.ctx.emit_change("tasks")
        self.ctx.signals.toast.emit("Task added")

    def _toggle_task(self, task_id: str, checked: bool) -> None:
        task = self.ctx.tasks.get(task_id)
        if not task:
            return
        if checked != task.completed:
            self.ctx.tasks.toggle_complete(task_id)
            if checked:
                self.ctx.stats.record_task_completed(task.category)
                self.ctx.achievements.on_task_completed(
                    self.ctx.stats.store.lifetime_tasks_completed
                )
            self.ctx.projects.refresh_counts()
            self.ctx.emit_change("tasks")

    def _start_task_timer(self, task_id: str) -> None:
        self.ctx.start_task_focus(task_id, navigate=True)
