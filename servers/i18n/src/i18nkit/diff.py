"""Compare locales against a base: missing/extra keys, plural coverage and completeness."""
from __future__ import annotations

from typing import Any

from .parse import layout, load_catalog, pick_base, roots


def _pluralized(forms: set[str]) -> bool:
    return forms != {""}


def locale_diff(path: str, base: str = "") -> dict[str, Any]:
    """Per locale: keys missing from it, keys the base lacks, and plural forms that disagree."""
    catalog = load_catalog(path)
    if not catalog:
        return {"error": "no locales found", "path": str(path)}
    base_name = pick_base(catalog, base)
    base_roots = roots(catalog[base_name])

    diff: dict[str, Any] = {}
    for name, mapping in catalog.items():
        if name == base_name:
            continue
        local_roots = roots(mapping)
        missing = sorted(set(base_roots) - set(local_roots))
        extra = sorted(set(local_roots) - set(base_roots))
        plural = [
            {"key": key, "base": sorted(base_roots[key]), "locale": sorted(local_roots[key])}
            for key in sorted(set(base_roots) & set(local_roots))
            if _pluralized(base_roots[key]) != _pluralized(local_roots[key])
        ]
        diff[name] = {
            "missing_count": len(missing),
            "extra_count": len(extra),
            "in_sync": not missing and not extra and not plural,
            "missing": missing[:200],
            "extra": extra[:200],
            "plural_mismatch": plural[:200],
        }
    return {
        "base": base_name,
        "layout": layout(path),
        "locales": sorted(catalog),
        "all_in_sync": all(entry["in_sync"] for entry in diff.values()),
        "diff": diff,
        "note": "Keys are compared without their plural suffix; a locale may legitimately hold "
        "more CLDR forms than the base. plural_mismatch is a key pluralized on one side only, "
        "which breaks the count lookup.",
    }


def completeness(path: str, base: str = "") -> dict[str, Any]:
    """Percentage of base keys (plural suffix ignored) present in each locale."""
    catalog = load_catalog(path)
    if not catalog:
        return {"error": "no locales found", "path": str(path)}
    base_name = pick_base(catalog, base)
    base_roots = set(roots(catalog[base_name]))
    total = len(base_roots) or 1
    out: dict[str, Any] = {}
    for name, mapping in catalog.items():
        translated = len(base_roots & set(roots(mapping)))
        out[name] = {
            "translated": translated,
            "total": len(base_roots),
            "percent": round(100 * translated / total, 1),
        }
    return {"base": base_name, "layout": layout(path), "completeness": out}
