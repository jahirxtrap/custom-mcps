"""Declarative sprite spec -> Grid, applying the canonical pixel-art pipeline."""
from __future__ import annotations

from typing import Any

from pixellib import (
    Coord,
    Grid,
    build_ramp,
    disc,
    from_rows,
    hex_to_rgb,
    outline,
    rect,
    shade,
    sphere,
)


def resolve_shape(shape: Any, size: int) -> set[Coord]:
    if isinstance(shape, list):
        pixels: set[Coord] = set()
        for part in shape:
            pixels |= resolve_shape(part, size)
        return pixels
    if not isinstance(shape, dict):
        raise ValueError(f"invalid shape: {shape!r}")
    if "rows" in shape:
        return from_rows(shape["rows"])
    if "rect" in shape:
        return rect(*shape["rect"])
    if "disc" in shape:
        cx, cy, r = shape["disc"]
        return disc(cx, cy, r, size)
    if "pixels" in shape:
        return {(int(p[0]), int(p[1])) for p in shape["pixels"]}
    raise ValueError(f"shape needs one of rows/rect/disc/pixels: {shape!r}")


def apply_fill(grid: Grid, pixels: set[Coord], fill: dict[str, Any]) -> None:
    if "color" in fill:
        grid.paint(pixels, hex_to_rgb(fill["color"]))
        return
    ramp_spec = fill.get("ramp")
    if not ramp_spec:
        raise ValueError("fill needs 'color' or 'ramp'")
    colors = build_ramp(
        hex_to_rgb(ramp_spec.get("base", "#808080")),
        ramp_spec.get("kind", "art"),
        int(ramp_spec.get("steps", 5)),
    )
    sh = fill.get("shade") or {}
    if "sphere" in sh:
        s = sh["sphere"]
        sphere(grid, s["cx"], s["cy"], s["r"], colors, ambient=sh.get("ambient", 0.32), region=pixels)
    else:
        shade(
            grid,
            pixels,
            colors,
            ambient=sh.get("ambient", 0.42),
            top=sh.get("top", 0.40),
            left=sh.get("left", 0.24),
        )


def build_from_spec(spec: dict[str, Any]) -> Grid:
    """Build a sprite from layers (silhouette + fill), then symmetry, then outline."""
    size = int(spec.get("size", 16))
    grid = Grid(size)
    for layer in spec.get("layers", []):
        if "shape" not in layer:
            raise ValueError("each layer needs a 'shape'")
        pixels = resolve_shape(layer["shape"], size)
        apply_fill(grid, pixels, layer.get("fill", {"color": "#cccccc"}))
    if spec.get("symmetry"):
        grid.mirror_left_to_right()
    border = spec.get("outline")
    if border:
        outline(grid, hex_to_rgb(border))
    return grid
