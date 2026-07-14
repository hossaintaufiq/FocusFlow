"""Settings / user preferences model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin
from src.utils.config import (
    DEFAULT_ACCENT,
    DEFAULT_FOCUS_MINUTES,
    DEFAULT_LONG_BREAK_INTERVAL,
    DEFAULT_LONG_BREAK_MINUTES,
    DEFAULT_SHORT_BREAK_MINUTES,
)


@dataclass
class Settings(JsonMixin):
    """Persisted user preferences for ``settings.json``."""

    version: int = 1
    theme: str = "dark"
    accent_color: str = DEFAULT_ACCENT
    font_size: int = 10
    notifications_enabled: bool = True
    sound_enabled: bool = True
    launch_on_startup: bool = False
    auto_backup: bool = True
    focus_minutes: int = DEFAULT_FOCUS_MINUTES
    short_break_minutes: int = DEFAULT_SHORT_BREAK_MINUTES
    long_break_minutes: int = DEFAULT_LONG_BREAK_MINUTES
    long_break_interval: int = DEFAULT_LONG_BREAK_INTERVAL
    morning_reminder: bool = True
    evening_summary: bool = True
    water_goal_ml: int = 2500
    daily_quote_enabled: bool = True
    sidebar_collapsed: bool = False
    language: str = "en"
    extra: dict[str, Any] = field(default_factory=dict)
