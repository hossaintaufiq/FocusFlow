"""
FocusFlow — double-click launcher (no console window).

If startup fails, writes logs/launch_error.log and shows a message box.
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
ERROR_LOG = LOG_DIR / "launch_error.log"


def _show_error(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ERROR_LOG.write_text(f"[{stamp}]\n{message}\n", encoding="utf-8")
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0,
            message + f"\n\nDetails saved to:\n{ERROR_LOG}",
            "FocusFlow failed to start",
            0x10,  # MB_ICONERROR
        )
    except Exception:
        pass


def _run() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)

    from main import main

    return main()


if __name__ == "__main__":
    try:
        raise SystemExit(_run())
    except SystemExit:
        raise
    except Exception:
        _show_error(traceback.format_exc())
        raise SystemExit(1)
