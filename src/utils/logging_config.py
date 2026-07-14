"""
Application-wide logging setup.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from src.utils.paths import LOGS_DIR, ensure_directories


def setup_logging(level: int = logging.INFO) -> None:
    """Configure console + rotating file logging."""
    ensure_directories()

    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    root.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        LOGS_DIR / "focusflow.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    logging.getLogger("FocusFlow").info("Logging initialized")
