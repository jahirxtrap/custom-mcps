"""Directional and spherical shading with a consistent top-left light source."""
from __future__ import annotations

import math
from collections.abc import Iterable

from .color import Ramp, pick
from .grid import Color, Coord, Grid


def shade(
    grid: Grid,
    region: Iterable[Coord],
    ramp: Ramp,
    ambient: float = 0.42,
    top: float = 0.40,
    left: float = 0.24,
) -> None:
    """Fill a region with top-left directional light plus edge accenting."""
    pixels = set(region)
    if not pixels:
        return
    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    width = max(1, x1 - x0)
    height = max(1, y1 - y0)
    for x, y in pixels:
        brightness = ambient + top * (1 - (y - y0) / height) + left * (1 - (x - x0) / width)
        if (x, y + 1) not in pixels:
            brightness -= 0.16
        if (x + 1, y) not in pixels:
            brightness -= 0.08
        if (x, y - 1) not in pixels:
            brightness += 0.08
        if (x - 1, y) not in pixels:
            brightness += 0.05
        grid.put(x, y, pick(ramp, brightness))


def sphere(
    grid: Grid,
    cx: float,
    cy: float,
    radius: float,
    ramp: Ramp,
    light: tuple[float, float, float] = (-0.5, -0.55, 0.67),
    ambient: float = 0.32,
    region: Iterable[Coord] | None = None,
) -> None:
    """Shade a region as a lit sphere (gems, coins, liquid bulbs)."""
    norm = math.sqrt(sum(c * c for c in light)) or 1.0
    lx, ly, lz = (light[0] / norm, light[1] / norm, light[2] / norm)
    cells = set(region) if region is not None else {
        (x, y)
        for y in range(grid.size)
        for x in range(grid.size)
        if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= radius
    }
    for x, y in cells:
        dx = (x + 0.5 - cx) / radius
        dy = (y + 0.5 - cy) / radius
        nz2 = 1 - dx * dx - dy * dy
        nz = math.sqrt(nz2) if nz2 > 0 else 0.0
        lit = dx * lx + dy * ly + nz * lz
        brightness = ambient + (1 - ambient) * (lit if lit > 0 else 0)
        grid.put(x, y, pick(ramp, brightness))


def inner_rim(grid: Grid, region: Iterable[Coord], color: Color) -> None:
    """Darken the inside border of a region (definition without an outer outline)."""
    pixels = set(region)
    for x, y in pixels:
        if any((x + dx, y + dy) not in pixels for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            grid.put(x, y, color)
