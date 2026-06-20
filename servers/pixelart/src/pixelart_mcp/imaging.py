"""PNG <-> grid conversion, palette extraction and rule validation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image
from pixellib import Grid, color_limit, hex_to_rgb

_NEIGHBORS = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0)]


def _hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def image_to_payload(path: str | Path, fmt: str = "hex") -> dict[str, Any]:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()
    if fmt == "index":
        order: list[str] = []
        symbols: dict[str, str] = {}
        grid: list[list[str]] = []
        for y in range(h):
            row: list[str] = []
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    row.append(".")
                    continue
                key = _hex(r, g, b)
                if key not in symbols:
                    symbols[key] = chr(ord("a") + len(order)) if len(order) < 26 else str(len(order))
                    order.append(key)
                row.append(symbols[key])
            grid.append(row)
        return {"size": w, "format": "index", "palette": {v: k for k, v in symbols.items()}, "grid": grid}
    grid_hex: list[list[str | None]] = []
    for y in range(h):
        row_hex: list[str | None] = []
        for x in range(w):
            r, g, b, a = px[x, y]
            row_hex.append(None if a == 0 else _hex(r, g, b))
        grid_hex.append(row_hex)
    return {"size": w, "format": "hex", "grid": grid_hex}


def payload_to_grid(rows: list[list[Any]], palette: dict[str, str] | None, size: int) -> Grid:
    grid = Grid(size)
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell in (None, ".", ""):
                continue
            value = palette[cell] if palette and cell in palette else cell
            grid.put(x, y, hex_to_rgb(value))
    return grid


def count_colors(path: str | Path) -> dict[str, int]:
    img = Image.open(path).convert("RGBA")
    px = img.load()
    w, h = img.size
    counts: dict[str, int] = {}
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 255:
                key = _hex(r, g, b)
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def validate(path: str | Path) -> dict[str, Any]:
    """Check a PNG against the embedded pixel-art rules; returns a structured report."""
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()
    solid: set[tuple[int, int]] = set()
    colors: set[str] = set()
    antialiased = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if 0 < a < 255:
                antialiased += 1
                continue
            solid.add((x, y))
            colors.add(_hex(r, g, b))

    edges = [
        name
        for name, hit in (
            ("top", any((x, 0) in solid for x in range(w))),
            ("bottom", any((x, h - 1) in solid for x in range(w))),
            ("left", any((0, y) in solid for y in range(h))),
            ("right", any((w - 1, y) in solid for y in range(h))),
        )
        if hit
    ]
    floating = [
        list(p)
        for p in solid
        if not any((p[0] + dx, p[1] + dy) in solid for dx, dy in _NEIGHBORS)
    ]
    lo, hi = color_limit(max(w, h))

    issues: list[str] = []
    if antialiased:
        issues.append(
            f"{antialiased} semi-transparent (anti-aliased) pixels; pixel art should be opaque or transparent"
        )
    if edges:
        issues.append(f"content touches canvas edge(s): {', '.join(edges)}; an outline cannot draw past the border")
    if floating:
        issues.append(f"{len(floating)} isolated pixel(s) with no neighbor; likely floating/unbordered")
    if len(colors) > hi:
        issues.append(f"{len(colors)} colors exceeds the {hi}-color budget for {max(w, h)}px sprites")

    return {
        "size": [w, h],
        "colors": len(colors),
        "color_budget": [lo, hi],
        "antialiased_pixels": antialiased,
        "edge_contact": edges,
        "floating_pixels": floating[:32],
        "floating_count": len(floating),
        "ok": not issues,
        "issues": issues,
    }
