"""Desktop notifications and optional sound cues."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.utils.config import APP_NAME
from src.utils.paths import SOUNDS_DIR

logger = logging.getLogger("FocusFlow.notify")


class NotificationService:
    def __init__(self, *, enabled: bool = True, sound_enabled: bool = True) -> None:
        self.enabled = enabled
        self.sound_enabled = sound_enabled

    def notify(self, title: str, message: str, timeout: int = 5) -> None:
        if not self.enabled:
            return
        try:
            from plyer import notification

            notification.notify(
                title=f"{APP_NAME}: {title}",
                message=message,
                app_name=APP_NAME,
                timeout=timeout,
            )
        except Exception as exc:
            logger.debug("plyer notify failed: %s — falling back", exc)
            self._windows_fallback(title, message)

    def _windows_fallback(self, title: str, message: str) -> None:
        if sys.platform != "win32":
            return
        try:
            # Lightweight balloon via PowerShell (no extra deps)
            import subprocess

            ps = (
                f'[void][Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");'
                f"$n = New-Object System.Windows.Forms.NotifyIcon;"
                f"$n.Icon = [System.Drawing.SystemIcons]::Information;"
                f"$n.Visible = $true;"
                f'$n.ShowBalloonTip(4000, "{APP_NAME}: {title}", "{message}", '
                f"[System.Windows.Forms.ToolTipIcon]::Info);"
                f"Start-Sleep -Seconds 5; $n.Dispose()"
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            logger.warning("Notification failed: %s", exc)

    def play_sound(self, name: str = "notify") -> None:
        if not self.sound_enabled:
            return
        path = SOUNDS_DIR / f"{name}.wav"
        if not path.exists():
            # Generate a tiny system beep on Windows
            if sys.platform == "win32":
                try:
                    import winsound

                    winsound.MessageBeep(winsound.MB_OK)
                except Exception:
                    pass
            return
        if sys.platform == "win32":
            try:
                import winsound

                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as exc:
                logger.debug("Sound play failed: %s", exc)

    def task_reminder(self, task_title: str) -> None:
        self.notify("Task Reminder", task_title)
        self.play_sound()

    def break_reminder(self) -> None:
        self.notify("Break Time", "Take a short break — you earned it.")
        self.play_sound()

    def focus_complete(self) -> None:
        self.notify("Focus Complete", "Pomodoro finished. Great work!")
        self.play_sound()

    def deadline_reminder(self, task_title: str) -> None:
        self.notify("Deadline Approaching", task_title)
        self.play_sound()

    def morning_reminder(self) -> None:
        self.notify("Good Morning", "Plan your focus for today.")

    def evening_summary(self, completed: int, focus_minutes: int) -> None:
        self.notify(
            "Evening Summary",
            f"Completed {completed} tasks · {focus_minutes} min focused",
        )
