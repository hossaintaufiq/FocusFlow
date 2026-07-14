"""Premium dark theme stylesheet generator."""

from __future__ import annotations

from src.utils.config import ThemeColors


def build_stylesheet(theme: ThemeColors, font_size: int = 10) -> str:
    t = theme
    return f"""
    * {{
        font-family: "Segoe UI", "Segoe UI Variable", "Cascadia Sans", sans-serif;
        font-size: {font_size}pt;
    }}
    QMainWindow, QDialog {{
        background: {t.bg_primary};
        color: {t.text_primary};
    }}
    QWidget {{
        background: transparent;
        color: {t.text_primary};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t.border_strong};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
        background: {t.bg_tertiary};
        border: 1px solid {t.border};
        border-radius: 10px;
        padding: 8px 12px;
        color: {t.text_primary};
        selection-background-color: {t.accent};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
        border: 1px solid {t.accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox QAbstractItemView {{
        background: {t.bg_elevated};
        border: 1px solid {t.border};
        selection-background-color: {t.accent_dim};
        color: {t.text_primary};
    }}
    QPushButton {{
        background: {t.bg_elevated};
        border: 1px solid {t.border};
        border-radius: 10px;
        padding: 8px 16px;
        color: {t.text_primary};
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: {t.bg_tertiary};
        border-color: {t.border_strong};
    }}
    QPushButton:pressed {{
        background: {t.bg_secondary};
    }}
    QPushButton#primaryBtn {{
        background: {t.accent};
        color: #0B1220;
        border: none;
    }}
    QPushButton#primaryBtn:hover {{
        background: {t.accent_hover};
    }}
    QPushButton#dangerBtn {{
        background: rgba(248, 113, 113, 0.15);
        color: {t.danger};
        border: 1px solid rgba(248, 113, 113, 0.35);
    }}
    QPushButton#ghostBtn {{
        background: transparent;
        border: none;
        color: {t.text_secondary};
    }}
    QPushButton#ghostBtn:hover {{
        color: {t.accent};
        background: {t.accent_dim};
    }}
    QFrame#card, QFrame.card {{
        background: {t.bg_glass};
        border: 1px solid {t.border};
        border-radius: 16px;
    }}
    QFrame#sidebar {{
        background: {t.bg_secondary};
        border-right: 1px solid {t.border};
    }}
    QLabel#pageTitle {{
        font-size: {font_size + 8}pt;
        font-weight: 700;
        color: {t.text_primary};
    }}
    QLabel#sectionTitle {{
        font-size: {font_size + 2}pt;
        font-weight: 600;
        color: {t.text_primary};
    }}
    QLabel#muted {{
        color: {t.text_muted};
    }}
    QLabel#accent {{
        color: {t.accent};
        font-weight: 600;
    }}
    QListWidget, QTreeWidget, QTableWidget {{
        background: {t.bg_tertiary};
        border: 1px solid {t.border};
        border-radius: 12px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item, QTreeWidget::item {{
        border-radius: 8px;
        padding: 8px;
        margin: 2px;
    }}
    QListWidget::item:selected, QTreeWidget::item:selected {{
        background: {t.accent_dim};
        color: {t.text_primary};
    }}
    QListWidget::item:hover, QTreeWidget::item:hover {{
        background: rgba(148, 163, 184, 0.1);
    }}
    QCheckBox {{
        spacing: 10px;
        color: {t.text_primary};
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 6px;
        border: 2px solid {t.border_strong};
        background: {t.bg_tertiary};
    }}
    QCheckBox::indicator:checked {{
        background: {t.accent};
        border-color: {t.accent};
    }}
    QProgressBar {{
        background: {t.bg_tertiary};
        border: none;
        border-radius: 8px;
        height: 12px;
        text-align: center;
        color: {t.text_primary};
    }}
    QProgressBar::chunk {{
        border-radius: 8px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.accent}, stop:1 {t.accent_hover});
    }}
    QTabWidget::pane {{
        border: 1px solid {t.border};
        border-radius: 12px;
        background: {t.bg_secondary};
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {t.text_secondary};
        padding: 10px 18px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {t.bg_tertiary};
        color: {t.accent};
        font-weight: 600;
    }}
    QSlider::groove:horizontal {{
        height: 6px;
        background: {t.bg_tertiary};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        margin: -5px 0;
        border-radius: 8px;
        background: {t.accent};
    }}
    QToolTip {{
        background: {t.bg_elevated};
        color: {t.text_primary};
        border: 1px solid {t.border};
        border-radius: 8px;
        padding: 6px 10px;
    }}
    QMenu {{
        background: {t.bg_elevated};
        border: 1px solid {t.border};
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {t.accent_dim};
    }}
    """


def card_style(theme: ThemeColors, radius: int = 16) -> str:
    return (
        f"background: {theme.bg_glass}; border: 1px solid {theme.border}; "
        f"border-radius: {radius}px;"
    )
