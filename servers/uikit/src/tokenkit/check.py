"""Measure a theme's pairs against the WCAG contrast thresholds."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .color import Color, contrast, over, parse, to_hex
from .pairs import find_pairs
from .tokens import read_tokens

AA_TEXT = 4.5
AA_LARGE = 3.0
AAA_TEXT = 7.0
_BACKDROP = ("background", "bg", "surface", "base", "canvas", "body")
_UI_HINTS = ("border", "outline", "divider", "ring", "separator", "rule", "stroke")
_DECORATIVE = ("logo", "shadow", "scrollbar", "hover", "overlay", "backdrop", "glow", "wash")


def _level(front: str, back: str, large: bool) -> tuple[float, str]:
    if any(hint in front for hint in _UI_HINTS):
        return AA_LARGE, "ui"
    return (AA_LARGE, "large text") if large else (AA_TEXT, "text")


def _backdrop(colors: dict[str, Color]) -> Color:
    for name in _BACKDROP:
        if name in colors:
            return over(colors[name], (255.0, 255.0, 255.0, 1.0))
    return (255.0, 255.0, 255.0, 1.0)


def measure(front: str, back: str, colors: dict[str, Color], large: bool = False) -> dict[str, Any]:
    """One pair: its ratio, the threshold that applies and whether it clears it."""
    base = _backdrop(colors)
    behind = over(colors[back], base)
    ratio = contrast(colors[front], behind)
    threshold, kind = _level(front, back, large)
    return {
        "front": front,
        "back": back,
        "front_color": to_hex(colors[front]),
        "back_color": to_hex(colors[back]),
        "ratio": round(ratio, 2),
        "required": threshold,
        "kind": kind,
        "passes": ratio >= threshold,
        "passes_aaa": ratio >= AAA_TEXT,
    }


def check_contrast(
    path: str | Path,
    src: str | Path | None = None,
    prefix: str = "",
    include_decorative: bool = False,
) -> dict[str, Any]:
    """Read a theme, find the pairs its code really uses and measure every one."""
    read = read_tokens(path)
    themes = read["themes"]
    if not themes:
        return {"error": "no color tokens found", "path": str(path)}

    report: dict[str, Any] = {}
    for name, colors in themes.items():
        pairs = find_pairs(colors, src, prefix)
        rows = []
        for pair in pairs:
            front, back = pair["front"], pair["back"]
            if not include_decorative and any(
                hint in front or hint in back for hint in _DECORATIVE
            ):
                continue
            row = measure(front, back, colors)
            row["source"] = pair.get("source", "")
            row["uses"] = pair.get("uses", 0)
            row["where"] = pair.get("where", [])
            if pair.get("variant"):
                row["variant"] = pair["variant"]
            rows.append(row)
        rows.sort(key=lambda item: item["ratio"])
        failed = [row for row in rows if not row["passes"]]
        report[name] = {
            "source": read["sources"].get(name, ""),
            "tokens": len(colors),
            "pairs": len(rows),
            "failing": len(failed),
            "ok": not failed,
            "failures": failed[:100],
            "measured": rows[:200],
        }
    return {
        "themes": sorted(report),
        "all_pass": all(entry["ok"] for entry in report.values()),
        "report": report,
        "note": "Pairs come from the tokens' own naming (on-* sits on *), from variant maps and "
        "from classes used together, never from a guessed table. Thresholds are WCAG 2.2: 4.5 "
        "for text, 3.0 for large text and for anything that reads as a border or outline. "
        "Decorative tokens (logo, shadow, scrollbar, hover) are left out unless asked for.",
    }


def contrast_of(front: str, back: str) -> dict[str, Any]:
    """Contrast between two colors given directly, in any CSS notation."""
    first, second = parse(front), parse(back)
    if first is None or second is None:
        return {"error": "could not parse a color", "front": front, "back": back}
    behind = over(second, (255.0, 255.0, 255.0, 1.0))
    ratio = contrast(first, behind)
    return {
        "front": to_hex(first),
        "back": to_hex(second),
        "ratio": round(ratio, 2),
        "aa_text": ratio >= AA_TEXT,
        "aa_large": ratio >= AA_LARGE,
        "aaa_text": ratio >= AAA_TEXT,
    }
