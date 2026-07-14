"""Matplotlib chart widgets embedded in Qt."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from src.utils.config import ThemeColors


class ChartWidget(QWidget):
    def __init__(self, theme: ThemeColors, parent=None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.figure = Figure(figsize=(5, 2.8), dpi=100)
        self.figure.patch.set_facecolor(theme.bg_secondary)
        self.canvas = FigureCanvasQTAgg(self.figure)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.canvas)

    def _style_ax(self, ax) -> None:
        ax.set_facecolor(self.theme.bg_tertiary)
        ax.tick_params(colors=self.theme.text_muted, labelsize=8)
        # Matplotlib needs hex/#rgb — CSS rgba() is invalid
        spine_color = "#475569"
        for spine in ax.spines.values():
            spine.set_color(spine_color)
        ax.title.set_color(self.theme.text_primary)

    def plot_line(self, labels: list[str], values: list[float], title: str = "") -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._style_ax(ax)
        ax.plot(labels, values, color=self.theme.accent, linewidth=2.2, marker="o", markersize=4)
        ax.fill_between(range(len(values)), values, alpha=0.15, color=self.theme.accent)
        if title:
            ax.set_title(title, fontsize=10, pad=8)
        try:
            self.figure.tight_layout(pad=1.2)
        except Exception:
            pass
        self.canvas.draw_idle()

    def plot_bar(self, labels: list[str], values: list[float], title: str = "") -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._style_ax(ax)
        ax.bar(labels, values, color=self.theme.accent, alpha=0.85, width=0.6)
        if title:
            ax.set_title(title, fontsize=10, pad=8)
        try:
            self.figure.tight_layout(pad=1.2)
        except Exception:
            pass
        self.canvas.draw_idle()

    def plot_pie(self, labels: list[str], values: list[float], title: str = "") -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(self.theme.bg_tertiary)
        if not values or sum(values) <= 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color=self.theme.text_muted)
            ax.axis("off")
        else:
            colors = [
                self.theme.accent,
                self.theme.info,
                self.theme.warning,
                self.theme.success,
                self.theme.danger,
                "#A78BFA",
                "#FB7185",
            ]
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct="%1.0f%%",
                colors=colors[: len(values)],
                textprops={"color": self.theme.text_secondary, "fontsize": 8},
            )
            for at in autotexts:
                at.set_color("#0B1220")
                at.set_fontweight("bold")
        if title:
            ax.set_title(title, fontsize=10, color=self.theme.text_primary, pad=8)
        try:
            self.figure.tight_layout(pad=1.2)
        except Exception:
            pass
        self.canvas.draw_idle()
