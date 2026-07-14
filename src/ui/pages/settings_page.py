"""Settings page — theme, pomodoro, startup, backup."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.ui.pages.base_page import BasePage
from src.utils.theme import build_stylesheet
from src.widgets.common import GlassCard, PageHeader


class SettingsPage(BasePage):
    page_id = "settings"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader("Settings", "Make FocusFlow yours.", self.theme)
        )
        card = GlassCard(self.theme)
        form = QFormLayout()

        self.accent_btn = QPushButton("Choose Accent")
        self.accent_btn.clicked.connect(self._pick_accent)
        form.addRow("Accent Color", self.accent_btn)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 18)
        self.font_size.valueChanged.connect(self._apply)
        form.addRow("Font Size", self.font_size)

        self.notifications = QCheckBox("Desktop notifications")
        self.notifications.stateChanged.connect(self._apply)
        form.addRow(self.notifications)

        self.sound = QCheckBox("Sound effects")
        self.sound.stateChanged.connect(self._apply)
        form.addRow(self.sound)

        self.startup = QCheckBox("Launch on Windows Startup")
        self.startup.stateChanged.connect(self._toggle_startup)
        form.addRow(self.startup)

        self.auto_backup = QCheckBox("Automatic daily backup")
        self.auto_backup.stateChanged.connect(self._apply)
        form.addRow(self.auto_backup)

        self.morning = QCheckBox("Morning reminder")
        self.morning.stateChanged.connect(self._apply)
        form.addRow(self.morning)

        self.evening = QCheckBox("Evening summary")
        self.evening.stateChanged.connect(self._apply)
        form.addRow(self.evening)

        self.focus_mins = QSpinBox()
        self.focus_mins.setRange(1, 120)
        self.focus_mins.valueChanged.connect(self._apply)
        form.addRow("Focus minutes", self.focus_mins)

        self.short_mins = QSpinBox()
        self.short_mins.setRange(1, 60)
        self.short_mins.valueChanged.connect(self._apply)
        form.addRow("Short break", self.short_mins)

        self.long_mins = QSpinBox()
        self.long_mins.setRange(1, 60)
        self.long_mins.valueChanged.connect(self._apply)
        form.addRow("Long break", self.long_mins)

        self.water_goal = QSpinBox()
        self.water_goal.setRange(500, 6000)
        self.water_goal.setSuffix(" ml")
        self.water_goal.valueChanged.connect(self._apply)
        form.addRow("Water goal", self.water_goal)

        card.body.addLayout(form)
        self.layout_main.addWidget(card)

        backup_card = GlassCard(self.theme)
        backup_card.body.addWidget(QLabel("Backup & Restore"))
        row = QHBoxLayout()
        now = QPushButton("Backup Now")
        now.clicked.connect(self._backup_now)
        restore = QPushButton("Restore Latest")
        restore.clicked.connect(self._restore)
        save = QPushButton("Manual Save (Ctrl+S)")
        save.setObjectName("primaryBtn")
        save.clicked.connect(lambda: self.ctx.manual_save())
        row.addWidget(now)
        row.addWidget(restore)
        row.addWidget(save)
        backup_card.body.addLayout(row)
        self.backup_info = QLabel()
        self.backup_info.setObjectName("muted")
        backup_card.body.addWidget(self.backup_info)
        self.layout_main.addWidget(backup_card)

        about = GlassCard(self.theme)
        about.body.addWidget(
            QLabel(
                f"FocusFlow v{self.ctx.version}\n"
                "Personal Productivity OS · Offline · JSON storage\n"
                "No cloud. No SQL. Your data stays on this machine."
            )
        )
        self.layout_main.addWidget(about)
        self.layout_main.addStretch()
        self._loading = False

    def refresh(self) -> None:
        self._loading = True
        s = self.ctx.settings
        self.font_size.setValue(s.font_size)
        self.notifications.setChecked(s.notifications_enabled)
        self.sound.setChecked(s.sound_enabled)
        self.startup.setChecked(s.launch_on_startup)
        self.auto_backup.setChecked(s.auto_backup)
        self.morning.setChecked(s.morning_reminder)
        self.evening.setChecked(s.evening_summary)
        self.focus_mins.setValue(s.focus_minutes)
        self.short_mins.setValue(s.short_break_minutes)
        self.long_mins.setValue(s.long_break_minutes)
        self.water_goal.setValue(s.water_goal_ml)
        self.accent_btn.setText(s.accent_color)
        backups = self.ctx.backup.list_backups()
        self.backup_info.setText(
            f"{len(backups)} backups kept (max 30). Latest: {backups[0].name if backups else 'none'}"
        )
        self._loading = False

    def _apply(self) -> None:
        if self._loading:
            return
        self.ctx.settings_svc.update(
            font_size=self.font_size.value(),
            notifications_enabled=self.notifications.isChecked(),
            sound_enabled=self.sound.isChecked(),
            auto_backup=self.auto_backup.isChecked(),
            morning_reminder=self.morning.isChecked(),
            evening_summary=self.evening.isChecked(),
            focus_minutes=self.focus_mins.value(),
            short_break_minutes=self.short_mins.value(),
            long_break_minutes=self.long_mins.value(),
            water_goal_ml=self.water_goal.value(),
        )
        self.ctx.notifications.enabled = self.notifications.isChecked()
        self.ctx.notifications.sound_enabled = self.sound.isChecked()
        # live restyle
        win = self.window()
        if win:
            win.setStyleSheet(
                build_stylesheet(self.ctx.theme, self.ctx.settings.font_size)
            )
        self.ctx.history.log("settings_changed", entity_type="settings", summary="Settings updated")

    def _pick_accent(self) -> None:
        color = QColorDialog.getColor(QColor(self.ctx.settings.accent_color), self)
        if color.isValid():
            self.ctx.settings_svc.update(accent_color=color.name())
            self.accent_btn.setText(color.name())
            win = self.window()
            if win:
                win.setStyleSheet(
                    build_stylesheet(self.ctx.theme, self.ctx.settings.font_size)
                )
            self.ctx.emit_change("settings")

    def _toggle_startup(self) -> None:
        if self._loading:
            return
        enabled = self.startup.isChecked()
        self.ctx.settings_svc.apply_startup(enabled)
        self.ctx.signals.toast.emit(
            "Startup enabled" if enabled else "Startup disabled"
        )

    def _backup_now(self) -> None:
        path = self.ctx.backup.create_backup("manual")
        self.ctx.history.log(
            "backup_created", entity_type="system", summary=f"Backup {path.name}"
        )
        self.ctx.signals.toast.emit(f"Backup saved: {path.name}")
        self.refresh()

    def _restore(self) -> None:
        backups = self.ctx.backup.list_backups()
        if not backups:
            QMessageBox.information(self, "Restore", "No backups found.")
            return
        latest = backups[0]
        if (
            QMessageBox.question(
                self,
                "Restore",
                f"Restore from {latest.name}? Current data will be overwritten.",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.ctx.backup.restore_backup(latest)
            self.ctx.history.log(
                "backup_restored",
                entity_type="system",
                summary=f"Restored {latest.name}",
            )
            QMessageBox.information(
                self, "Restore", "Restore complete. Please restart FocusFlow."
            )
