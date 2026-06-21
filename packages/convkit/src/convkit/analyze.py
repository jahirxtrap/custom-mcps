"""Static checks: multi-stack hardcoded colors/sizes and duplicated line blocks."""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any

_COLOR_LITERAL = re.compile(r"Color\(\s*0x[0-9a-fA-F]{6,8}|\b0x[0-9a-fA-F]{8}\b")
_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_SIZE = re.compile(r"[\"'\[]\s*\d+(?:\.\d+)?(?:px|rem)\b")
_TAILWIND = re.compile(
    r"\b(?:bg|text|border|ring|from|via|to|fill|stroke|divide|outline)-"
    r"(?:red|blue|green|yellow|gray|grey|slate|zinc|neutral|stone|orange|amber|lime|emerald|"
    r"teal|cyan|sky|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b"
)

_CODE_EXT = (".java", ".kt", ".kts", ".ts", ".tsx", ".js", ".jsx", ".gd", ".py")
_DEFAULT_ALLOW = ("themes.", "theme.", "palette.", "accents.", "colors.", "tokens.", "tailwind.config")
_SKIP_DIRS = {
    ".venv", "venv", "node_modules", ".git", "__pycache__", "build", "dist", ".gradle",
    "target", ".idea", ".next", "out", ".ruff_cache", ".pytest_cache",
}


def _vendored(path: Path) -> bool:
    return any(part in _SKIP_DIRS for part in path.parts)


def _code_lines(text: str):
    """Yield (number, line) for code lines, skipping line comments and docstrings/block comments."""
    in_doc: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if in_doc is not None:
            if in_doc in stripped:
                in_doc = None
            continue
        if stripped.startswith(("#", "//", "*", "/*")):
            continue
        if stripped.startswith(('"""', "'''")):
            quote = stripped[:3]
            if stripped.count(quote) < 2:
                in_doc = quote
            continue
        yield number, line


def find_hardcoded(path: str, allow: list[str] | None = None) -> dict[str, Any]:
    """Flag hardcoded colors (hex, Color(0xFF...)), sizes (px/rem/.dp/.sp) and raw Tailwind classes."""
    base = Path(path)
    allow_list = [a.lower() for a in (list(_DEFAULT_ALLOW) + (allow or []))]
    files = base.rglob("*") if base.is_dir() else [base]
    hits: list[dict[str, Any]] = []
    scanned = 0
    for f in files:
        if not f.is_file() or f.suffix not in _CODE_EXT or _vendored(f):
            continue
        if any(token in f.name.lower() for token in allow_list):
            continue
        scanned += 1
        rel = str(f.relative_to(base)) if base.is_dir() else str(f)
        for number, line in _code_lines(f.read_text(encoding="utf-8", errors="replace")):
            kinds: list[str] = []
            if _COLOR_LITERAL.search(line):
                kinds.append("color-literal")
            elif _HEX.search(line):
                kinds.append("hex-color")
            if _SIZE.search(line):
                kinds.append("size")
            if _TAILWIND.search(line):
                kinds.append("raw-tailwind")
            if kinds:
                hits.append({"file": rel, "line": number, "kinds": kinds, "text": line.strip()[:120]})
    return {
        "scanned_files": scanned,
        "hit_count": len(hits),
        "hits": hits[:300],
        "note": "Colors (any stack) and web px/rem sizes. Compose .dp/.sp spacing is idiomatic "
        "and intentionally not flagged. Token files (themes/palette/...) and comments are skipped.",
    }


_DP = re.compile(r"\b(\d+(?:\.\d+)?)\.dp\b")
_SP = re.compile(r"\b(\d+(?:\.\d+)?)\.sp\b")
_CSS_FONT = re.compile(r"font-size\s*:\s*(\d+(?:\.\d+)?)(?:px|rem)", re.IGNORECASE)
_TW_ARBITRARY = re.compile(r"\b[a-z]+-\[(\d+(?:\.\d+)?)(?:px|rem)\]")
_SCALE_SKIP = ("dimens", "spacing", "type.", "typography", "theme", "tokens", "palette")


def _scale_report(counter: Counter[str], rare: int, grid: int) -> dict[str, Any]:
    values = sorted(counter.items(), key=lambda kv: (-kv[1], float(kv[0])))
    outliers = sorted((v for v, c in counter.items() if c <= rare), key=float)
    off_grid = sorted(
        (v for v in counter if float(v).is_integer() and float(v) != 0 and int(float(v)) % grid),
        key=float,
    )
    return {
        "distinct": len(counter),
        "total": sum(counter.values()),
        "values": [[v, c] for v, c in values[:40]],
        "outliers": outliers[:40],
        "off_grid": off_grid[:40],
    }


def find_inconsistent(path: str, rare: int = 2, grid: int = 4) -> dict[str, Any]:
    """Measure the spacing and text-size scales actually in use and flag what breaks consistency:
    rare one-off values (used <= `rare` times), values off a base `grid` (default 4), and Tailwind
    arbitrary values. Sources: Compose .dp (spacing) / .sp (text), CSS font-size, `-[Npx]` classes."""
    base = Path(path)
    spacing: Counter[str] = Counter()
    text: Counter[str] = Counter()
    arbitrary: list[dict[str, Any]] = []
    scanned = 0
    files = base.rglob("*") if base.is_dir() else [base]
    for f in files:
        if not f.is_file() or f.suffix not in _CODE_EXT or _vendored(f):
            continue
        if any(token in f.name.lower() for token in _SCALE_SKIP):
            continue
        scanned += 1
        rel = str(f.relative_to(base)) if base.is_dir() else str(f)
        for number, line in _code_lines(f.read_text(encoding="utf-8", errors="replace")):
            spacing.update(_DP.findall(line))
            text.update(_SP.findall(line))
            text.update(_CSS_FONT.findall(line))
            if _TW_ARBITRARY.search(line):
                arbitrary.append({"file": rel, "line": number, "text": line.strip()[:120]})
    return {
        "scanned_files": scanned,
        "spacing": _scale_report(spacing, rare, grid),
        "text_size": _scale_report(text, rare, grid),
        "arbitrary": arbitrary[:100],
        "note": "Scale snapshot, not errors. Converge rare/off-grid spacing onto the base grid and "
        "inline text sizes onto one type scale; route Tailwind arbitrary values back to the scale. "
        "Token files (dimens/type/theme/...) are skipped.",
    }


def find_duplication(path: str, window: int = 6) -> dict[str, Any]:
    """Find identical normalized line blocks (~window lines) repeated across the code (DRY candidates)."""
    base = Path(path)
    files = [
        f
        for f in (base.rglob("*") if base.is_dir() else [base])
        if f.is_file() and f.suffix in _CODE_EXT and not _vendored(f)
    ]
    seen: dict[str, list[dict[str, Any]]] = {}
    for f in files:
        rel = str(f.relative_to(base)) if base.is_dir() else str(f)
        stripped = [ln.strip() for ln in f.read_text(encoding="utf-8", errors="replace").splitlines()]
        for index in range(len(stripped) - window + 1):
            block = stripped[index : index + window]
            if any(not line for line in block) or all(len(line) < 4 for line in block):
                continue
            digest = hashlib.sha1("\n".join(block).encode("utf-8")).hexdigest()
            seen.setdefault(digest, []).append({"file": rel, "line": index + 1, "sample": "\n".join(block)})
    blocks = []
    for occ in seen.values():
        if len(occ) > 1:
            blocks.append({
                "count": len(occ),
                "occurrences": [{"file": o["file"], "line": o["line"]} for o in occ],
                "sample": occ[0]["sample"][:200],
            })
    blocks.sort(key=lambda b: b["count"], reverse=True)
    return {
        "window": window,
        "duplicate_blocks": len(blocks),
        "blocks": blocks[:50],
        "note": "Heuristic: identical normalized line windows. Some are legit boilerplate; "
        "treat as candidates to unify.",
    }
