"""uikit MCP server: interface guidance and contrast measured against the real code."""
from __future__ import annotations

import json

from fastmcp import FastMCP
from tokenkit import (
    check_contrast as _check_contrast,
    contrast_of as _contrast_of,
    design_guide as _design_guide,
    find_pairs as _find_pairs,
    read_tokens as _read_tokens,
)

mcp = FastMCP(
    name="uikit",
    instructions=(
        "Interface design measured, not argued: it reads a theme's design tokens, works out "
        "which colors the code actually puts together, and checks them against WCAG. "
        "Framework-agnostic and read-only.\n"
        "Tools: design_guide, read_tokens, find_pairs, check_contrast, contrast.\n"
        "Reach for it when building or reviewing a UI, adding a theme, or picking a color. "
        "Run check_contrast on the token file with the source folder, so the pairs come from "
        "variant maps and real class usage instead of a guessed table; read design_guide for "
        "the usability heuristics and the thresholds behind the numbers."
    ),
)


@mcp.tool
def design_guide(topic: str = "") -> str:
    """Return the embedded interface guidance, all of it or one topic: heuristics (Nielsen's
    ten) / laws (Fitts, Hick, Miller, Gestalt and the rest, each from its primary source) /
    contrast (what WCAG actually requires and what is exempt) / targets (pointer size, line
    length, line height, reflow, type and spacing scales) / tokens (naming and theming)."""
    return _design_guide(topic)


@mcp.tool
def read_tokens(path: str) -> str:
    """Read the design tokens under `path` and report the themes found, their token names and
    their colors normalized to hex. Understands the three shapes a theme ships in: a source
    object (TS/JS/Kotlin with `light: {...}` / `dark: {...}`), a theme JSON (a `colors` map,
    as a pack carries it) and CSS custom properties. Colors may be hex, rgb(), hsl(), oklch()
    or oklab(). `path` is one file or a folder to walk."""
    return json.dumps(_read_tokens(path))


@mcp.tool
def find_pairs(path: str, src: str = "", prefix: str = "") -> str:
    """Report which foreground/background token pairs are really in play, and how each was
    found: declared by the naming (an `on-x` token sits on `x`), tied together by a variant
    map (the variant that styles a surface and the one that styles its text), or simply used
    in the same class attribute. `src` is the source folder to read; `prefix` strips a token
    prefix such as `app` so `bg-app-surface` resolves to the token `surface`."""
    tokens = _read_tokens(path)["themes"]
    colors = next(iter(tokens.values()), {})
    return json.dumps(_find_pairs(colors, src or None, prefix))


@mcp.tool
def check_contrast(path: str, src: str = "", prefix: str = "", include_decorative: bool = False) -> str:
    """Measure every pair of every theme under `path` against WCAG 2.2: 4.5:1 for text, 3:1
    for large text and for anything that reads as a border or outline. Pass `src` (the source
    folder) so the pairs come from the code rather than a table, and `prefix` for a token
    prefix like `app`. A translucent color is composited onto what sits behind it before
    measuring. Decorative tokens (logo, shadow, scrollbar, hover) are skipped unless
    `include_decorative`. Returns the failures first, each with its ratio and where it is used."""
    return json.dumps(_check_contrast(path, src or None, prefix, include_decorative))


@mcp.tool
def contrast(front: str, back: str) -> str:
    """Contrast ratio between two colors given directly, in any CSS notation (#hex, rgb(),
    hsl(), oklch(), oklab()), with the AA and AAA verdicts. For a quick check while picking a
    color; use check_contrast to audit a whole theme."""
    return json.dumps(_contrast_of(front, back))


def main() -> None:
    mcp.run()
