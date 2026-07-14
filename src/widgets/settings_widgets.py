"""Professional settings controls — toggle rows with painted checkmarks."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.utils.config import ThemeColors


class SettingToggle(QWidget):
    """Settings toggle with a reliable painted checkmark."""

    toggled = Signal(bool)

    def __init__(self, theme: ThemeColors, checked: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._checked = checked
        self._hover = False
        self._block = False
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Toggle on / off")

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool, *, emit: bool = True) -> None:
        self._block = not emit
        self._checked = checked
        self.update()
        self._block = False

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.update()
            if not self._block:
                self.toggled.emit(self._checked)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        t = self._theme

        if self._checked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(t.accent))
            painter.drawRoundedRect(rect, 8, 8)
            pen = QPen(QColor("#0B1220"))
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(8, 14, 12, 18)
            painter.drawLine(12, 18, 20, 9)
        else:
            border = QColor(t.accent if self._hover else t.border_strong)
            painter.setPen(QPen(border, 2))
            painter.setBrush(QColor(t.bg_elevated))
            painter.drawRoundedRect(rect, 8, 8)
        painter.end()


class SettingRow(QFrame):
    """Label + description + toggle in a professional row."""

    toggled = Signal(bool)

    def __init__(
        self,
        theme: ThemeColors,
        title: str,
        description: str = "",
        *,
        checked: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingRow")
        self._theme = theme
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(14)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"font-weight: 650; font-size: 10.5pt; color: {theme.text_primary}; "
            "background: transparent; border: none;"
        )
        text_col.addWidget(self.title_label)
        self.desc_label = QLabel(description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(
            f"color: {theme.text_muted}; font-size: 9pt; background: transparent; border: none;"
        )
        if description:
            text_col.addWidget(self.desc_label)
        else:
            self.desc_label.hide()
        lay.addLayout(text_col, 1)

        self.toggle = SettingToggle(theme, checked=checked)
        self.toggle.toggled.connect(self.toggled.emit)
        lay.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignVCenter)

        self.setStyleSheet(
            f"QFrame#settingRow {{ background: {theme.bg_tertiary}; "
            f"border: 1px solid {theme.border}; border-radius: 12px; }}"
            f"QFrame#settingRow:hover {{ border-color: {theme.border_strong}; "
            f"background: {theme.bg_elevated}; }}"
        )

    def is_checked(self) -> bool:
        return self.toggle.is_checked()

    def set_checked(self, checked: bool) -> None:
        self.toggle.set_checked(checked, emit=False)


class SettingSectionHeader(QLabel):
    def __init__(self, title: str, theme: ThemeColors, parent=None) -> None:
        super().__init__(title.upper(), parent)
        self.setStyleSheet(
            f"color: {theme.text_muted}; font-size: 8.5pt; font-weight: 700; "
            f"letter-spacing: 1.2px; padding: 8px 4px 4px 4px; "
            "background: transparent; border: none;"
        )
