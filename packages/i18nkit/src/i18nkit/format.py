"""Check placeholder consistency across locales and flag empty values."""
from __future__ import annotations

import re
from typing import Any

from .parse import list_locales, load_locale, pick_base

_PLACEHOLDER = re.compile(r"\{[^}]*\}|%[sd]")


def placeholders(text: str) -> set[str]:
    """Extract the placeholder tokens ({name}, {0}, %s, %d) from a string."""
    return set(_PLACEHOLDER.findall(text or ""))


def check_format(path: str, base: str = "") -> dict[str, Any]:
    """Report keys whose placeholders differ from the base, and empty translation values."""
    locales = list_locales(path)
    if not locales:
        return {"error": "no .json locales found", "path": str(path)}
    base_name = pick_base(locales, base)
    loaded = {name: load_locale(file) for name, file in locales.items()}
    base_map = loaded[base_name]

    issues: list[dict[str, Any]] = []
    empties: list[dict[str, str]] = []
    for name, mapping in loaded.items():
        for key, value in mapping.items():
            if value == "":
                empties.append({"locale": name, "key": key})
        if name == base_name:
            continue
        for key, base_value in base_map.items():
            if key not in mapping:
                continue
            want = placeholders(base_value)
            got = placeholders(mapping[key])
            if want != got:
                issues.append({"locale": name, "key": key, "expected": sorted(want), "found": sorted(got)})

    return {
        "base": base_name,
        "ok": not issues and not empties,
        "placeholder_issues": issues[:200],
        "empty_values": empties[:200],
    }
