"""Compare locales against a base: missing/extra keys and completeness."""
from __future__ import annotations

from typing import Any

from .parse import list_locales, load_locale, pick_base


def locale_diff(path: str, base: str = "") -> dict[str, Any]:
    """For each locale, report keys missing from it and keys it has that the base lacks."""
    locales = list_locales(path)
    if not locales:
        return {"error": "no .json locales found", "path": str(path)}
    base_name = pick_base(locales, base)
    base_keys = set(load_locale(locales[base_name]))
    diff: dict[str, Any] = {}
    for name, file in locales.items():
        if name == base_name:
            continue
        keys = set(load_locale(file))
        missing = sorted(base_keys - keys)
        extra = sorted(keys - base_keys)
        diff[name] = {
            "missing_count": len(missing),
            "extra_count": len(extra),
            "in_sync": not missing and not extra,
            "missing": missing[:200],
            "extra": extra[:200],
        }
    return {
        "base": base_name,
        "locales": sorted(locales),
        "all_in_sync": all(entry["in_sync"] for entry in diff.values()),
        "diff": diff,
    }


def completeness(path: str, base: str = "") -> dict[str, Any]:
    """Percentage of base keys present (translated) in each locale."""
    locales = list_locales(path)
    if not locales:
        return {"error": "no .json locales found", "path": str(path)}
    base_name = pick_base(locales, base)
    base_keys = set(load_locale(locales[base_name]))
    total = len(base_keys) or 1
    out: dict[str, Any] = {}
    for name, file in locales.items():
        translated = len(base_keys & set(load_locale(file)))
        out[name] = {"translated": translated, "total": len(base_keys), "percent": round(100 * translated / total, 1)}
    return {"base": base_name, "completeness": out}
