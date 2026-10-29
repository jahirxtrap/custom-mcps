"""Read a design theme from the shapes it ships in: a TS object, a pack JSON or CSS variables."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .color import Color, parse

_ENTRY = re.compile(r"""["']?([\w-]+)["']?\s*:\s*["']([^"']+)["']""")
_CSS_VAR = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")
_THEME_KIND = re.compile(r"\b(light|dark)\b", re.IGNORECASE)
_SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist", "node_modules", "venv"}


def _colors(pairs: Any) -> dict[str, Color]:
    out: dict[str, Color] = {}
    for name, raw in pairs:
        color = parse(raw)
        if color is not None:
            out[name] = color
    return out


def _from_json(data: Any, label: str) -> dict[str, dict[str, Color]]:
    if isinstance(data, dict) and isinstance(data.get("colors"), dict):
        kind = str(data.get("kind") or data.get("name") or label)
        colors = _colors(data["colors"].items())
        accent = data.get("accent")
        if isinstance(accent, str) and parse(accent):
            colors.setdefault("accent", parse(accent))  # type: ignore[arg-type]
        return {kind: colors} if colors else {}
    out: dict[str, dict[str, Color]] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                colors = _colors(
                    (name, raw) for name, raw in value.items() if isinstance(raw, str)
                )
                if colors:
                    out[str(key)] = colors
    return out


def _from_source(text: str, label: str) -> dict[str, dict[str, Color]]:
    out: dict[str, dict[str, Color]] = {}
    for found in re.finditer(r"\b(\w+)\s*:\s*\{", text):
        name = found.group(1)
        if not _THEME_KIND.fullmatch(name) and name not in ("colors", "palette", "tokens"):
            continue
        depth, index = 1, found.end()
        while index < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[index], 0)
            index += 1
        colors = _colors(_ENTRY.findall(text[found.end():index]))
        if colors:
            out[name] = colors
    if out:
        return out
    colors = _colors(_ENTRY.findall(text))
    return {label: colors} if colors else {}


def _from_css(text: str, label: str) -> dict[str, dict[str, Color]]:
    out: dict[str, dict[str, Color]] = {}
    for block in re.finditer(r"([^{};]*)\{([^{}]*)\}", text):
        selector, body = block.group(1).strip(), block.group(2)
        colors = _colors(_CSS_VAR.findall(body))
        if not colors:
            continue
        kind = _THEME_KIND.search(selector)
        name = kind.group(1).lower() if kind else (label if not out else f"{label}-{len(out)}")
        out.setdefault(name, {}).update(colors)
    return out


def read_theme(path: str | Path) -> dict[str, dict[str, Color]]:
    """Theme name -> token name -> color, from one JSON, CSS or source file."""
    file = Path(path)
    text = file.read_text(encoding="utf-8", errors="replace")
    label = file.stem
    if file.suffix == ".json":
        try:
            return _from_json(json.loads(text), label)
        except json.JSONDecodeError:
            return {}
    if file.suffix == ".css":
        return _from_css(text, label)
    return _from_source(text, label)


def read_tokens(path: str | Path) -> dict[str, Any]:
    """Collect every theme under `path`, whether it is one file or a folder of them."""
    base = Path(path)
    files = [base] if base.is_file() else sorted(
        f for f in base.rglob("*")
        if f.is_file()
        and f.suffix in (".json", ".css", ".ts", ".tsx", ".js", ".kt")
        and not any(part in _SKIP_DIRS for part in f.parts)
    )
    themes: dict[str, dict[str, Color]] = {}
    sources: dict[str, str] = {}
    for file in files:
        for name, colors in read_theme(file).items():
            if len(colors) < 3 and base.is_dir():
                continue
            key = name if name not in themes else f"{file.stem}:{name}"
            themes[key] = colors
            sources[key] = str(file if base.is_file() else file.relative_to(base))
    return {"themes": themes, "sources": sources}
