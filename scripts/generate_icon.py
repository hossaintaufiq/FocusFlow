"""Generate FocusFlow app icon (assets/icons/focusflow.ico)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.utils.config import DEFAULT_ACCENT  # noqa: E402
from src.utils.paths import ICONS_DIR  # noqa: E402


def _render(size: int, accent: str = DEFAULT_ACCENT) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = max(2, size // 16)
    r = size - margin * 2
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#0F172A"))
    p.drawRoundedRect(margin, margin, r, r, size // 5, size // 5)

    p.setBrush(QColor(accent))
    inner = margin + size // 8
    inner_r = r - size // 4
    p.drawRoundedRect(inner, inner, inner_r, inner_r, size // 6, size // 6)

    font = QFont("Segoe UI", max(8, size // 3))
    font.setWeight(QFont.Weight.Bold)
    p.setFont(font)
    p.setPen(QColor("#0B1220"))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "F")
    p.end()
    return px


def main() -> int:
    app = QApplication([])
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_render(size))
    out = ICONS_DIR / "focusflow.ico"
    if not icon.pixmap(256).save(str(out), "ICO"):
        print("Failed to write icon")
        return 1
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
