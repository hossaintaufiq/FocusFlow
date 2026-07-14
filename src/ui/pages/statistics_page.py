"""Statistics page with Matplotlib charts."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout

from src.ui.pages.base_page import BasePage
from src.utils.helpers import format_duration
from src.widgets.charts import ChartWidget
from src.widgets.common import GlassCard, PageHeader, StatChip


class StatisticsPage(BasePage):
    page_id = "statistics"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader("Statistics", "Measure what matters.", self.theme)
        )
        chips = QHBoxLayout()
        self.chip_score = StatChip(self.theme, "Score")
        self.chip_focus = StatChip(self.theme, "Focus Today", accent=self.theme.info)
        self.chip_tasks = StatChip(self.theme, "Tasks Done")
        self.chip_avg = StatChip(self.theme, "Avg Focus", accent=self.theme.warning)
        self.chip_long = StatChip(self.theme, "Longest Session", accent=self.theme.success)
        for c in (self.chip_score, self.chip_focus, self.chip_tasks, self.chip_avg, self.chip_long):
            chips.addWidget(c)
        self.layout_main.addLayout(chips)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Range:"))
        self.range = QComboBox()
        self.range.addItem("Daily (7d)", 7)
        self.range.addItem("Weekly (14d)", 14)
        self.range.addItem("Monthly (30d)", 30)
        self.range.addItem("Yearly (365d)", 365)
        self.range.currentIndexChanged.connect(self.refresh)
        controls.addWidget(self.range)
        controls.addStretch()
        self.layout_main.addLayout(controls)

        row1 = QHBoxLayout()
        self.line_chart = ChartWidget(self.theme)
        self.bar_chart = ChartWidget(self.theme)
        row1.addWidget(self._card("Tasks Completed", self.line_chart))
        row1.addWidget(self._card("Focus Hours", self.bar_chart))
        self.layout_main.addLayout(row1)

        row2 = QHBoxLayout()
        self.score_chart = ChartWidget(self.theme)
        self.pie_chart = ChartWidget(self.theme)
        row2.addWidget(self._card("Productivity Score", self.score_chart))
        row2.addWidget(self._card("Category Distribution", self.pie_chart))
        self.layout_main.addLayout(row2)

        self.summary = QLabel()
        self.summary.setObjectName("muted")
        self.summary.setWordWrap(True)
        self.layout_main.addWidget(self.summary)

    def _card(self, title: str, chart: ChartWidget):
        card = GlassCard(self.theme)
        lab = QLabel(title)
        lab.setObjectName("sectionTitle")
        card.body.addWidget(lab)
        card.body.addWidget(chart)
        return card

    def refresh(self) -> None:
        days = self.range.currentData() or 7
        summary = self.ctx.stats.summary()
        self.chip_score.set_value(str(int(summary["productivity_score"])))
        self.chip_focus.set_value(format_duration(summary["focus_seconds_today"]))
        self.chip_tasks.set_value(str(summary["tasks_completed_today"]))
        self.chip_avg.set_value(format_duration(int(summary["average_focus_today"])))
        self.chip_long.set_value(format_duration(int(summary["longest_session_seconds"])))

        labels, tasks = self.ctx.stats.series("tasks_completed", days if days <= 30 else 30)
        _, focus = self.ctx.stats.series("focus_hours", days if days <= 30 else 30)
        _, scores = self.ctx.stats.series("productivity_score", days if days <= 30 else 30)

        if days >= 365:
            self.line_chart.plot_line(labels, tasks, "Year view (last 30 sample days)")
        else:
            self.line_chart.plot_line(labels, tasks)
        self.bar_chart.plot_bar(labels, focus)
        self.score_chart.plot_line(labels, scores)

        dist = self.ctx.stats.category_distribution(min(days, 90))
        if not dist:
            dist = {}
            for t in self.ctx.tasks.tasks:
                if t.completed:
                    dist[t.category] = dist.get(t.category, 0) + 1
        self.pie_chart.plot_pie(list(dist.keys()) or ["—"], list(dist.values()) or [1])

        totals = self.ctx.timers.focus_totals()
        completed = sum(1 for t in self.ctx.tasks.tasks if t.completed and not t.archived)
        total = sum(1 for t in self.ctx.tasks.tasks if not t.archived)
        rate = round(100 * completed / total, 1) if total else 0
        self.summary.setText(
            f"Completion rate: {rate}%  ·  "
            f"Lifetime focus: {format_duration(totals['lifetime'])}  ·  "
            f"Streak {summary['current_streak']} (best {summary['longest_streak']})  ·  "
            f"Level {self.ctx.achievements.store.level} / {self.ctx.achievements.store.xp} XP"
        )
