"""Reusable premium UI widgets."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.utils.config import ThemeColors


def apply_shadow(widget: QWidget, blur: int = 24, dy: int = 8, alpha: int = 80) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, dy)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


class GlassCard(QFrame):
    """Rounded glassmorphism card container."""

    def __init__(self, theme: ThemeColors, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            f"QFrame#card {{ background: {theme.bg_glass}; border: 1px solid {theme.border}; "
            f"border-radius: 16px; }}"
        )
        apply_shadow(self, blur=28, dy=10, alpha=70)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 18, 20, 18)
        self._layout.setSpacing(10)

    @property
    def body(self) -> QVBoxLayout:
        return self._layout


class StatChip(QFrame):
    """Compact metric display."""

    def __init__(
        self,
        theme: ThemeColors,
        label: str,
        value: str = "0",
        accent: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        color = accent or theme.accent
        self.setStyleSheet(
            f"QFrame {{ background: {theme.bg_tertiary}; border: 1px solid {theme.border}; "
            f"border-radius: 14px; }}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: 22pt; font-weight: 700; border: none; background: transparent;"
        )
        self.caption = QLabel(label)
        self.caption.setStyleSheet(
            f"color: {theme.text_muted}; font-size: 9pt; border: none; background: transparent;"
        )
        lay.addWidget(self.value_label)
        lay.addWidget(self.caption)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class ProgressRing(QWidget):
    """Circular progress indicator (0–100)."""

    def __init__(
        self,
        theme: ThemeColors,
        size: int = 120,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._value = 0.0
        self._thickness = 10
        self.setFixedSize(size, size)

    def get_value(self) -> float:
        return self._value

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(100.0, float(value)))
        self.update()

    value = Property(float, get_value, set_value)

    def animate_to(self, target: float, duration: int = 600) -> None:
        anim = QPropertyAnimation(self, b"value", self)
        anim.setDuration(duration)
        anim.setStartValue(self._value)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim = anim  # keep ref

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(
            self._thickness, self._thickness, -self._thickness, -self._thickness
        )
        # track
        pen = QPen(QColor(self._theme.bg_elevated))
        pen.setWidth(self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        # progress
        pen.setColor(QColor(self._theme.accent))
        painter.setPen(pen)
        span = int(-self._value / 100.0 * 360 * 16)
        painter.drawArc(rect, 90 * 16, span)
        # center text
        painter.setPen(QColor(self._theme.text_primary))
        font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{int(self._value)}%")


class AnimatedCheckBox(QWidget):
    """Completion checkbox with a painted checkmark (reliable across fonts)."""

    toggled_custom = Signal(bool)

    def __init__(self, theme: ThemeColors, checked: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._checked = checked
        self._hover = False
        self.setFixedSize(26, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Mark complete / incomplete")

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self.update()

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
            self.toggled_custom.emit(self._checked)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        if self._checked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(self._theme.accent))
            painter.drawRoundedRect(rect, 7, 7)
            # checkmark
            pen = QPen(QColor("#0B1220"))
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(7, 13, 11, 17)
            painter.drawLine(11, 17, 19, 8)
        else:
            border = QColor(self._theme.accent if self._hover else self._theme.border_strong)
            painter.setPen(QPen(border, 2))
            painter.setBrush(QColor(self._theme.bg_elevated))
            painter.drawRoundedRect(rect, 7, 7)
        painter.end()


class GradientBar(QWidget):
    """Horizontal gradient progress bar."""

    def __init__(self, theme: ThemeColors, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._value = 0.0
        self.setFixedHeight(10)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(100.0, float(value)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._theme.bg_tertiary))
        painter.drawRoundedRect(self.rect(), 5, 5)
        w = int(self.width() * self._value / 100.0)
        if w > 0:
            from PySide6.QtGui import QLinearGradient

            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(self._theme.accent))
            grad.setColorAt(1, QColor(self._theme.accent_hover))
            painter.setBrush(grad)
            painter.drawRoundedRect(0, 0, w, self.height(), 5, 5)


class SidebarSectionLabel(QLabel):
    """Uppercase section divider in the sidebar."""

    def __init__(self, text: str, theme: ThemeColors, parent=None) -> None:
        super().__init__(text.upper(), parent)
        self.setStyleSheet(
            f"color: {theme.text_muted}; font-size: 8pt; font-weight: 700; "
            f"letter-spacing: 1.4px; padding: 14px 12px 6px 12px; "
            "background: transparent; border: none;"
        )


class SidebarButton(QFrame):
    """Navigation item with monogram badge and active accent strip."""

    clicked = Signal()

    def __init__(
        self,
        page_id: str,
        label: str,
        icon_text: str,
        theme: ThemeColors,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.page_id = page_id
        self._theme = theme
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 12, 8)
        lay.setSpacing(12)

        self.badge = QLabel(icon_text)
        self.badge.setFixedSize(32, 32)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.badge)

        self.label = QLabel(label)
        self.label.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.label, 1)

        self.set_active(False)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def set_active(self, active: bool) -> None:
        self._active = active
        t = self._theme
        if active:
            self.setStyleSheet(
                f"QFrame {{ border: none; border-left: 3px solid {t.accent}; "
                f"border-top-right-radius: 10px; border-bottom-right-radius: 10px; "
                f"background: {t.accent_dim}; }}"
            )
            self.badge.setStyleSheet(
                f"background: {t.accent}; color: #0B1220; font-weight: 800; "
                f"font-size: 8.5pt; border-radius: 8px; border: none;"
            )
            self.label.setStyleSheet(
                f"color: {t.text_primary}; font-weight: 650; font-size: 10pt; "
                "background: transparent; border: none;"
            )
        else:
            self.setStyleSheet(
                f"QFrame {{ border: none; border-left: 3px solid transparent; "
                f"border-top-right-radius: 10px; border-bottom-right-radius: 10px; "
                f"background: transparent; }}"
            )
            self.badge.setStyleSheet(
                f"background: {t.bg_tertiary}; color: {t.text_muted}; font-weight: 700; "
                f"font-size: 8.5pt; border-radius: 8px; border: 1px solid {t.border};"
            )
            self.label.setStyleSheet(
                f"color: {t.text_secondary}; font-weight: 500; font-size: 10pt; "
                "background: transparent; border: none;"
            )

    def enterEvent(self, event) -> None:  # noqa: N802
        if not self._active:
            t = self._theme
            self.setStyleSheet(
                f"QFrame {{ border: none; border-left: 3px solid {t.border_strong}; "
                f"border-top-right-radius: 10px; border-bottom-right-radius: 10px; "
                f"background: rgba(148,163,184,0.08); }}"
            )
            self.label.setStyleSheet(
                f"color: {t.text_primary}; font-weight: 500; font-size: 10pt; "
                "background: transparent; border: none;"
            )
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        if not self._active:
            self.set_active(False)
        super().leaveEvent(event)


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", theme: ThemeColors | None = None, parent=None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 8)
        lay.setSpacing(4)
        self.title = QLabel(title)
        self.title.setObjectName("pageTitle")
        lay.addWidget(self.title)
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("muted")
        if not subtitle:
            self.subtitle.hide()
        lay.addWidget(self.subtitle)

    def set_subtitle(self, text: str) -> None:
        self.subtitle.setText(text)
        self.subtitle.setVisible(bool(text))


class EmptyState(QLabel):
    def __init__(self, text: str, theme: ThemeColors, parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"color: {theme.text_muted}; padding: 40px; font-size: 11pt;")
