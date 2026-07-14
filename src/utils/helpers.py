"""Shared formatting helpers."""

from __future__ import annotations

from datetime import date, datetime


def greeting_for_hour(hour: int | None = None) -> str:
    hour = datetime.now().hour if hour is None else hour
    if hour < 12:
        return "Good Morning"
    if hour < 17:
        return "Good Afternoon"
    return "Good Evening"


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def format_clock(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_date_long(d: date | None = None) -> str:
    d = d or date.today()
    return d.strftime("%A, %B %d, %Y")


def priority_label(priority: str) -> str:
    return priority.replace("_", " ").title()


def status_label(status: str) -> str:
    return status.replace("_", " ").title()
