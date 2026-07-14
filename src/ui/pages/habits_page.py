"""Habits page with streak and heatmap."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, PageHeader


class HabitsPage(BasePage):
    page_id = "habits"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader("Habits", "Build streaks. Consistency compounds.", self.theme)
        )
        bar = QHBoxLayout()
        add = QPushButton("+ New Habit")
        add.setObjectName("primaryBtn")
        add.clicked.connect(self._add)
        bar.addWidget(add)
        self.rate_label = QLabel()
        self.rate_label.setObjectName("accent")
        bar.addStretch()
        bar.addWidget(self.rate_label)
        self.layout_main.addLayout(bar)

        self.list_host = QVBoxLayout()
        self.layout_main.addLayout(self.list_host)

        heat_card = GlassCard(self.theme)
        heat_card.body.addWidget(QLabel("Completion Heatmap (12 weeks)"))
        self.heat_grid = QGridLayout()
        heat_card.body.addLayout(self.heat_grid)
        self.layout_main.addWidget(heat_card)
        self.layout_main.addStretch()

    def refresh(self) -> None:
        while self.list_host.count():
            item = self.list_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        rate = self.ctx.habits.today_completion_rate()
        cur, longest = self.ctx.habits.best_streaks()
        self.rate_label.setText(
            f"Today {rate}% · streak {cur} · best {longest}"
        )
        for habit in self.ctx.habits.habits:
            card = GlassCard(self.theme)
            row = QHBoxLayout()
            done = habit.is_completed_on()
            toggle = QPushButton("✓ Done" if done else "Mark done")
            toggle.setObjectName("primaryBtn" if not done else "ghostBtn")
            toggle.clicked.connect(lambda _, h=habit.id: self._toggle(h))
            col = QVBoxLayout()
            name = QLabel(habit.name)
            name.setStyleSheet("font-weight: 700; border: none;")
            meta = QLabel(
                f"{habit.frequency} · streak {habit.current_streak} · "
                f"best {habit.longest_streak} · {habit.completion_rate}% lifetime"
            )
            meta.setObjectName("muted")
            col.addWidget(name)
            col.addWidget(meta)
            row.addLayout(col, 1)
            row.addWidget(toggle)
            delete = QPushButton("Delete")
            delete.setObjectName("dangerBtn")
            delete.clicked.connect(lambda _, h=habit.id: self._delete(h))
            row.addWidget(delete)
            card.body.addLayout(row)
            self.list_host.addWidget(card)

        # heatmap
        while self.heat_grid.count():
            item = self.heat_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        data = self.ctx.habits.heatmap_data(84)
        dates = sorted(data.keys())
        for i, day in enumerate(dates):
            count = data[day]
            cell = QLabel()
            cell.setFixedSize(12, 12)
            intensity = min(1.0, count / max(1, len(self.ctx.habits.habits)))
            alpha = int(40 + intensity * 200)
            cell.setStyleSheet(
                f"background: rgba(45, 212, 191, {alpha / 255:.2f}); border-radius: 2px;"
            )
            cell.setToolTip(f"{day}: {count}")
            self.heat_grid.addWidget(cell, i // 14, i % 14)

    def _sync_habit_stats(self) -> None:
        cur, longest = self.ctx.habits.best_streaks()
        self.ctx.stats.record_habit(
            sum(1 for h in self.ctx.habits.habits if h.is_completed_on()),
            len(self.ctx.habits.habits),
        )
        self.ctx.stats.update_streaks(cur, longest)

    def _add(self) -> None:
        name, ok = QInputDialog.getText(self, "New Habit", "Habit name:")
        if not ok or not name.strip():
            return
        freq, ok2 = QInputDialog.getItem(
            self, "Frequency", "Frequency:", ["daily", "weekly", "monthly"], 0, False
        )
        if ok2:
            self.ctx.habits.add(name=name.strip(), frequency=freq)
            self.ctx.emit_change("habits")

    def _toggle(self, habit_id: str) -> None:
        habit = self.ctx.habits.toggle_today(habit_id)
        if habit and habit.is_completed_on():
            self.ctx.achievements.on_habit_completed()
            cur, _ = self.ctx.habits.best_streaks()
            self.ctx.achievements.on_streak(cur)
        self._sync_habit_stats()
        self.ctx.emit_change("habits")

    def _delete(self, habit_id: str) -> None:
        if QMessageBox.question(self, "Delete", "Delete habit?") == QMessageBox.StandardButton.Yes:
            self.ctx.habits.delete(habit_id)
            self._sync_habit_stats()
            self.ctx.emit_change("habits")
