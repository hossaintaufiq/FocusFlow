"""
Atomic JSON persistence with corruption detection and recovery.
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, TypeVar

from src.utils.paths import DATA_DIR, JSON_FILES, ensure_directories

logger = logging.getLogger("FocusFlow.storage")

T = TypeVar("T")


class JsonCorruptError(Exception):
    """Raised when a JSON file cannot be parsed and recovery failed."""


class JsonStorage:
    """
    Load/save JSON documents with atomic writes and corruption recovery.

    Recovery order on corrupt read:
    1. ``*.bak`` sibling file
    2. Caller-supplied ``default_factory``
    """

    def __init__(self) -> None:
        ensure_directories()

    def path_for(self, key: str) -> Path:
        if key not in JSON_FILES:
            raise KeyError(f"Unknown store key: {key}")
        return JSON_FILES[key]

    def read_raw(self, key: str) -> dict[str, Any] | None:
        """Read JSON; return None if missing; raise JsonCorruptError if unrecoverable."""
        path = self.path_for(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise json.JSONDecodeError("Root must be object", "", 0)
            return data
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            logger.warning("Corrupt JSON at %s: %s — attempting recovery", path, exc)
            recovered = self._recover(path)
            if recovered is not None:
                logger.info("Recovered %s from backup", path.name)
                self.write_raw(key, recovered)
                return recovered
            raise JsonCorruptError(f"Unrecoverable corrupt JSON: {path}") from exc

    def write_raw(self, key: str, data: dict[str, Any]) -> None:
        """Atomically write JSON (temp file + replace) and keep a ``.bak`` sibling."""
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        tmp_path = Path(tmp_name)
        try:
            with open(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
            if path.exists():
                bak = path.with_suffix(path.suffix + ".bak")
                try:
                    shutil.copy2(path, bak)
                except OSError:
                    logger.debug("Could not write .bak for %s", path.name)
            tmp_path.replace(path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    def load(
        self,
        key: str,
        from_dict: Callable[[dict[str, Any]], T],
        default_factory: Callable[[], T],
    ) -> T:
        """Load a typed document, falling back to default on missing file."""
        raw = self.read_raw(key)
        if raw is None:
            obj = default_factory()
            self.save(key, obj)  # type: ignore[arg-type]
            return obj
        try:
            return from_dict(raw)
        except Exception as exc:
            logger.error("Failed to hydrate %s: %s — using defaults", key, exc)
            return default_factory()

    def save(self, key: str, model: Any) -> None:
        """Persist a model that exposes ``to_dict()``."""
        if hasattr(model, "to_dict"):
            self.write_raw(key, model.to_dict())
        elif isinstance(model, dict):
            self.write_raw(key, model)
        else:
            raise TypeError(f"Cannot save type {type(model)}")

    def _recover(self, path: Path) -> dict[str, Any] | None:
        bak = path.with_suffix(path.suffix + ".bak")
        if bak.exists():
            try:
                with bak.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return data
            except Exception as exc:
                logger.error("Backup also corrupt for %s: %s", path.name, exc)
        return None

    def all_data_files(self) -> list[Path]:
        return [p for p in JSON_FILES.values() if p.exists()]

    def data_dir(self) -> Path:
        return DATA_DIR
