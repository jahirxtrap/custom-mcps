"""Check placeholder consistency across locales and flag empty values."""
from __future__ import annotations

import re
from typing import Any

from .parse import layout, load_catalog, pick_base

_PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}|\{[^{}]*\}|%[sd]")


def placeholders(text: str) -> set[str]:
    """Extract the placeholder tokens ({{name}}, {name}, {0}, %s, %d) from a string."""
    return set(_PLACEHOLDER.findall(text or ""))


def check_format(path: str, base: str = "") -> dict[str, Any]:
    """Report keys whose placeholders differ from the base, and empty translation values."""
    catalog = load_catalog(path)
    if not catalog:
        return {"error": "no locales found", "path": str(path)}
    base_name = pick_base(catalog, base)
    base_map = catalog[base_name]

    issues: list[dict[str, Any]] = []
    empties: list[dict[str, str]] = []
    for name, mapping in catalog.items():
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
                issues.append(
                    {"locale": name, "key": key, "expected": sorted(want), "found": sorted(got)}
                )

    return {
        "base": base_name,
        "layout": layout(path),
        "ok": not issues and not empties,
        "placeholder_issues": issues[:200],
        "empty_values": empties[:200],
    }
