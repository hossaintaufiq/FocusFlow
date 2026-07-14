"""History / audit log page."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton

from src.ui.pages.base_page import BasePage
from src.widgets.common import GlassCard, PageHeader


class HistoryPage(BasePage):
    page_id = "history"

    def build(self) -> None:
        self.layout_main.addWidget(
            PageHeader("History", "Every action is logged.", self.theme)
        )
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search history…")
        self.search.textChanged.connect(self.refresh)
        clear = QPushButton("Clear History")
        clear.setObjectName("dangerBtn")
        clear.clicked.connect(self._clear)
        bar.addWidget(self.search, 1)
        bar.addWidget(clear)
        self.layout_main.addLayout(bar)

        card = GlassCard(self.theme)
        self.list = QListWidget()
        card.body.addWidget(self.list)
        self.layout_main.addWidget(card, 1)

    def refresh(self) -> None:
        self.list.clear()
        for entry in self.ctx.history.search(self.search.text()):
            item = QListWidgetItem(
                f"{entry.timestamp.replace('T', ' ')[:19]}  ·  {entry.summary}"
            )
            self.list.addItem(item)

    def _clear(self) -> None:
        self.ctx.history.clear()
        self.refresh()
