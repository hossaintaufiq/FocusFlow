"""
Path helpers for FocusFlow. Resolves project root and data/asset locations.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _project_root() -> Path:
    """Resolve app root for source checkout and frozen PyInstaller builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


# FocusFlow/ (parent of src/, or folder containing FocusFlow.exe)
PROJECT_ROOT: Path = _project_root()

DATA_DIR: Path = PROJECT_ROOT / "data"
BACKUP_DIR: Path = DATA_DIR / "backups"
ASSETS_DIR: Path = PROJECT_ROOT / "assets"
ICONS_DIR: Path = ASSETS_DIR / "icons"
APP_ICON: Path = ICONS_DIR / "focusflow.ico"
IMAGES_DIR: Path = ASSETS_DIR / "images"
SOUNDS_DIR: Path = ASSETS_DIR / "sounds"
FONTS_DIR: Path = ASSETS_DIR / "fonts"
LOGS_DIR: Path = PROJECT_ROOT / "logs"

# Canonical JSON stores
JSON_FILES: dict[str, Path] = {
    "tasks": DATA_DIR / "tasks.json",
    "history": DATA_DIR / "history.json",
    "settings": DATA_DIR / "settings.json",
    "projects": DATA_DIR / "projects.json",
    "habits": DATA_DIR / "habits.json",
    "notes": DATA_DIR / "notes.json",
    "timers": DATA_DIR / "timers.json",
    "stats": DATA_DIR / "stats.json",
    "extras": DATA_DIR / "extras.json",
    "achievements": DATA_DIR / "achievements.json",
}


def ensure_directories() -> None:
    """Create required directories if they do not exist."""
    for path in (
        DATA_DIR,
        BACKUP_DIR,
        ASSETS_DIR,
        ICONS_DIR,
        IMAGES_DIR,
        SOUNDS_DIR,
        FONTS_DIR,
        LOGS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
