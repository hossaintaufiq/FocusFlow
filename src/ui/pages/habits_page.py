"""Habits + daily extras tracking (wellness, activities, XP)."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.models.achievements import xp_for_next_level
from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, GradientBar, PageHeader, StatChip


class HabitsPage(BasePage):
    page_id = "habits"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader(
                "Habits & Daily Tracking",
                "Custom habits, wellness, and daily activity logs in one place.",
                self.theme,
            )
        )

        # Daily overview chips
        chips = QHBoxLayout()
        self.chip_habits = StatChip(self.theme, "Habits today")
        self.chip_wellness = StatChip(self.theme, "Wellness", accent=self.theme.info)
        self.chip_activity = StatChip(self.theme, "Activities", accent=self.theme.warning)
        self.chip_water = StatChip(self.theme, "Water", accent=self.theme.success)
        self.chip_xp = StatChip(self.theme, "Level", accent=self.theme.accent)
        for c in (
            self.chip_habits,
            self.chip_wellness,
            self.chip_activity,
            self.chip_water,
            self.chip_xp,
        ):
            chips.addWidget(c)
        self.layout_main.addLayout(chips)

        bar = QHBoxLayout()
        add = QPushButton("+ New Habit")
        add.setObjectName("primaryBtn")
        add.clicked.connect(self._add_habit)
        self.rate_label = QLabel()
        self.rate_label.setObjectName("accent")
        bar.addWidget(add)
        bar.addStretch()
        bar.addWidget(self.rate_label)
        self.layout_main.addLayout(bar)

        # --- Custom habits ---
        habits_card = GlassCard(self.theme)
        habits_card.body.addWidget(QLabel("Custom habits"))
        self.habits_host = QVBoxLayout()
        habits_card.body.addLayout(self.habits_host)
        self.layout_main.addWidget(habits_card)

        # --- Wellness today ---
        wellness = GlassCard(self.theme)
        wellness.body.addWidget(QLabel("Wellness today"))
        wgrid = QGridLayout()

        # Mood
        mood_box = QVBoxLayout()
        mood_box.addWidget(QLabel("Mood (1-5)"))
        mood_row = QHBoxLayout()
        self.mood_slider = QSlider(Qt.Orientation.Horizontal)
        self.mood_slider.setRange(1, 5)
        self.mood_slider.setValue(3)
        self.mood_value = QLabel("3")
        self.mood_slider.valueChanged.connect(lambda v: self.mood_value.setText(str(v)))
        save_mood = QPushButton("Save")
        save_mood.clicked.connect(self._save_mood)
        mood_row.addWidget(self.mood_slider, 1)
        mood_row.addWidget(self.mood_value)
        mood_row.addWidget(save_mood)
        mood_box.addLayout(mood_row)
        self.mood_status = QLabel()
        self.mood_status.setObjectName("muted")
        mood_box.addWidget(self.mood_status)
        wgrid.addLayout(mood_box, 0, 0)

        # Water
        water_box = QVBoxLayout()
        water_box.addWidget(QLabel("Water intake"))
        self.water_label = QLabel()
        self.water_bar = GradientBar(self.theme)
        water_btns = QHBoxLayout()
        for ml in (250, 500, 750):
            b = QPushButton(f"+{ml}ml")
            b.clicked.connect(lambda _, m=ml: self._add_water(m))
            water_btns.addWidget(b)
        water_box.addWidget(self.water_label)
        water_box.addWidget(self.water_bar)
        water_box.addLayout(water_btns)
        wgrid.addLayout(water_box, 0, 1)

        # Journal
        journal_box = QVBoxLayout()
        journal_box.addWidget(QLabel("Daily journal"))
        self.journal_title = QLineEdit()
        self.journal_title.setPlaceholderText("Title")
        self.journal_body = QTextEdit()
        self.journal_body.setPlaceholderText("How was today?")
        self.journal_body.setFixedHeight(72)
        jbtn = QPushButton("Save journal")
        jbtn.setObjectName("primaryBtn")
        jbtn.clicked.connect(self._save_journal)
        self.journal_status = QLabel()
        self.journal_status.setObjectName("muted")
        journal_box.addWidget(self.journal_title)
        journal_box.addWidget(self.journal_body)
        journal_box.addWidget(jbtn)
        journal_box.addWidget(self.journal_status)
        wgrid.addLayout(journal_box, 1, 0)

        # Prayer
        prayer_box = QVBoxLayout()
        prayer_box.addWidget(QLabel("Prayer checklist"))
        self.prayer_row = QHBoxLayout()
        self.prayer_status = QLabel()
        self.prayer_status.setObjectName("muted")
        prayer_box.addLayout(self.prayer_row)
        prayer_box.addWidget(self.prayer_status)
        wgrid.addLayout(prayer_box, 1, 1)

        wellness.body.addLayout(wgrid)
        self.layout_main.addWidget(wellness)

        # --- Daily activity trackers ---
        act_card = GlassCard(self.theme)
        act_card.body.addWidget(QLabel("Activities today — log what you did today"))
        self.trackers_host = QVBoxLayout()
        act_card.body.addLayout(self.trackers_host)
        self.layout_main.addWidget(act_card)

        # Scratch + XP
        bottom = QHBoxLayout()
        scratch_card = GlassCard(self.theme)
        scratch_card.body.addWidget(QLabel("Scratch pad"))
        self.scratch = QTextEdit()
        self.scratch.setPlaceholderText("Quick notes… autosaves")
        self.scratch.setFixedHeight(80)
        self.scratch.textChanged.connect(self._save_scratch)
        scratch_card.body.addWidget(self.scratch)
        bottom.addWidget(scratch_card, 2)

        xp_card = GlassCard(self.theme)
        xp_card.body.addWidget(QLabel("XP progress"))
        self.xp_bar = GradientBar(self.theme)
        self.xp_meta = QLabel()
        self.xp_meta.setObjectName("muted")
        xp_card.body.addWidget(self.xp_bar)
        xp_card.body.addWidget(self.xp_meta)
        bottom.addWidget(xp_card, 1)
        self.layout_main.addLayout(bottom)

        heat_card = GlassCard(self.theme)
        heat_card.body.addWidget(QLabel("Habit heatmap (12 weeks)"))
        self.heat_grid = QGridLayout()
        heat_card.body.addLayout(self.heat_grid)
        self.layout_main.addWidget(heat_card)
        self.layout_main.addStretch()

        self._tracker_defs = (
            ("workout", "Workout", self._log_workout, "Activity name"),
            ("reading", "Reading", self._log_reading, "Book / article"),
            ("coding", "Coding", self._log_coding, "Project"),
            ("leetcode", "LeetCode", self._log_leetcode, "Problem"),
            ("github", "GitHub", self._log_github, "Repo"),
            ("study", "Study", self._log_study, "Subject"),
            ("finance", "Finance", self._log_finance, "Note title"),
        )

    def refresh(self) -> None:
        goal = self.ctx.settings.water_goal_ml
        summary = self.ctx.extras.daily_summary(goal)
        habit_rate = self.ctx.habits.today_completion_rate()
        cur, longest = self.ctx.habits.best_streaks()
        self.rate_label.setText(f"Today {habit_rate}% · streak {cur} · best {longest}")

        habits_done = sum(1 for h in self.ctx.habits.habits if h.is_completed_on())
        habits_total = len(self.ctx.habits.habits)
        self.chip_habits.set_value(f"{habits_done}/{habits_total}")
        self.chip_wellness.set_value(
            f"{summary['wellness_points']}/{summary['wellness_max']}"
        )
        self.chip_activity.set_value(str(summary["activity_total"]))
        self.chip_water.set_value(f"{summary['water_ml']}ml")

        store = self.ctx.achievements.store
        self.chip_xp.set_value(str(store.level))

        # Habits list
        while self.habits_host.count():
            item = self.habits_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for habit in self.ctx.habits.habits:
            row = QHBoxLayout()
            done = habit.is_completed_on()
            toggle = QPushButton("Done" if not done else "Undo")
            toggle.setObjectName("primaryBtn" if not done else "ghostBtn")
            toggle.clicked.connect(lambda _, h=habit.id: self._toggle_habit(h))
            col = QVBoxLayout()
            name = QLabel(habit.name)
            name.setStyleSheet("font-weight: 700; border: none;")
            meta = QLabel(
                f"{habit.frequency} · streak {habit.current_streak} · "
                f"best {habit.longest_streak}"
            )
            meta.setObjectName("muted")
            col.addWidget(name)
            col.addWidget(meta)
            row.addLayout(col, 1)
            row.addWidget(toggle)
            delete = QPushButton("Delete")
            delete.setObjectName("dangerBtn")
            delete.clicked.connect(lambda _, h=habit.id: self._delete_habit(h))
            row.addWidget(delete)
            wrap = QWidget()
            wrap.setLayout(row)
            self.habits_host.addWidget(wrap)
        if not self.ctx.habits.habits:
            self.habits_host.addWidget(QLabel("No habits yet — add your first daily habit."))

        # Wellness
        mood = self.ctx.extras.mood_today()
        if mood:
            self.mood_slider.blockSignals(True)
            self.mood_slider.setValue(mood.score)
            self.mood_value.setText(str(mood.score))
            self.mood_slider.blockSignals(False)
            self.mood_status.setText(f"Logged today: {mood.score}/5")
        else:
            self.mood_status.setText("Not logged today")

        water = self.ctx.extras.water_today(goal)
        pct = min(100.0, 100.0 * water.ml / max(1, water.goal_ml))
        self.water_label.setText(f"{water.ml} / {water.goal_ml} ml")
        self.water_bar.set_value(pct)

        journals = self.ctx.extras.journal_today()
        self.journal_status.setText(
            f"{len(journals)} journal entr{'y' if len(journals) == 1 else 'ies'} today"
        )

        while self.prayer_row.count():
            item = self.prayer_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        prayer = self.ctx.extras.prayer_today()
        for key, done in prayer.items.items():
            b = QPushButton(("✓ " if done else "") + key.title())
            if done:
                b.setObjectName("primaryBtn")
            b.clicked.connect(lambda _, k=key: self._toggle_prayer(k))
            self.prayer_row.addWidget(b)
        self.prayer_status.setText(
            f"{summary['prayer_done']}/{summary['prayer_total']} prayers checked"
        )

        # Activity trackers
        while self.trackers_host.count():
            item = self.trackers_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for key, label, log_fn, prompt in self._tracker_defs:
            count = summary["trackers"][key]  # type: ignore[index]
            row = QHBoxLayout()
            info = QVBoxLayout()
            title = QLabel(label)
            title.setStyleSheet("font-weight: 600; border: none;")
            sub = QLabel(self._tracker_detail(key, count))
            sub.setObjectName("muted")
            info.addWidget(title)
            info.addWidget(sub)
            log_btn = QPushButton("+ Log today")
            log_btn.clicked.connect(log_fn)
            row.addLayout(info, 1)
            row.addWidget(log_btn)
            wrap = QWidget()
            wrap.setLayout(row)
            self.trackers_host.addWidget(wrap)

        self.scratch.blockSignals(True)
        self.scratch.setPlainText(self.ctx.extras.data.scratchpad)
        self.scratch.blockSignals(False)

        floor, nxt = xp_for_next_level(store.xp)
        span = max(1, nxt - floor)
        self.xp_bar.set_value(100.0 * (store.xp - floor) / span)
        self.xp_meta.setText(f"{store.xp} XP · next level at {nxt} XP")

        # Heatmap
        while self.heat_grid.count():
            item = self.heat_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        data = self.ctx.habits.heatmap_data(84)
        for i, day in enumerate(sorted(data.keys())):
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

    def _tracker_detail(self, key: str, count: int) -> str:
        today = date.today().isoformat()
        if count == 0:
            return f"Today ({today}): nothing logged yet"
        entries = {
            "workout": self.ctx.extras.workouts_today(),
            "reading": self.ctx.extras.reading_today(),
            "coding": self.ctx.extras.coding_today(),
            "leetcode": self.ctx.extras.leetcode_today(),
            "github": self.ctx.extras.github_today(),
            "study": self.ctx.extras.study_today(),
            "finance": self.ctx.extras.finance_today(),
        }.get(key, [])
        if not entries:
            return f"Today: {count} logged"
        first = entries[0]
        if key == "workout":
            return f"Today: {count} · latest {getattr(first, 'activity', '')}"
        if key == "reading":
            return f"Today: {count} · latest {getattr(first, 'title', '')}"
        if key == "coding":
            return f"Today: {count} · {getattr(first, 'hours', 0)}h on {getattr(first, 'project', '')}"
        if key == "leetcode":
            return f"Today: {count} · {getattr(first, 'problem', '')}"
        if key == "github":
            return f"Today: {count} · {getattr(first, 'commits', 0)} commits"
        if key == "study":
            return f"Today: {count} · {getattr(first, 'hours', 0)}h {getattr(first, 'subject', '')}"
        if key == "finance":
            return f"Today: {count} · {getattr(first, 'title', '')}"
        return f"Today: {count} logged"

    def _sync_habit_stats(self) -> None:
        cur, longest = self.ctx.habits.best_streaks()
        self.ctx.stats.record_habit(
            sum(1 for h in self.ctx.habits.habits if h.is_completed_on()),
            len(self.ctx.habits.habits),
        )
        self.ctx.stats.update_streaks(cur, longest)

    def _emit(self) -> None:
        self.ctx.emit_change("habits")
        self.ctx.emit_change("extras")

    def _add_habit(self) -> None:
        name, ok = QInputDialog.getText(self, "New Habit", "Habit name:")
        if not ok or not name.strip():
            return
        freq, ok2 = QInputDialog.getItem(
            self, "Frequency", "Frequency:", ["daily", "weekly", "monthly"], 0, False
        )
        if ok2:
            self.ctx.habits.add(name=name.strip(), frequency=freq)
            self._emit()

    def _toggle_habit(self, habit_id: str) -> None:
        habit = self.ctx.habits.toggle_today(habit_id)
        if habit and habit.is_completed_on():
            self.ctx.achievements.on_habit_completed()
            cur, _ = self.ctx.habits.best_streaks()
            self.ctx.achievements.on_streak(cur)
        self._sync_habit_stats()
        self._emit()

    def _delete_habit(self, habit_id: str) -> None:
        if QMessageBox.question(self, "Delete", "Delete habit?") == QMessageBox.StandardButton.Yes:
            self.ctx.habits.delete(habit_id)
            self._sync_habit_stats()
            self._emit()

    def _save_mood(self) -> None:
        self.ctx.extras.set_mood(self.mood_slider.value())
        self.ctx.signals.toast.emit("Mood saved for today")
        self._emit()

    def _add_water(self, ml: int) -> None:
        self.ctx.extras.add_water(ml, self.ctx.settings.water_goal_ml)
        self._emit()

    def _save_journal(self) -> None:
        body = self.journal_body.toPlainText().strip()
        if not body:
            return
        self.ctx.extras.add_journal(
            self.journal_title.text().strip() or "Journal",
            body,
            self.mood_slider.value(),
        )
        self.journal_title.clear()
        self.journal_body.clear()
        self.ctx.signals.toast.emit("Journal saved for today")
        self._emit()

    def _toggle_prayer(self, key: str) -> None:
        self.ctx.extras.toggle_prayer(key)
        self._emit()

    def _save_scratch(self) -> None:
        self.ctx.extras.set_scratchpad(self.scratch.toPlainText())

    def _prompt(self, title: str, label: str) -> str | None:
        text, ok = QInputDialog.getText(self, title, label)
        return text.strip() if ok and text.strip() else None

    def _log_workout(self) -> None:
        name = self._prompt("Workout", "Activity:")
        if name:
            mins, ok = QInputDialog.getInt(self, "Workout", "Minutes:", 30, 1, 600)
            if ok:
                self.ctx.extras.add_workout(activity=name, duration_minutes=mins)
                self._emit()

    def _log_reading(self) -> None:
        title = self._prompt("Reading", "Title:")
        if title:
            pages, ok = QInputDialog.getInt(self, "Reading", "Pages:", 10, 0, 9999)
            if ok:
                self.ctx.extras.add_reading(title=title, pages=pages, minutes=20)
                self._emit()

    def _log_coding(self) -> None:
        project = self._prompt("Coding", "Project:")
        if project:
            hours, ok = QInputDialog.getDouble(self, "Coding", "Hours:", 1.0, 0.25, 24, 2)
            if ok:
                self.ctx.extras.add_coding(project=project, hours=hours)
                self._emit()

    def _log_leetcode(self) -> None:
        problem = self._prompt("LeetCode", "Problem:")
        if problem:
            self.ctx.extras.add_leetcode(problem=problem)
            self._emit()

    def _log_github(self) -> None:
        repo = self._prompt("GitHub", "Repo:")
        if repo:
            commits, ok = QInputDialog.getInt(self, "GitHub", "Commits today:", 1, 0, 999)
            if ok:
                self.ctx.extras.add_github(repo=repo, commits=commits)
                self._emit()

    def _log_study(self) -> None:
        subject = self._prompt("Study", "Subject:")
        if subject:
            hours, ok = QInputDialog.getDouble(self, "Study", "Hours:", 1.0, 0.25, 24, 2)
            if ok:
                self.ctx.extras.add_study(subject=subject, hours=hours)
                self._emit()

    def _log_finance(self) -> None:
        title = self._prompt("Finance", "Title:")
        if title:
            amount, ok = QInputDialog.getDouble(self, "Finance", "Amount:", 0.0, -999999, 999999, 2)
            if ok:
                self.ctx.extras.add_finance(title=title, amount=amount)
                self._emit()
