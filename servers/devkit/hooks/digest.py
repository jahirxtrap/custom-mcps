"""Print the core developer conventions so Claude Code adds them to the session context."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")
print(importlib.import_module("convkit").digest())
