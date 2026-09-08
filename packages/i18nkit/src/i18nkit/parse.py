"""Load translation catalogs: one file per locale, or one folder of namespaces per locale."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PLURAL_FORMS = ("zero", "one", "two", "few", "many", "other")
_PLURAL_SUFFIX = re.compile(rf"_({'|'.join(PLURAL_FORMS)})$")


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


def base_key(key: str) -> str:
    """Drop the library's plural suffix: 'units_many' -> 'units'."""
    return _PLURAL_SUFFIX.sub("", key)


def plural_form(key: str) -> str:
    """The CLDR category a key carries, or '' when it is not a plural form."""
    found = _PLURAL_SUFFIX.search(key)
    return found.group(1) if found else ""


def load_locale(path: str | Path) -> dict[str, str]:
    """Load one locale JSON file (flat or nested) flattened to dot-path keys."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return flatten(data)


def list_locales(path: str | Path) -> dict[str, Path]:
    """Map locale name (file stem) -> JSON file, for the one-file-per-locale layout."""
    base = Path(path)
    if not base.is_dir():
        return {}
    return {f.stem: f for f in sorted(base.glob("*.json"))}


def _locale_folders(base: Path) -> list[Path]:
    return [d for d in sorted(base.iterdir()) if d.is_dir() and any(d.glob("*.json"))]


def layout(path: str | Path) -> str:
    """'namespaced' when each locale is a folder of namespace files, else 'flat'."""
    base = Path(path)
    if base.is_dir() and _locale_folders(base):
        return "namespaced"
    return "flat"


def load_catalog(path: str | Path) -> dict[str, dict[str, str]]:
    """Locale -> keys. A folder per locale addresses its keys as 'namespace:key'."""
    base = Path(path)
    if not base.is_dir():
        return {}
    folders = _locale_folders(base)
    if folders:
        return {
            folder.name: {
                f"{file.stem}:{key}": value
                for file in sorted(folder.glob("*.json"))
                for key, value in load_locale(file).items()
            }
            for folder in folders
        }
    return {name: load_locale(file) for name, file in list_locales(base).items()}


def pick_base(locales: dict[str, Any], base: str = "") -> str:
    """Choose the reference locale: the given one, else en/en_us, else the first."""
    if base and base in locales:
        return base
    for candidate in ("en_us", "en", "en_US"):
        if candidate in locales:
            return candidate
    return next(iter(locales), "")


def roots(mapping: dict[str, str]) -> dict[str, set[str]]:
    """Base key -> the plural forms declared for it ('' when a plain key)."""
    out: dict[str, set[str]] = {}
    for key in mapping:
        out.setdefault(base_key(key), set()).add(plural_form(key))
    return out
