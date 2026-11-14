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
_TOKEN_DIRS = {"theme", "themes", "tokens", "palette"}
_SKIP_DIRS = {
    ".cache", ".expo", ".git", ".gradle", ".idea", ".mypy_cache", ".next", ".nuxt",
    ".pytest_cache", ".ruff_cache", ".svelte-kit", ".turbo", ".venv", "__pycache__", "build",
    "coverage", "dist", "generated", "node_modules", "out", "site-packages", "target",
    "third_party", "vendor", "venv",
}
_VENDORED_PATHS = ("components/ui/", "components/rnr/", "src/generated/")


def _fragments(exclude: str | None) -> list[str]:
    extra = [item.strip().replace("\\", "/") for item in (exclude or "").split(",")]
    return list(_VENDORED_PATHS) + [item for item in extra if item]


def _vendored(path: Path, fragments: list[str] | None = None) -> bool:
    if any(part in _SKIP_DIRS for part in path.parts):
        return True
    posix = path.as_posix()
    return any(fragment in posix for fragment in (fragments or _VENDORED_PATHS))


def _is_token_file(path: Path, allow_list: list[str]) -> bool:
    return path.parent.name.lower() in _TOKEN_DIRS or any(
        token in path.name.lower() for token in allow_list
    )


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


def find_hardcoded(path: str, allow: list[str] | None = None, exclude: str = "") -> dict[str, Any]:
    """Flag hardcoded colors (hex, Color(0xFF...)), sizes (px/rem/.dp/.sp) and raw Tailwind classes."""
    base = Path(path)
    allow_list = [a.lower() for a in (list(_DEFAULT_ALLOW) + (allow or []))]
    fragments = _fragments(exclude)
    files = base.rglob("*") if base.is_dir() else [base]
    hits: list[dict[str, Any]] = []
    scanned = 0
    for f in files:
        if not f.is_file() or f.suffix not in _CODE_EXT or _vendored(f, fragments):
            continue
        if _is_token_file(f, allow_list):
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
        "excluded": fragments,
        "note": "Colors (any stack) and web px/rem sizes. Compose .dp/.sp spacing is idiomatic and "
        "intentionally not flagged. Skipped: comments, token files (by name or by a theme/tokens/"
        "palette parent folder) and the vendored paths in `excluded` -- pass more through `exclude`.",
    }


_DP = re.compile(r"\b(\d+(?:\.\d+)?)\.dp\b")
_SP = re.compile(r"\b(\d+(?:\.\d+)?)\.sp\b")
_CSS_FONT = re.compile(r"font-size\s*:\s*(\d+(?:\.\d+)?)(?:px|rem)", re.IGNORECASE)
_TW_ARBITRARY = re.compile(r"\b[a-z]+-\[(\d+(?:\.\d+)?)(?:px|rem)\]")
_TW_SPACE = re.compile(
    r"\b(?:gap-x|gap-y|space-x|space-y|gap|px|py|pt|pb|pl|pr|ps|pe|mx|my|mt|mb|ml|mr|ms|me|p|m)"
    r"-(\d+(?:\.\d+)?|[a-z]{1,4})\b"
)
_TW_TEXT = re.compile(r"\btext-(xs|sm|base|lg|xl|[2-9]xl)\b")
_TW_NOT_SCALE = {"auto", "full", "px", "min", "max", "fit"}
_SCALE_SKIP = ("dimens", "spacing", "type.", "typography", "theme", "tokens", "palette")


def _token_report(counter: Counter[str], rare: int) -> dict[str, Any]:
    values = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return {
        "distinct": len(counter),
        "total": sum(counter.values()),
        "values": [[v, c] for v, c in values[:40]],
        "outliers": sorted(v for v, c in counter.items() if c <= rare)[:40],
    }


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


def find_inconsistent(path: str, rare: int = 2, grid: int = 4, exclude: str = "") -> dict[str, Any]:
    """Measure the spacing and text-size scales actually in use and flag what breaks consistency:
    rare one-off values (used <= `rare` times), values off a base `grid` (default 4), and Tailwind
    arbitrary values. Sources: Compose .dp (spacing) / .sp (text), CSS font-size, Tailwind and
    NativeWind utility classes (p/m/gap/space and text-*), and `-[Npx]` classes."""
    base = Path(path)
    spacing: Counter[str] = Counter()
    text: Counter[str] = Counter()
    utility: Counter[str] = Counter()
    utility_text: Counter[str] = Counter()
    arbitrary: list[dict[str, Any]] = []
    fragments = _fragments(exclude)
    scanned = 0
    files = base.rglob("*") if base.is_dir() else [base]
    for f in files:
        if not f.is_file() or f.suffix not in _CODE_EXT or _vendored(f, fragments):
            continue
        if any(token in f.name.lower() for token in _SCALE_SKIP):
            continue
        scanned += 1
        rel = str(f.relative_to(base)) if base.is_dir() else str(f)
        for number, line in _code_lines(f.read_text(encoding="utf-8", errors="replace")):
            spacing.update(_DP.findall(line))
            text.update(_SP.findall(line))
            text.update(_CSS_FONT.findall(line))
            utility.update(v for v in _TW_SPACE.findall(line) if v not in _TW_NOT_SCALE)
            utility_text.update(_TW_TEXT.findall(line))
            if _TW_ARBITRARY.search(line):
                arbitrary.append({"file": rel, "line": number, "text": line.strip()[:120]})
    return {
        "scanned_files": scanned,
        "spacing": _scale_report(spacing, rare, grid),
        "text_size": _scale_report(text, rare, grid),
        "utility_spacing": _token_report(utility, rare),
        "utility_text": _token_report(utility_text, rare),
        "arbitrary": arbitrary[:100],
        "excluded": fragments,
        "note": "Scale snapshot, not errors. spacing/text_size are numeric scales (Compose, CSS) "
        "and carry the grid check; utility_* are the Tailwind/NativeWind classes in use, where the "
        "tokens ARE the scale so only rare one-offs matter. An arbitrary `-[Npx]` is worth routing "
        "back to a token only when a token already covers that value.",
    }


_FQN = re.compile(r"\b(?:[a-z][A-Za-z0-9_]*\.){2,}[A-Z][A-Za-z0-9_]*")
_IMPORT_JAVA = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)\s*;")
_IMPORT_KT = re.compile(r"^\s*import\s+([\w.]+)(?:\s+as\s+(\w+))?\s*$")
_IMPORT_TS = re.compile(r"^\s*import\s+(.+?)\s+from\s+")
_IDENT = re.compile(r"[A-Za-z_]\w*")
_JSON_INDENT = re.compile(r"^([ \t]+)\S", re.MULTILINE)
_IMPLICIT_KT = {
    "getValue", "setValue", "provideDelegate", "plus", "minus", "times", "div", "rem",
    "plusAssign", "minusAssign", "timesAssign", "divAssign", "remAssign", "inc", "dec",
    "unaryPlus", "unaryMinus", "not", "rangeTo", "rangeUntil", "contains", "invoke", "iterator",
    "compareTo", "component1", "component2", "component3", "component4", "component5",
}


def _ts_names(clause: str) -> list[str]:
    clause = re.sub(r"^type\s+", "", clause.strip())
    names: list[str] = []
    brace = re.search(r"\{([^}]*)\}", clause)
    if brace:
        for part in brace.group(1).split(","):
            item = re.sub(r"^type\s+", "", part.strip()).split(" as ")[-1].strip()
            if item:
                names.append(item)
        clause = clause[: brace.start()] + clause[brace.end():]
    star = re.search(r"\*\s+as\s+(\w+)", clause)
    if star:
        names.append(star.group(1))
        clause = clause[: star.start()]
    default = clause.replace(",", " ").strip()
    if default and re.fullmatch(r"\w+", default):
        names.append(default)
    return [n for n in names if n and n != "type"]


def _imported_names(line: str, suffix: str) -> list[str]:
    if suffix == ".java":
        match = _IMPORT_JAVA.match(line)
        return [] if not match or match.group(1).endswith(".*") else [match.group(1).rsplit(".", 1)[-1]]
    if suffix in (".kt", ".kts"):
        match = _IMPORT_KT.match(line)
        if not match or match.group(1).endswith(".*"):
            return []
        return [match.group(2) or match.group(1).rsplit(".", 1)[-1]]
    if suffix in (".ts", ".tsx", ".js", ".jsx"):
        match = _IMPORT_TS.match(line)
        return _ts_names(match.group(1)) if match else []
    return []


def find_format(path: str, exclude: str = "") -> dict[str, Any]:
    """Flag AI-typical format breaks formatters miss: inline fully-qualified class names (Java/Kotlin),
    unused imports (Java/Kotlin/TS), tab+space mixed indentation, and JSON files whose indent style
    differs from the rest of the tree."""
    base = Path(path)
    inline_fqn: list[dict[str, Any]] = []
    unused: list[dict[str, Any]] = []
    mixed_indent: list[str] = []
    json_styles: Counter[str] = Counter()
    json_files: list[dict[str, Any]] = []
    code_scanned = json_scanned = 0
    fragments = _fragments(exclude)
    for f in (base.rglob("*") if base.is_dir() else [base]):
        if not f.is_file() or _vendored(f, fragments):
            continue
        rel = str(f.relative_to(base)) if base.is_dir() else str(f)
        text = f.read_text(encoding="utf-8", errors="replace")
        if f.suffix in _CODE_EXT:
            code_scanned += 1
            lines = text.splitlines()
            if any(ln.startswith("\t") for ln in lines) and any(ln.startswith("  ") for ln in lines):
                mixed_indent.append(rel)
            imports: dict[str, int] = {}
            used: set[str] = set()
            for number, line in enumerate(lines, 1):
                names = _imported_names(line, f.suffix)
                if names:
                    for name in names:
                        imports[name] = number
                else:
                    used.update(_IDENT.findall(line))
            implicit = _IMPLICIT_KT if f.suffix in (".kt", ".kts") else set()
            unused += [
                {"file": rel, "line": n, "name": k}
                for k, n in imports.items()
                if k not in used and k not in implicit
            ]
            if f.suffix in (".java", ".kt", ".kts"):
                for number, line in _code_lines(text):
                    if line.strip().startswith(("import ", "package ")):
                        continue
                    inline_fqn += [{"file": rel, "line": number, "match": m.group(0)} for m in _FQN.finditer(line)]
        elif f.suffix == ".json":
            json_scanned += 1
            match = _JSON_INDENT.search(text)
            style = ("tab" if "\t" in match.group(1) else f"{len(match.group(1))}sp") if match else "flat"
            json_styles[style] += 1
            json_files.append({"file": rel, "indent": style, "trailing_newline": text.endswith("\n")})
    shaped = [s for s in json_styles if s != "flat"]
    majority = max(shaped, key=lambda s: json_styles[s]) if shaped else None
    outliers = [jf for jf in json_files if majority and jf["indent"] not in ("flat", majority)]
    return {
        "code_scanned": code_scanned,
        "json_scanned": json_scanned,
        "inline_fqn": inline_fqn[:100],
        "inline_fqn_count": len(inline_fqn),
        "unused_imports": unused[:100],
        "unused_import_count": len(unused),
        "mixed_indent": mixed_indent[:100],
        "json_style": {"indents": dict(json_styles), "majority": majority, "outliers": outliers[:60]},
        "note": "Heuristic. inline_fqn = a package.path.Class used inline (import it). unused_imports "
        "skips names that appear anywhere else (incl. comments), so they are strong candidates. "
        "json_style flags files whose indent differs from the tree majority. Vendored dirs skipped.",
    }


def find_duplication(path: str, window: int = 6, exclude: str = "") -> dict[str, Any]:
    """Find identical normalized line blocks (~window lines) repeated across the code (DRY candidates)."""
    base = Path(path)
    fragments = _fragments(exclude)
    files = [
        f
        for f in (base.rglob("*") if base.is_dir() else [base])
        if f.is_file() and f.suffix in _CODE_EXT and not _vendored(f, fragments)
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
