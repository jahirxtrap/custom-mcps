"""Load translation files (flat or nested JSON) and flatten them to dot-path keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def flatten(data: Any, prefix: str = "") -> dict[str, str]:
    """Flatten nested dicts/lists into dot-path keys; leaf values become strings."""
    out: dict[str, str] = {}
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list):
        items = ((str(i), v) for i, v in enumerate(data))
    else:
        return out
    for key, value in items:
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, (dict, list)):
            out.update(flatten(value, path))
        else:
            out[path] = "" if value is None else str(value)
    return out


def load_locale(path: str | Path) -> dict[str, str]:
    """Load a locale JSON file (flat or nested) flattened to dot-path keys."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return flatten(data)


def list_locales(path: str | Path) -> dict[str, Path]:
    """Map locale name (file stem) -> JSON file for every *.json under `path`."""
    base = Path(path)
    if not base.is_dir():
        return {}
    return {f.stem: f for f in sorted(base.glob("*.json"))}


def pick_base(locales: dict[str, Path], base: str = "") -> str:
    """Choose the reference locale: the given one, else en/en_us, else the first."""
    if base and base in locales:
        return base
    for candidate in ("en_us", "en", "en_US"):
        if candidate in locales:
            return candidate
    return next(iter(locales), "")
