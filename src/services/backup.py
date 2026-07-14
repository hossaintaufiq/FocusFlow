"""
Daily backup & restore for all JSON data files.
Keeps the last BACKUP_RETENTION_DAYS dated folders.
"""

from __future__ import annotations

import logging
import shutil
from datetime import date, datetime
from pathlib import Path

from src.utils.config import BACKUP_RETENTION_DAYS
from src.utils.paths import BACKUP_DIR, JSON_FILES, ensure_directories

logger = logging.getLogger("FocusFlow.backup")


class BackupService:
    """Create dated backups and restore from them."""

    def __init__(self) -> None:
        ensure_directories()

    def backup_root(self) -> Path:
        return BACKUP_DIR

    def today_stamp(self) -> str:
        return date.today().isoformat()

    def list_backups(self) -> list[Path]:
        if not BACKUP_DIR.exists():
            return []
        dirs = [p for p in BACKUP_DIR.iterdir() if p.is_dir()]
        return sorted(dirs, key=lambda p: p.name, reverse=True)

    def create_backup(self, label: str | None = None) -> Path:
        """Copy all JSON stores into ``backups/YYYY-MM-DD[_label]/``."""
        ensure_directories()
        stamp = self.today_stamp()
        folder_name = f"{stamp}_{label}" if label else stamp
        target = BACKUP_DIR / folder_name
        # If daily folder already exists, create a timestamped one
        if target.exists() and label is None:
            folder_name = f"{stamp}_{datetime.now().strftime('%H%M%S')}"
            target = BACKUP_DIR / folder_name
        target.mkdir(parents=True, exist_ok=True)

        copied = 0
        for path in JSON_FILES.values():
            if path.exists():
                shutil.copy2(path, target / path.name)
                copied += 1
        logger.info("Backup created at %s (%d files)", target, copied)
        self.prune_old_backups()
        return target

    def ensure_daily_backup(self) -> Path | None:
        """Create today's backup if one does not already exist for this date."""
        stamp = self.today_stamp()
        existing = [p for p in self.list_backups() if p.name.startswith(stamp)]
        if existing:
            return existing[0]
        return self.create_backup()

    def restore_backup(self, backup_dir: Path | str) -> int:
        """Overwrite live JSON files from a backup folder. Returns file count."""
        src = Path(backup_dir)
        if not src.is_dir():
            raise FileNotFoundError(f"Backup not found: {src}")
        restored = 0
        for path in JSON_FILES.values():
            candidate = src / path.name
            if candidate.exists():
                shutil.copy2(candidate, path)
                restored += 1
        logger.info("Restored %d files from %s", restored, src)
        return restored

    def prune_old_backups(self, keep: int = BACKUP_RETENTION_DAYS) -> None:
        backups = self.list_backups()
        for old in backups[keep:]:
            try:
                shutil.rmtree(old)
                logger.info("Pruned old backup %s", old.name)
            except OSError as exc:
                logger.warning("Failed to prune %s: %s", old, exc)
