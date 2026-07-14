"""Base page class for FocusFlow views."""

from __future__ import annotations

from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from src.services.app_context import AppContext
from src.utils.config import ThemeColors


class BasePage(QWidget):
    """Scrollable page with a content column."""

    page_id: str = ""

    def __init__(self, context: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.ctx = context
        self.theme: ThemeColors = context.theme

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.content = QWidget()
        self.layout_main = QVBoxLayout(self.content)
        self.layout_main.setContentsMargins(28, 24, 28, 28)
        self.layout_main.setSpacing(16)
        self._scroll.setWidget(self.content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        self.build()
        self.ctx.signals.data_changed.connect(self._on_data)

    def build(self) -> None:
        """Override to construct widgets."""

    def refresh(self) -> None:
        """Override to reload data into widgets."""

    def _on_data(self, kind: str) -> None:
        self.refresh()

    def on_show(self) -> None:
        self.refresh()
