"""
FocusFlow — Personal Productivity OS
Entry point. Bootstraps logging, data layer, and the main window.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when launched as `python main.py`
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from src.utils.logging_config import setup_logging
from src.utils.paths import APP_ICON, ensure_directories
from src.services.app_context import AppContext
from src.ui.main_window import MainWindow


def main() -> int:
    setup_logging()
    ensure_directories()

    app = QApplication(sys.argv)
    app.setApplicationName("FocusFlow")
    app.setOrganizationName("FocusFlow")
    app.setApplicationDisplayName("FocusFlow — Personal Productivity OS")

    if APP_ICON.exists():
        icon = QIcon(str(APP_ICON))
        app.setWindowIcon(icon)
    else:
        try:
            from scripts.generate_icon import main as generate_app_icon

            generate_app_icon()
            if APP_ICON.exists():
                app.setWindowIcon(QIcon(str(APP_ICON)))
        except Exception:
            pass

    # Prefer Segoe UI Variable / Inter-like system fonts on Windows
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Load optional bundled fonts if present
    fonts_dir = ROOT / "assets" / "fonts"
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))

    context = AppContext.create()
    window = MainWindow(context)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
