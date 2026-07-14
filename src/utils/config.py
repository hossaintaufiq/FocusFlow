"""
Central application configuration and constants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


APP_NAME: Final[str] = "FocusFlow"
APP_VERSION: Final[str] = "1.0.0"
APP_TAGLINE: Final[str] = "Personal Productivity OS"

# Persistence
AUTO_SAVE_INTERVAL_MS: Final[int] = 1000  # timer tick persistence
BACKUP_RETENTION_DAYS: Final[int] = 30
MAX_HISTORY_ENTRIES: Final[int] = 5000

# Pomodoro defaults (minutes)
DEFAULT_FOCUS_MINUTES: Final[int] = 25
DEFAULT_SHORT_BREAK_MINUTES: Final[int] = 5
DEFAULT_LONG_BREAK_MINUTES: Final[int] = 15
DEFAULT_LONG_BREAK_INTERVAL: Final[int] = 4  # after N focus sessions

# XP / gamification
XP_PER_TASK: Final[int] = 25
XP_PER_HABIT: Final[int] = 15
XP_PER_FOCUS_MINUTE: Final[int] = 1
XP_PER_STREAK_DAY: Final[int] = 5

# UI
SIDEBAR_WIDTH: Final[int] = 240
SIDEBAR_COLLAPSED_WIDTH: Final[int] = 72
ANIMATION_DURATION_MS: Final[int] = 220

# Default accent (teal — avoiding purple bias)
DEFAULT_ACCENT: Final[str] = "#2DD4BF"

# Navigation — flat list (shortcuts) + grouped sidebar sections
NAV_PAGES: Final[tuple[tuple[str, str, str], ...]] = (
    ("dashboard", "Dashboard", "DB"),
    ("today", "Today's Tasks", "TD"),
    ("projects", "Projects", "PR"),
    ("habits", "Habits & Daily", "HB"),
    ("calendar", "Calendar", "CA"),
    ("pomodoro", "Pomodoro", "PM"),
    ("notes", "Notes", "NT"),
    ("statistics", "Statistics", "ST"),
    ("history", "History", "HI"),
    ("settings", "Settings", "SF"),
)

NAV_SECTIONS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("Overview", ("dashboard", "today")),
    ("Work", ("projects", "calendar", "pomodoro")),
    ("Track", ("habits", "notes", "statistics")),
    ("System", ("history", "settings")),
)

NAV_LABELS: Final[dict[str, str]] = {pid: title for pid, title, _ in NAV_PAGES}
NAV_ICONS: Final[dict[str, str]] = {pid: icon for pid, _, icon in NAV_PAGES}

TASK_STATUSES: Final[tuple[str, ...]] = (
    "not_started",
    "in_progress",
    "paused",
    "completed",
    "cancelled",
)

TASK_PRIORITIES: Final[tuple[str, ...]] = (
    "low",
    "medium",
    "high",
    "urgent",
)

PRIORITY_COLORS: Final[dict[str, str]] = {
    "low": "#64748B",
    "medium": "#38BDF8",
    "high": "#FBBF24",
    "urgent": "#F87171",
}

DEFAULT_QUOTE: Final[str] = (
    "Focus on being productive instead of busy. — Tim Ferriss"
)

QUOTES: Final[tuple[str, ...]] = (
    "Focus on being productive instead of busy. — Tim Ferriss",
    "The secret of getting ahead is getting started. — Mark Twain",
    "Done is better than perfect. — Sheryl Sandberg",
    "Small daily improvements are the key to staggering long-term results. — Robin Sharma",
    "You don't have to be extreme, just consistent. — Unknown",
    "Deep work is the ability to focus without distraction. — Cal Newport",
    "Action is the foundational key to all success. — Pablo Picasso",
    "What gets measured gets managed. — Peter Drucker",
    "Discipline is choosing between what you want now and what you want most. — Abraham Lincoln",
    "Clarity about what matters provides clarity about what does not. — Cal Newport",
)


@dataclass
class ThemeColors:
    """Dark theme palette used across the UI."""

    bg_primary: str = "#0B1220"
    bg_secondary: str = "#111827"
    bg_tertiary: str = "#1A2332"
    bg_elevated: str = "#1E293B"
    bg_glass: str = "rgba(30, 41, 59, 0.72)"
    border: str = "rgba(148, 163, 184, 0.18)"
    border_strong: str = "rgba(148, 163, 184, 0.32)"
    text_primary: str = "#F1F5F9"
    text_secondary: str = "#94A3B8"
    text_muted: str = "#64748B"
    accent: str = DEFAULT_ACCENT
    accent_hover: str = "#5EEAD4"
    accent_dim: str = "rgba(45, 212, 191, 0.15)"
    success: str = "#34D399"
    warning: str = "#FBBF24"
    danger: str = "#F87171"
    info: str = "#38BDF8"
    shadow: str = "rgba(0, 0, 0, 0.45)"
    gradient_start: str = "#0B1220"
    gradient_end: str = "#0F1C2E"


@dataclass
class AppDefaults:
    """Factory defaults for settings.json."""

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
    extra: dict = field(default_factory=dict)
