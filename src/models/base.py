"""
Shared model helpers — ID generation and JSON (de)serialization mixin.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, fields, is_dataclass
from datetime import date, datetime, timezone
from typing import Any, TypeVar

T = TypeVar("T", bound="JsonMixin")


def new_id(prefix: str = "") -> str:
    """Return a short unique ID, optionally prefixed (e.g. ``task_a1b2c3d4``)."""
    short = uuid.uuid4().hex[:12]
    return f"{prefix}_{short}" if prefix else short


def utc_now_iso() -> str:
    """Current UTC timestamp as ISO-8601 string."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def today_iso() -> str:
    """Today's date as ``YYYY-MM-DD``."""
    return date.today().isoformat()


def _serialize_value(value: Any) -> Any:
    """Recursively convert dataclass values into JSON-safe primitives."""
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _serialize_value(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


class JsonMixin:
    """Mixin providing ``to_dict`` / ``from_dict`` for dataclass models."""

    def to_dict(self) -> dict[str, Any]:
        if not is_dataclass(self):
            raise TypeError(f"{type(self).__name__} must be a dataclass")
        return _serialize_value(self)

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Build an instance, ignoring unknown keys and filling missing fields."""
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")
        valid = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid}
        return cls(**filtered)  # type: ignore[call-arg]

    def copy_with(self: T, **changes: Any) -> T:
        """Return a shallow copy with selected fields overridden."""
        payload = asdict(self) if is_dataclass(self) else {}
        payload.update(changes)
        return type(self).from_dict(payload)
