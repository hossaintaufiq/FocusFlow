"""Settings page — appearance, notifications, pomodoro, data."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.utils.config import APP_NAME, APP_VERSION
from src.utils.theme import build_stylesheet
from src.widgets.common import GlassCard, PageHeader
from src.widgets.settings_widgets import SettingRow, SettingSectionHeader


class _SpinRow(QFrame):
    """Numeric setting with label and spin box."""

    def __init__(
        self,
        theme,
        title: str,
        description: str,
        spin: QSpinBox,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingRow")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(14)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        title_l = QLabel(title)
        title_l.setStyleSheet(
            f"font-weight: 650; font-size: 10.5pt; color: {theme.text_primary}; "
            "background: transparent; border: none;"
        )
        text_col.addWidget(title_l)
        desc_l = QLabel(description)
        desc_l.setWordWrap(True)
        desc_l.setStyleSheet(
            f"color: {theme.text_muted}; font-size: 9pt; background: transparent; border: none;"
        )
        text_col.addWidget(desc_l)
        lay.addLayout(text_col, 1)

        spin.setFixedWidth(96)
        spin.setStyleSheet(
            f"QSpinBox {{ background: {theme.bg_elevated}; border: 1px solid {theme.border}; "
            f"border-radius: 8px; padding: 6px 8px; color: {theme.text_primary}; }}"
        )
        lay.addWidget(spin, 0)

        self.setStyleSheet(
            f"QFrame#settingRow {{ background: {theme.bg_tertiary}; "
            f"border: 1px solid {theme.border}; border-radius: 12px; }}"
        )


class SettingsPage(BasePage):
    page_id = "settings"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader(
                "Settings",
                "Customize appearance, focus timers, and data preferences.",
                self.theme,
            )
        )

        # — Appearance —
        appearance = GlassCard(self.theme)
        appearance.body.addWidget(SettingSectionHeader("Appearance", self.theme))
        accent_row = QFrame()
        accent_row.setObjectName("settingRow")
        accent_lay = QHBoxLayout(accent_row)
        accent_lay.setContentsMargins(14, 12, 14, 12)
        accent_text = QVBoxLayout()
        accent_title = QLabel("Accent color")
        accent_title.setStyleSheet(
            f"font-weight: 650; font-size: 10.5pt; color: {self.theme.text_primary}; "
            "background: transparent; border: none;"
        )
        accent_desc = QLabel("Primary highlight used across the app.")
        accent_desc.setStyleSheet(
            f"color: {self.theme.text_muted}; font-size: 9pt; background: transparent; border: none;"
        )
        accent_text.addWidget(accent_title)
        accent_text.addWidget(accent_desc)
        accent_lay.addLayout(accent_text, 1)
        self.accent_swatch = QFrame()
        self.accent_swatch.setFixedSize(36, 36)
        self.accent_swatch.setStyleSheet(
            f"background: {self.ctx.settings.accent_color}; border-radius: 10px; "
            f"border: 2px solid {self.theme.border_strong};"
        )
        self.accent_btn = QPushButton("Change")
        self.accent_btn.clicked.connect(self._pick_accent)
        accent_lay.addWidget(self.accent_swatch)
        accent_lay.addWidget(self.accent_btn)
        accent_row.setStyleSheet(
            f"QFrame#settingRow {{ background: {self.theme.bg_tertiary}; "
            f"border: 1px solid {self.theme.border}; border-radius: 12px; }}"
        )
        appearance.body.addWidget(accent_row)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 18)
        self.font_size.setSuffix(" pt")
        self.font_size.valueChanged.connect(self._apply)
        appearance.body.addWidget(
            _SpinRow(
                self.theme,
                "Font size",
                "Base text size for the interface.",
                self.font_size,
            )
        )
        self.layout_main.addWidget(appearance)

        # — Notifications —
        notif = GlassCard(self.theme)
        notif.body.addWidget(SettingSectionHeader("Notifications", self.theme))
        self.notifications = SettingRow(
            self.theme,
            "Desktop notifications",
            "Show system alerts for reminders and timer events.",
        )
        self.notifications.toggled.connect(lambda _: self._apply())
        notif.body.addWidget(self.notifications)

        self.sound = SettingRow(
            self.theme,
            "Sound effects",
            "Play a short sound when a Pomodoro session ends.",
        )
        self.sound.toggled.connect(lambda _: self._apply())
        notif.body.addWidget(self.sound)

        self.morning = SettingRow(
            self.theme,
            "Morning reminder",
            "Daily nudge to review today's tasks.",
        )
        self.morning.toggled.connect(lambda _: self._apply())
        notif.body.addWidget(self.morning)

        self.evening = SettingRow(
            self.theme,
            "Evening summary",
            "End-of-day recap of completed work.",
        )
        self.evening.toggled.connect(lambda _: self._apply())
        notif.body.addWidget(self.evening)
        self.layout_main.addWidget(notif)

        # — System —
        system = GlassCard(self.theme)
        system.body.addWidget(SettingSectionHeader("System", self.theme))
        self.startup = SettingRow(
            self.theme,
            "Launch on Windows startup",
            "Open FocusFlow automatically when you sign in.",
        )
        self.startup.toggled.connect(self._toggle_startup)
        system.body.addWidget(self.startup)

        self.auto_backup = SettingRow(
            self.theme,
            "Automatic daily backup",
            "Save a snapshot of your data each day.",
        )
        self.auto_backup.toggled.connect(lambda _: self._apply())
        system.body.addWidget(self.auto_backup)
        self.layout_main.addWidget(system)

        # — Pomodoro —
        pomo = GlassCard(self.theme)
        pomo.body.addWidget(SettingSectionHeader("Pomodoro", self.theme))
        self.focus_mins = QSpinBox()
        self.focus_mins.setRange(1, 120)
        self.focus_mins.setSuffix(" min")
        self.focus_mins.valueChanged.connect(self._apply)
        pomo.body.addWidget(
            _SpinRow(
                self.theme,
                "Focus session",
                "Default length for a focus block.",
                self.focus_mins,
            )
        )
        self.short_mins = QSpinBox()
        self.short_mins.setRange(1, 60)
        self.short_mins.setSuffix(" min")
        self.short_mins.valueChanged.connect(self._apply)
        pomo.body.addWidget(
            _SpinRow(
                self.theme,
                "Short break",
                "Rest between focus sessions.",
                self.short_mins,
            )
        )
        self.long_mins = QSpinBox()
        self.long_mins.setRange(1, 60)
        self.long_mins.setSuffix(" min")
        self.long_mins.valueChanged.connect(self._apply)
        pomo.body.addWidget(
            _SpinRow(
                self.theme,
                "Long break",
                "Extended break after several focus rounds.",
                self.long_mins,
            )
        )
        self.water_goal = QSpinBox()
        self.water_goal.setRange(500, 6000)
        self.water_goal.setSingleStep(250)
        self.water_goal.setSuffix(" ml")
        self.water_goal.valueChanged.connect(self._apply)
        pomo.body.addWidget(
            _SpinRow(
                self.theme,
                "Daily water goal",
                "Target intake tracked on Habits & Daily.",
                self.water_goal,
            )
        )
        self.layout_main.addWidget(pomo)

        # — Data —
        backup_card = GlassCard(self.theme)
        backup_card.body.addWidget(SettingSectionHeader("Data & backup", self.theme))
        backup_card.body.addWidget(
            QLabel(
                "Your data is stored locally as JSON. Create backups before major changes."
            )
        )
        row = QHBoxLayout()
        row.setSpacing(10)
        now = QPushButton("Backup now")
        now.clicked.connect(self._backup_now)
        restore = QPushButton("Restore backup")
        restore.clicked.connect(self._restore)
        save = QPushButton("Save now")
        save.setObjectName("primaryBtn")
        save.clicked.connect(lambda: self.ctx.manual_save())
        row.addWidget(now)
        row.addWidget(restore)
        row.addWidget(save)
        row.addStretch()
        backup_card.body.addLayout(row)
        self.backup_info = QLabel()
        self.backup_info.setObjectName("muted")
        backup_card.body.addWidget(self.backup_info)
        self.layout_main.addWidget(backup_card)

        # — About —
        about = GlassCard(self.theme)
        about.body.addWidget(SettingSectionHeader("About", self.theme))
        about.body.addWidget(
            QLabel(
                f"{APP_NAME} v{APP_VERSION}\n"
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
        self.notifications.set_checked(s.notifications_enabled)
        self.sound.set_checked(s.sound_enabled)
        self.startup.set_checked(s.launch_on_startup)
        self.auto_backup.set_checked(s.auto_backup)
        self.morning.set_checked(s.morning_reminder)
        self.evening.set_checked(s.evening_summary)
        self.focus_mins.setValue(s.focus_minutes)
        self.short_mins.setValue(s.short_break_minutes)
        self.long_mins.setValue(s.long_break_minutes)
        self.water_goal.setValue(s.water_goal_ml)
        self.accent_swatch.setStyleSheet(
            f"background: {s.accent_color}; border-radius: 10px; "
            f"border: 2px solid {self.theme.border_strong};"
        )
        backups = self.ctx.backup.list_backups()
        self.backup_info.setText(
            f"{len(backups)} backups kept (max 30). "
            f"Latest: {backups[0].name if backups else 'none'}"
        )
        self._loading = False

    def _apply(self) -> None:
        if self._loading:
            return
        self.ctx.settings_svc.update(
            font_size=self.font_size.value(),
            notifications_enabled=self.notifications.is_checked(),
            sound_enabled=self.sound.is_checked(),
            auto_backup=self.auto_backup.is_checked(),
            morning_reminder=self.morning.is_checked(),
            evening_summary=self.evening.is_checked(),
            focus_minutes=self.focus_mins.value(),
            short_break_minutes=self.short_mins.value(),
            long_break_minutes=self.long_mins.value(),
            water_goal_ml=self.water_goal.value(),
        )
        self.ctx.notifications.enabled = self.notifications.is_checked()
        self.ctx.notifications.sound_enabled = self.sound.is_checked()
        win = self.window()
        if win:
            win.setStyleSheet(
                build_stylesheet(self.ctx.theme, self.ctx.settings.font_size)
            )
        self.ctx.history.log(
            "settings_changed", entity_type="settings", summary="Settings updated"
        )

    def _pick_accent(self) -> None:
        color = QColorDialog.getColor(QColor(self.ctx.settings.accent_color), self)
        if color.isValid():
            self.ctx.settings_svc.update(accent_color=color.name())
            self.accent_swatch.setStyleSheet(
                f"background: {color.name()}; border-radius: 10px; "
                f"border: 2px solid {self.theme.border_strong};"
            )
            win = self.window()
            if win:
                win.setStyleSheet(
                    build_stylesheet(self.ctx.theme, self.ctx.settings.font_size)
                )
            self.ctx.emit_change("settings")

    def _toggle_startup(self, checked: bool) -> None:
        if self._loading:
            return
        self.ctx.settings_svc.apply_startup(checked)
        self.ctx.signals.toast.emit(
            "Startup enabled" if checked else "Startup disabled"
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
        names = [b.name for b in backups]
        from PySide6.QtWidgets import QInputDialog

        choice, ok = QInputDialog.getItem(
            self, "Restore Backup", "Choose a backup:", names, 0, False
        )
        if not ok or not choice:
            return
        target = next(b for b in backups if b.name == choice)
        if (
            QMessageBox.question(
                self,
                "Restore",
                f"Restore from {target.name}? Current data will be overwritten.",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.ctx.backup.create_backup("pre-restore")
            self.ctx.backup.restore_backup(target)
            self.ctx.reload_from_disk()
            self.ctx.history.log(
                "backup_restored",
                entity_type="system",
                summary=f"Restored {target.name}",
            )
            self.ctx.signals.toast.emit(f"Restored {target.name}")
            QMessageBox.information(
                self, "Restore", "Restore complete. Data reloaded."
            )
            self.refresh()
