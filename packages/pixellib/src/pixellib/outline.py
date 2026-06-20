"""1px 8-connected outline plus the canvas-edge guard that keeps it complete."""
from __future__ import annotations

from .grid import Color, Grid

_NEIGHBORS = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0)]


def outline(grid: Grid, color: Color) -> None:
    """Paint a dark 1px border on every transparent cell touching content. Draw last."""
    additions = []
    for y in range(grid.size):
        for x in range(grid.size):
            if grid.get(x, y) is not None:
                continue
            if any(grid.get(x + dx, y + dy) is not None for dx, dy in _NEIGHBORS):
                additions.append((x, y))
    for x, y in additions:
        grid.put(x, y, color)


def edge_contact(grid: Grid) -> list[str]:
    """Report canvas borders the content touches; the outline cannot draw past them."""
    n = grid.size
    touched: list[str] = []
    if any(grid.get(x, 0) is not None for x in range(n)):
        touched.append("top")
    if any(grid.get(x, n - 1) is not None for x in range(n)):
        touched.append("bottom")
    if any(grid.get(0, y) is not None for y in range(n)):
        touched.append("left")
    if any(grid.get(n - 1, y) is not None for y in range(n)):
        touched.append("right")
    return touched
