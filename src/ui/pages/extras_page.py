"""Extras hub — journal, mood, water, trackers, XP, sticky notes."""

from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, GradientBar, PageHeader, StatChip


class ExtrasPage(BasePage):
    page_id = "extras"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader("Extras", "Journal · Mood · Trackers · XP", self.theme)
        )
        tabs = QTabWidget()
        tabs.addTab(self._build_wellness(), "Wellness")
        tabs.addTab(self._build_trackers(), "Trackers")
        tabs.addTab(self._build_tools(), "Tools")
        tabs.addTab(self._build_xp(), "XP & Badges")
        self.layout_main.addWidget(tabs)

    def _build_wellness(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        mood_card = GlassCard(self.theme)
        mood_card.body.addWidget(QLabel("Mood Tracker"))
        row = QHBoxLayout()
        self.mood_slider = QSlider(Qt.Orientation.Horizontal)
        self.mood_slider.setRange(1, 5)
        self.mood_slider.setValue(3)
        save_mood = QPushButton("Save Mood")
        save_mood.setObjectName("primaryBtn")
        save_mood.clicked.connect(self._save_mood)
        row.addWidget(self.mood_slider, 1)
        row.addWidget(save_mood)
        mood_card.body.addLayout(row)
        lay.addWidget(mood_card)

        water_card = GlassCard(self.theme)
        water_card.body.addWidget(QLabel("Water Intake"))
        self.water_label = QLabel()
        self.water_bar = GradientBar(self.theme)
        water_row = QHBoxLayout()
        for ml in (250, 500):
            b = QPushButton(f"+{ml}ml")
            b.clicked.connect(lambda _, m=ml: self._add_water(m))
            water_row.addWidget(b)
        water_card.body.addWidget(self.water_label)
        water_card.body.addWidget(self.water_bar)
        water_card.body.addLayout(water_row)
        lay.addWidget(water_card)

        journal_card = GlassCard(self.theme)
        journal_card.body.addWidget(QLabel("Daily Journal"))
        self.journal_title = QLineEdit()
        self.journal_title.setPlaceholderText("Title")
        self.journal_body = QTextEdit()
        self.journal_body.setPlaceholderText("How was today?")
        self.journal_body.setFixedHeight(120)
        jbtn = QPushButton("Save Journal Entry")
        jbtn.setObjectName("primaryBtn")
        jbtn.clicked.connect(self._save_journal)
        journal_card.body.addWidget(self.journal_title)
        journal_card.body.addWidget(self.journal_body)
        journal_card.body.addWidget(jbtn)
        lay.addWidget(journal_card)

        prayer_card = GlassCard(self.theme)
        prayer_card.body.addWidget(QLabel("Prayer Checklist"))
        self.prayer_row = QHBoxLayout()
        prayer_card.body.addLayout(self.prayer_row)
        lay.addWidget(prayer_card)
        lay.addStretch()
        return w

    def _build_trackers(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        for label, slot in (
            ("+ Workout", self._add_workout),
            ("+ Reading", self._add_reading),
            ("+ Coding Hours", self._add_coding),
            ("+ LeetCode", self._add_leetcode),
            ("+ GitHub Commits", self._add_github),
            ("+ Study Hours", self._add_study),
            ("+ Finance Note", self._add_finance),
        ):
            b = QPushButton(label)
            b.clicked.connect(slot)
            lay.addWidget(b)
        self.tracker_summary = QLabel()
        self.tracker_summary.setObjectName("muted")
        self.tracker_summary.setWordWrap(True)
        lay.addWidget(self.tracker_summary)
        lay.addStretch()
        return w

    def _build_tools(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        scratch = GlassCard(self.theme)
        scratch.body.addWidget(QLabel("Quick Scratch Pad"))
        self.scratch = QTextEdit()
        self.scratch.setPlaceholderText("Brain dump… autosaves")
        self.scratch.textChanged.connect(self._save_scratch)
        scratch.body.addWidget(self.scratch)
        lay.addWidget(scratch)

        sticky = GlassCard(self.theme)
        sticky.body.addWidget(QLabel("Sticky Notes"))
        add_sticky = QPushButton("+ Sticky")
        add_sticky.clicked.connect(self._add_sticky)
        sticky.body.addWidget(add_sticky)
        self.sticky_host = QVBoxLayout()
        sticky.body.addLayout(self.sticky_host)
        lay.addWidget(sticky)

        cd = GlassCard(self.theme)
        cd.body.addWidget(QLabel("Countdowns"))
        add_cd = QPushButton("+ Countdown")
        add_cd.clicked.connect(self._add_countdown)
        cd.body.addWidget(add_cd)
        self.cd_label = QLabel()
        self.cd_label.setObjectName("muted")
        cd.body.addWidget(self.cd_label)
        lay.addWidget(cd)
        lay.addStretch()
        return w

    def _build_xp(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self.xp_chip = StatChip(self.theme, "Level")
        self.xp_bar = GradientBar(self.theme)
        self.xp_meta = QLabel()
        self.badges_label = QLabel()
        self.badges_label.setWordWrap(True)
        self.badges_label.setObjectName("muted")
        lay.addWidget(self.xp_chip)
        lay.addWidget(self.xp_bar)
        lay.addWidget(self.xp_meta)
        lay.addWidget(QLabel("Badges & Achievements"))
        lay.addWidget(self.badges_label)
        lay.addStretch()
        return w

    def refresh(self) -> None:
        goal = self.ctx.settings.water_goal_ml
        water = self.ctx.extras.water_today(goal)
        pct = min(100.0, 100.0 * water.ml / max(1, water.goal_ml))
        self.water_label.setText(f"{water.ml} / {water.goal_ml} ml")
        self.water_bar.set_value(pct)

        # prayer buttons
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

        self.scratch.blockSignals(True)
        self.scratch.setPlainText(self.ctx.extras.data.scratchpad)
        self.scratch.blockSignals(False)

        while self.sticky_host.count():
            item = self.sticky_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for note in self.ctx.extras.data.sticky_notes:
            row = QHBoxLayout()
            lab = QLabel(note.content[:80] or "(empty)")
            lab.setStyleSheet(
                f"background: {note.color}; color: #0B1220; padding: 8px; border-radius: 8px;"
            )
            del_b = QPushButton("×")
            del_b.clicked.connect(lambda _, i=note.id: self._del_sticky(i))
            holder = QWidget()
            row.addWidget(lab, 1)
            row.addWidget(del_b)
            holder.setLayout(row)
            self.sticky_host.addWidget(holder)

        lines = []
        for c in self.ctx.extras.data.countdowns:
            try:
                target = date.fromisoformat(c.target_date[:10])
                days = (target - date.today()).days
                lines.append(f"• {c.title}: {days} days ({c.target_date[:10]})")
            except ValueError:
                lines.append(f"• {c.title}: {c.target_date}")
        self.cd_label.setText("\n".join(lines) or "No countdowns")

        d = self.ctx.extras.data
        self.tracker_summary.setText(
            f"Workouts {len(d.workout)} · Reading {len(d.reading)} · Coding {len(d.coding)} · "
            f"LeetCode {len(d.leetcode)} · GitHub {len(d.github)} · Study {len(d.study)} · "
            f"Finance {len(d.finance)}"
        )

        store = self.ctx.achievements.store
        from src.models.achievements import xp_for_next_level

        floor, nxt = xp_for_next_level(store.xp)
        span = max(1, nxt - floor)
        self.xp_chip.set_value(str(store.level))
        self.xp_bar.set_value(100.0 * (store.xp - floor) / span)
        self.xp_meta.setText(f"{store.xp} XP  ·  next level at {nxt} XP")
        badge_lines = []
        for bid in store.badges:
            meta = self.ctx.achievements.badge_meta(bid)
            badge_lines.append(f"🏅 {meta['name']} — {meta['description']}")
        self.badges_label.setText("\n".join(badge_lines) or "Complete tasks and habits to unlock badges.")

    def _save_mood(self) -> None:
        self.ctx.extras.set_mood(self.mood_slider.value())
        self.ctx.signals.toast.emit("Mood saved")
        self.ctx.emit_change("extras")

    def _add_water(self, ml: int) -> None:
        self.ctx.extras.add_water(ml, self.ctx.settings.water_goal_ml)
        self.ctx.emit_change("extras")

    def _save_journal(self) -> None:
        self.ctx.extras.add_journal(
            self.journal_title.text().strip() or "Journal",
            self.journal_body.toPlainText(),
            self.mood_slider.value(),
        )
        self.journal_title.clear()
        self.journal_body.clear()
        self.ctx.signals.toast.emit("Journal saved")
        self.ctx.emit_change("extras")

    def _toggle_prayer(self, key: str) -> None:
        self.ctx.extras.toggle_prayer(key)
        self.ctx.emit_change("extras")

    def _save_scratch(self) -> None:
        self.ctx.extras.set_scratchpad(self.scratch.toPlainText())

    def _add_sticky(self) -> None:
        text, ok = QInputDialog.getText(self, "Sticky", "Note:")
        if ok and text.strip():
            self.ctx.extras.add_sticky(text.strip())
            self.ctx.emit_change("extras")

    def _del_sticky(self, note_id: str) -> None:
        self.ctx.extras.delete_sticky(note_id)
        self.ctx.emit_change("extras")

    def _add_countdown(self) -> None:
        title, ok = QInputDialog.getText(self, "Countdown", "Title:")
        if not ok or not title.strip():
            return
        target, ok2 = QInputDialog.getText(
            self, "Countdown", "Target date (YYYY-MM-DD):", text=date.today().isoformat()
        )
        if ok2 and target.strip():
            self.ctx.extras.add_countdown(title.strip(), target.strip())
            self.ctx.emit_change("extras")

    def _prompt_title(self, label: str) -> str | None:
        text, ok = QInputDialog.getText(self, label, "Name / title:")
        return text.strip() if ok and text.strip() else None

    def _add_workout(self) -> None:
        name = self._prompt_title("Workout")
        if name:
            self.ctx.extras.add_workout(activity=name, duration_minutes=30)
            self.ctx.emit_change("extras")

    def _add_reading(self) -> None:
        name = self._prompt_title("Book")
        if name:
            self.ctx.extras.add_reading(title=name, pages=10, minutes=20)
            self.ctx.emit_change("extras")

    def _add_coding(self) -> None:
        name = self._prompt_title("Project")
        if name:
            self.ctx.extras.add_coding(project=name, hours=1.0)
            self.ctx.emit_change("extras")

    def _add_leetcode(self) -> None:
        name = self._prompt_title("Problem")
        if name:
            self.ctx.extras.add_leetcode(problem=name)
            self.ctx.emit_change("extras")

    def _add_github(self) -> None:
        name = self._prompt_title("Repo")
        if name:
            self.ctx.extras.add_github(repo=name, commits=1)
            self.ctx.emit_change("extras")

    def _add_study(self) -> None:
        name = self._prompt_title("Subject")
        if name:
            self.ctx.extras.add_study(subject=name, hours=1.0)
            self.ctx.emit_change("extras")

    def _add_finance(self) -> None:
        name = self._prompt_title("Finance note")
        if name:
            self.ctx.extras.add_finance(title=name, amount=0.0)
            self.ctx.emit_change("extras")
