"""Find translation keys used in source code, to spot missing or dead keys."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .parse import list_locales, load_locale, pick_base

_DEFAULT_PATTERNS = [r"""\bt\(\s*["']([^"']+)["']""", r"""\btr\(\s*["']([^"']+)["']"""]
_SOURCE_EXT = (".java", ".gd", ".ts", ".tsx", ".js", ".jsx", ".py", ".kt", ".mjs")


def used_keys(src: str | Path, patterns: list[str]) -> set[str]:
    """Collect translation keys referenced in source files under `src`."""
    regexes = [re.compile(p) for p in patterns]
    found: set[str] = set()
    base = Path(src)
    files = base.rglob("*") if base.is_dir() else [base]
    for f in files:
        if not f.is_file() or f.suffix not in _SOURCE_EXT:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for regex in regexes:
            found.update(regex.findall(text))
    return found


def find_unused(path: str, src: str, patterns: list[str] | None = None) -> dict[str, Any]:
    """Cross base keys with source usage: keys used-but-undefined and defined-but-unused."""
    locales = list_locales(path)
    if not locales:
        return {"error": "no .json locales found", "path": str(path)}
    base_name = pick_base(locales, "")
    defined = set(load_locale(locales[base_name]))
    used = used_keys(src, patterns or _DEFAULT_PATTERNS)
    return {
        "base": base_name,
        "defined": len(defined),
        "used": len(used),
        "used_not_defined": sorted(used - defined)[:200],
        "defined_not_used": sorted(defined - used)[:200],
        "note": "Keys built dynamically (string concatenation) may appear as false positives.",
    }
