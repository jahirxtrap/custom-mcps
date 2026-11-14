"""Pixel grid primitives: a square canvas of optional RGB cells, plus region builders."""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from pathlib import Path

from PIL import Image

Color = tuple[int, int, int]
Coord = tuple[int, int]


class Grid:
    """A square pixel canvas. Each cell is an RGB color or None (transparent)."""

    __slots__ = ("size", "_cells")

    def __init__(self, size: int) -> None:
        if size <= 0:
            raise ValueError("size must be positive")
        self.size = size
        self._cells: list[list[Color | None]] = [[None] * size for _ in range(size)]

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x: int, y: int) -> Color | None:
        return self._cells[y][x] if self.inside(x, y) else None

    def put(self, x: int, y: int, color: Color | None) -> None:
        if self.inside(x, y):
            self._cells[y][x] = color

    def paint(self, pixels: Iterable[Coord], color: Color) -> None:
        for x, y in pixels:
            self.put(x, y, color)

    def apply(self, mapping: Mapping[Coord, Color]) -> None:
        for (x, y), color in mapping.items():
            self.put(x, y, color)

    def filled(self) -> set[Coord]:
        return {
            (x, y)
            for y in range(self.size)
            for x in range(self.size)
            if self._cells[y][x] is not None
        }

    def bounds(self) -> tuple[int, int, int, int] | None:
        cells = self.filled()
        if not cells:
            return None
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        return min(xs), min(ys), max(xs), max(ys)

    def mirror_left_to_right(self) -> None:
        n = self.size
        for y in range(n):
            for x in range(n // 2):
                self._cells[y][n - 1 - x] = self._cells[y][x]

    def to_image(self) -> Image.Image:
        img = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        px = img.load()
        for y in range(self.size):
            for x in range(self.size):
                cell = self._cells[y][x]
                if cell is not None:
                    px[x, y] = (cell[0], cell[1], cell[2], 255)
        return img

    def save(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.to_image().save(out)
        return out


def rect(x0: int, y0: int, x1: int, y1: int) -> set[Coord]:
    lo_x, hi_x = sorted((x0, x1))
    lo_y, hi_y = sorted((y0, y1))
    return {(x, y) for y in range(lo_y, hi_y + 1) for x in range(lo_x, hi_x + 1)}


def disc(cx: float, cy: float, radius: float, size: int) -> set[Coord]:
    out: set[Coord] = set()
    for y in range(size):
        for x in range(size):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= radius:
                out.add((x, y))
    return out


def from_rows(rows: list[str], filled: str = "*", empty: str = ".") -> set[Coord]:
    out: set[Coord] = set()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != empty and (filled == "*" or ch == filled):
                out.add((x, y))
    return out
