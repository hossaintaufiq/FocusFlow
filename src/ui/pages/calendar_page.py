"""Calendar month / week views with task indicators."""

from __future__ import annotations

from calendar import Calendar, month_name
from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, PageHeader


class CalendarPage(BasePage):
    page_id = "calendar"

    def build(self) -> None:
        self._cursor = date.today().replace(day=1)
        self._mode = "month"
        self.layout_main.addWidget(PageHeader("Calendar", "Tasks and deadlines at a glance.", self.theme))

        nav = QHBoxLayout()
        prev = QPushButton("◀")
        nxt = QPushButton("▶")
        prev.clicked.connect(self._prev)
        nxt.clicked.connect(self._next)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 14pt; font-weight: 700;")
        month_btn = QPushButton("Month")
        week_btn = QPushButton("Week")
        month_btn.clicked.connect(lambda: self._set_mode("month"))
        week_btn.clicked.connect(lambda: self._set_mode("week"))
        nav.addWidget(prev)
        nav.addWidget(self.title_label, 1)
        nav.addWidget(month_btn)
        nav.addWidget(week_btn)
        nav.addWidget(nxt)
        self.layout_main.addLayout(nav)

        card = GlassCard(self.theme)
        self.grid = QGridLayout()
        card.body.addLayout(self.grid)
        self.layout_main.addWidget(card)
        self.detail = QLabel()
        self.detail.setObjectName("muted")
        self.detail.setWordWrap(True)
        self.layout_main.addWidget(self.detail)
        self.layout_main.addStretch()

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        self.refresh()

    def _prev(self) -> None:
        if self._mode == "month":
            if self._cursor.month == 1:
                self._cursor = self._cursor.replace(year=self._cursor.year - 1, month=12)
            else:
                self._cursor = self._cursor.replace(month=self._cursor.month - 1)
        else:
            self._cursor = self._cursor - timedelta(days=7)
        self.refresh()

    def _next(self) -> None:
        if self._mode == "month":
            if self._cursor.month == 12:
                self._cursor = self._cursor.replace(year=self._cursor.year + 1, month=1)
            else:
                self._cursor = self._cursor.replace(month=self._cursor.month + 1)
        else:
            self._cursor = self._cursor + timedelta(days=7)
        self.refresh()

    def _tasks_on(self, day: date) -> list:
        iso = day.isoformat()
        return [
            t
            for t in self.ctx.tasks.tasks
            if not t.archived
            and (t.date == iso or (t.deadline[:10] == iso if t.deadline else False))
        ]

    def refresh(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._mode == "month":
            self.title_label.setText(f"{month_name[self._cursor.month]} {self._cursor.year}")
            for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                lab = QLabel(name)
                lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lab.setObjectName("muted")
                self.grid.addWidget(lab, 0, i)
            weeks = Calendar(firstweekday=0).monthdatescalendar(
                self._cursor.year, self._cursor.month
            )
            for r, week in enumerate(weeks, start=1):
                for c, day in enumerate(week):
                    self.grid.addWidget(self._day_cell(day), r, c)
        else:
            # week view starting Monday of cursor week
            start = self._cursor - timedelta(days=self._cursor.weekday())
            self.title_label.setText(f"Week of {start.isoformat()}")
            for c in range(7):
                day = start + timedelta(days=c)
                self.grid.addWidget(self._day_cell(day, tall=True), 0, c)

    def _day_cell(self, day: date, tall: bool = False) -> QWidget:
        tasks = self._tasks_on(day)
        deadlines = [t for t in tasks if t.deadline and t.deadline[:10] == day.isoformat()]
        cell = QPushButton()
        in_month = day.month == self._cursor.month or self._mode == "week"
        today = day == date.today()
        marks = ""
        if tasks:
            marks += " •"
        if deadlines:
            marks += " !"
        cell.setText(f"{day.day}{marks}")
        cell.setMinimumHeight(70 if tall else 54)
        bg = self.theme.bg_tertiary if in_month else self.theme.bg_secondary
        border = self.theme.accent if today else self.theme.border
        cell.setStyleSheet(
            f"QPushButton {{ background: {bg}; border: 1px solid {border}; border-radius: 10px; "
            f"color: {self.theme.text_primary if in_month else self.theme.text_muted}; text-align: top left; padding: 8px; }}"
            f"QPushButton:hover {{ border-color: {self.theme.accent}; }}"
        )
        cell.clicked.connect(lambda _, d=day, ts=tasks: self._show_day(d, ts))
        return cell

    def _show_day(self, day: date, tasks: list) -> None:
        if not tasks:
            self.detail.setText(f"{day.isoformat()}: no tasks")
            return
        lines = [f"{day.isoformat()}:"]
        for t in tasks:
            flag = "⏰" if t.deadline and t.deadline[:10] == day.isoformat() else "☐"
            lines.append(f"  {flag} {t.title} ({t.priority})")
        self.detail.setText("\n".join(lines))
