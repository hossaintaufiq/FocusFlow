"""
FocusFlow — double-click launcher (no console window).

Associate .pyw with pythonw.exe, or use FocusFlow.vbs / Desktop shortcut instead.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
