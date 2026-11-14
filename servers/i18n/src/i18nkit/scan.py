"""Cross the keys the code asks for with the keys the locales declare."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .parse import base_key, layout, load_catalog, pick_base

_DEFAULT_PATTERNS = [r"""\bt\(\s*["']([^"']+)["']""", r"""\btr\(\s*["']([^"']+)["']"""]
_SOURCE_EXT = (".java", ".gd", ".ts", ".tsx", ".js", ".jsx", ".py", ".kt", ".mjs")
_SKIP_DIRS = {
    ".expo", ".git", ".next", ".turbo", ".venv", "__pycache__", "build", "dist", "generated",
    "node_modules", "out", "target", "vendor",
}


def _source_files(base: Path):
    if base.is_file():
        yield base
        return
    for entry in base.iterdir():
        if entry.name in _SKIP_DIRS:
            continue
        if entry.is_dir():
            yield from _source_files(entry)
        elif entry.suffix in _SOURCE_EXT:
            yield entry


def used_keys(src: str | Path, patterns: list[str]) -> set[str]:
    """Collect translation keys referenced in source files under `src`, skipping vendored trees."""
    regexes = [re.compile(p) for p in patterns]
    found: set[str] = set()
    for f in _source_files(Path(src)):
        text = f.read_text(encoding="utf-8", errors="replace")
        for regex in regexes:
            found.update(regex.findall(text))
    return found


def find_unused(
    path: str,
    src: str,
    patterns: list[str] | None = None,
    default_ns: str = "common",
    ignore: str = "",
) -> dict[str, Any]:
    """Report keys the code asks for that nothing declares, and declared keys nothing asks for."""
    catalog = load_catalog(path)
    if not catalog:
        return {"error": "no locales found", "path": str(path)}
    base_name = pick_base(catalog, "")
    declared = set(catalog[base_name])
    namespaced = layout(path) == "namespaced"
    exempt = {item.strip() for item in ignore.split(",") if item.strip()}

    used = {
        f"{default_ns}:{key}" if namespaced and ":" not in key else key
        for key in used_keys(src, patterns or _DEFAULT_PATTERNS)
    }
    declared_roots = {base_key(key) for key in declared}
    asked_roots = {base_key(key) for key in used}

    missing = sorted(
        key for key in used if base_key(key) not in declared_roots and key not in exempt
    )
    dead = sorted(
        key
        for key in declared
        if base_key(key) not in asked_roots
        and key not in exempt
        and not (namespaced and key.startswith(f"{default_ns}:"))
    )
    return {
        "base": base_name,
        "layout": layout(path),
        "default_namespace": default_ns if namespaced else None,
        "declared": len(declared),
        "used": len(used),
        "used_not_declared": missing[:200],
        "declared_not_used": dead[:200],
        "note": "A plural resolves through any of its forms, and an unprefixed key resolves to the "
        "default namespace, which is exempt from the dead-key report because it is the catalogue. "
        "Pass `ignore` for keys only a variable names (enum values).",
    }
