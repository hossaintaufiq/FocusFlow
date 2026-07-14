"""Settings persistence and Windows startup toggle."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from src.models.settings import Settings
from src.services.storage import JsonStorage
from src.utils.config import APP_NAME, ThemeColors
from src.utils.paths import APP_ICON, PROJECT_ROOT

logger = logging.getLogger("FocusFlow.settings")

# Windows registry Run key
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class SettingsService:
    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage
        self.settings = storage.load("settings", Settings.from_dict, Settings)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self.settings, key, default)

    def update(self, **kwargs: Any) -> Settings:
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save()
        return self.settings

    def save(self) -> None:
        self._storage.save("settings", self.settings)

    def theme_colors(self) -> ThemeColors:
        return ThemeColors(accent=self.settings.accent_color)

    def apply_startup(self, enabled: bool | None = None) -> bool:
        """Register/unregister Windows startup. Returns resulting enabled state."""
        if enabled is None:
            enabled = self.settings.launch_on_startup
        self.settings.launch_on_startup = enabled
        self.save()
        if sys.platform == "win32":
            try:
                self._set_windows_startup(enabled)
            except Exception as exc:
                logger.error("Failed to set Windows startup: %s", exc)
        return enabled

    def _set_windows_startup(self, enabled: bool) -> None:
        import winreg

        app_exe = PROJECT_ROOT / "FocusFlow.exe"
        if app_exe.exists():
            command = f'"{app_exe}"'
        else:
            launcher = PROJECT_ROOT / "FocusFlow.pyw"
            script = str(launcher if launcher.exists() else PROJECT_ROOT / "main.py")
            exe = sys.executable
            pythonw = Path(exe).with_name("pythonw.exe")
            runner = str(pythonw) if pythonw.exists() else exe
            command = f'"{runner}" "{script}"'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _RUN_KEY,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )
        try:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
                logger.info("Registered Windows startup: %s", command)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Removed Windows startup entry")
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
