"""
Main application window — sidebar navigation, stacked pages, shortcuts.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.app_context import AppContext
from src.ui.pages.calendar_page import CalendarPage
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.pages.habits_page import HabitsPage
from src.ui.pages.history_page import HistoryPage
from src.ui.pages.notes_page import NotesPage
from src.ui.pages.pomodoro_page import PomodoroPage
from src.ui.pages.projects_page import ProjectsPage
from src.ui.pages.settings_page import SettingsPage
from src.ui.pages.statistics_page import StatisticsPage
from src.ui.pages.today_page import TodayPage
from src.utils.config import (
    APP_NAME,
    APP_TAGLINE,
    NAV_ICONS,
    NAV_LABELS,
    NAV_PAGES,
    NAV_SECTIONS,
    SIDEBAR_WIDTH,
)
from src.utils.paths import APP_ICON
from src.utils.theme import build_stylesheet
from src.widgets.common import SidebarButton, SidebarSectionLabel

logger = logging.getLogger("FocusFlow.ui")


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.ctx = context
        self.setWindowTitle(f"{APP_NAME} — {APP_TAGLINE}")
        self.resize(1400, 860)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(
            build_stylesheet(context.theme, context.settings.font_size)
        )
        if APP_ICON.exists():
            self.setWindowIcon(QIcon(str(APP_ICON)))

        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH)
        side_lay = QVBoxLayout(self.sidebar)
        side_lay.setContentsMargins(12, 20, 12, 16)
        side_lay.setSpacing(2)

        brand = QLabel(APP_NAME)
        brand.setStyleSheet(
            f"font-size: 18pt; font-weight: 800; color: {context.theme.accent}; "
            "letter-spacing: 0.5px; border: none; background: transparent; padding-left: 8px;"
        )
        tag = QLabel(APP_TAGLINE)
        tag.setStyleSheet(
            f"color: {context.theme.text_muted}; font-size: 8pt; border: none; "
            "background: transparent; padding-left: 8px;"
        )
        side_lay.addWidget(brand)
        side_lay.addWidget(tag)
        side_lay.addSpacing(16)

        self._nav_buttons: dict[str, SidebarButton] = {}
        for section_title, page_ids in NAV_SECTIONS:
            side_lay.addWidget(SidebarSectionLabel(section_title, context.theme))
            for page_id in page_ids:
                btn = SidebarButton(
                    page_id,
                    NAV_LABELS[page_id],
                    NAV_ICONS[page_id],
                    context.theme,
                )
                btn.clicked.connect(lambda p=page_id: self.navigate(p))
                side_lay.addWidget(btn)
                self._nav_buttons[page_id] = btn
        side_lay.addStretch(1)

        self.xp_card = QFrame()
        self.xp_card.setObjectName("xpCard")
        xp_lay = QVBoxLayout(self.xp_card)
        xp_lay.setContentsMargins(14, 12, 14, 12)
        xp_lay.setSpacing(4)
        self.level_label = QLabel()
        self.level_label.setStyleSheet(
            f"color: {context.theme.text_primary}; font-weight: 700; font-size: 10pt; "
            "border: none; background: transparent;"
        )
        self.xp_detail = QLabel()
        self.xp_detail.setStyleSheet(
            f"color: {context.theme.text_muted}; font-size: 8.5pt; "
            "border: none; background: transparent;"
        )
        xp_lay.addWidget(self.level_label)
        xp_lay.addWidget(self.xp_detail)
        self.xp_card.setStyleSheet(
            f"QFrame#xpCard {{ background: {context.theme.bg_tertiary}; "
            f"border: 1px solid {context.theme.border}; border-radius: 12px; }}"
        )
        side_lay.addWidget(self.xp_card)
        shell.addWidget(self.sidebar)

        # Content
        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)

        self.stack = QStackedWidget()
        content_lay.addWidget(self.stack, 1)

        self.toast = QLabel("")
        self.toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast.setFixedHeight(0)
        self.toast.setStyleSheet(
            f"background: {context.theme.accent}; color: #0B1220; font-weight: 600; "
            "border-radius: 0px;"
        )
        content_lay.addWidget(self.toast)
        shell.addWidget(content, 1)

        # Register pages
        self._pages: dict[str, QWidget] = {}
        page_classes = [
            DashboardPage,
            TodayPage,
            ProjectsPage,
            HabitsPage,
            CalendarPage,
            PomodoroPage,
            NotesPage,
            StatisticsPage,
            HistoryPage,
            SettingsPage,
        ]
        for cls in page_classes:
            page = cls(context)
            self._pages[cls.page_id] = page
            self.stack.addWidget(page)

        self.ctx.signals.navigate.connect(self.navigate)
        self.ctx.signals.toast.connect(self.show_toast)
        self.ctx.signals.data_changed.connect(self._on_data)
        self._setup_shortcuts()
        self.navigate("dashboard")
        self._refresh_level()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._shortcut_new_task)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._shortcut_search)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.ctx.manual_save)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, activated=self._shortcut_delete)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self._shortcut_timer)

        for i, (page_id, _, _) in enumerate(NAV_PAGES[:9], start=1):
            QShortcut(
                QKeySequence(f"Ctrl+{i}"),
                self,
                activated=lambda p=page_id: self.navigate(p),
            )

    def navigate(self, page_id: str) -> None:
        page = self._pages.get(page_id)
        if not page:
            return
        self.stack.setCurrentWidget(page)
        for pid, btn in self._nav_buttons.items():
            btn.set_active(pid == page_id)
        if hasattr(page, "on_show"):
            page.on_show()

    def show_toast(self, message: str) -> None:
        self.toast.setText(message)
        self.toast.setFixedHeight(36)
        QTimer.singleShot(2200, lambda: self.toast.setFixedHeight(0))

    def _on_data(self, kind: str) -> None:
        self._refresh_level()
        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    def _refresh_level(self) -> None:
        store = self.ctx.achievements.store
        self.level_label.setText(f"Level {store.level}")
        self.xp_detail.setText(f"{store.xp:,} XP earned")

    def _shortcut_new_task(self) -> None:
        self.navigate("today")
        page = self._pages.get("today")
        if page and hasattr(page, "new_task"):
            page.new_task()

    def _shortcut_search(self) -> None:
        self.navigate("today")
        page = self._pages.get("today")
        if page and hasattr(page, "search"):
            page.search.setFocus()
            page.search.selectAll()

    def _shortcut_delete(self) -> None:
        page = self.stack.currentWidget()
        if page and hasattr(page, "_delete"):
            page._delete()

    def _shortcut_timer(self) -> None:
        focus = self.focusWidget()
        if focus is not None:
            from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QTextEdit

            if isinstance(focus, (QLineEdit, QTextEdit, QPlainTextEdit)):
                return
        self.ctx.timers.toggle()
        self.ctx.emit_change("timers")
        self.show_toast("Timer toggled")

    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self.ctx.manual_save()
            self.ctx.history.log(
                "app_closed", entity_type="system", summary="FocusFlow closed"
            )
        except Exception as exc:
            logger.error("Error on close: %s", exc)
        event.accept()
