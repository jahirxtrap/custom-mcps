"""pixelart MCP server: draw, inspect and verify pixel art by data. Engine-agnostic."""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from PIL import Image as PILImage
from pixellib import (
    build_ramp,
    color_limit,
    guide as guide_text,
    hex_to_rgb,
    montage,
    reference_brief,
    rgb_to_hex,
)

from .builder import build_from_spec
from .imaging import count_colors, image_to_payload, payload_to_grid, validate

mcp = FastMCP(name="pixelart")


def _scratch(prefix: str, out_dir: str = "") -> Path:
    base = Path(out_dir) if out_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{prefix}_{uuid.uuid4().hex[:8]}.png"


def _result(native: Path, out_dir: str, scale: int) -> list[Any]:
    preview_img = montage([native], scale=scale)
    preview_path = _scratch("preview", out_dir)
    preview_img.save(preview_path)
    width, height = PILImage.open(native).size
    colors = len(count_colors(native))
    summary = (
        f"path={native} mime=image/png size={width}x{height} colors={colors} "
        f"preview={preview_path}"
    )
    return [Image(path=str(preview_path)), summary]


@mcp.tool
def pixel_guide(size: int = 0) -> str:
    """Return the embedded pixel-art principles (silhouette, hue-shift, top-left light,
    outline + gotchas, per-size color budgets). Pass size (8/16/32/64) to tune the budget."""
    return guide_text(size)


@mcp.tool(output_schema=None)
def render_sprite(spec: str, out_dir: str = "", scale: int = 0) -> list[Any]:
    """Render a sprite from a declarative JSON spec and return an upscaled preview image
    plus a 'path=' summary line. Spec: {size, layers:[{shape, fill}], outline?, symmetry?, out?}.
    shape = {rows:[...]} | {rect:[x0,y0,x1,y1]} | {disc:[cx,cy,r]} | {pixels:[[x,y]...]} | a list (union).
    fill = {color:'#rrggbb'} | {ramp:{base,kind:art|skin|hair|gray,steps}, shade:{ambient,top,left}|{sphere:{cx,cy,r}}}.
    The native PNG goes to spec.out or a temp file; the preview goes to out_dir or temp."""
    data = json.loads(spec)
    grid = build_from_spec(data)
    out = data.get("out")
    native = Path(out) if out else _scratch("sprite", out_dir)
    grid.save(native)
    return _result(native, out_dir, scale)


@mcp.tool(output_schema=None)
def from_grid(grid: str, size: int, out: str, palette: str = "", out_dir: str = "", scale: int = 0) -> list[Any]:
    """Build a native PNG from an explicit 2D matrix. Cells are '#rrggbb'/null (hex), or symbols
    plus a palette map {symbol:'#rrggbb'}. Returns the upscaled preview + a 'path=' line."""
    rows = json.loads(grid)
    pal = json.loads(palette) if palette else None
    built = payload_to_grid(rows, pal, size)
    native = Path(out)
    built.save(native)
    return _result(native, out_dir, scale)


@mcp.tool
def to_grid(path: str, fmt: str = "hex") -> str:
    """Dump a PNG as a 2D matrix. fmt='hex' -> rows of '#rrggbb'/null; fmt='index' -> rows of
    symbols plus a {symbol:'#rrggbb'} palette. Use it to read a reference or edit an existing PNG."""
    return json.dumps(image_to_payload(path, fmt))


@mcp.tool(output_schema=None)
def preview(paths: list[str], scale: int = 0, out_dir: str = "") -> list[Any]:
    """Upscale one or more PNGs with NEAREST on a checkerboard for inspection (never blurs).
    Returns the montage image + a 'path=' line. scale=0 auto-scales to ~512px."""
    image = montage(list(paths), scale=scale)
    path = _scratch("montage", out_dir)
    image.save(path)
    return [Image(path=str(path)), f"path={path} mime=image/png size={image.width}x{image.height} sources={len(paths)}"]


@mcp.tool
def palette(path: str = "", base: str = "", kind: str = "art", steps: int = 5) -> str:
    """Inspect or generate a palette. With path: extract distinct colors, counts, and check the
    per-size budget. With base ('#rrggbb'): generate a ramp (kind=art|skin|hair|gray)."""
    if base:
        colors = build_ramp(hex_to_rgb(base), kind, steps)
        return json.dumps({"kind": kind, "steps": steps, "ramp": [rgb_to_hex(c) for c in colors]})
    if path:
        counts = count_colors(path)
        width, height = PILImage.open(path).size
        lo, hi = color_limit(max(width, height))
        return json.dumps(
            {
                "size": [width, height],
                "count": len(counts),
                "budget": [lo, hi],
                "within_budget": len(counts) <= hi,
                "colors": counts,
            }
        )
    raise ValueError("provide 'path' to inspect or 'base' to generate")


@mcp.tool
def search_reference(subject: str, size: int = 0, kind: str = "") -> str:
    """Build a reference brief before drawing (optional, but it makes results much better). Returns
    targeted web-search queries for `subject` (realistic photos and similar pixel arts), what to
    extract (silhouette, proportions, palette, light) and how to translate it to pixels at `size`.
    kind = character/creature/item/tile/environment. It does NOT fetch images: run the queries with
    your own web search/fetch, read a downloaded reference with to_grid/palette, then render_sprite."""
    return json.dumps(reference_brief(subject, size, kind))


@mcp.tool
def check(path: str) -> str:
    """Validate a PNG against the pixel-art rules: anti-aliasing (semi-transparent pixels),
    content touching the canvas edge, isolated/floating pixels, and the per-size color budget."""
    return json.dumps(validate(path))


def main() -> None:
    mcp.run()
