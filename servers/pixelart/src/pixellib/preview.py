"""Nearest-neighbor upscaled montage on a checkerboard, for human/agent verification."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

_DARK = (74, 74, 86, 255)
_LIGHT = (94, 94, 108, 255)
_BG = (38, 38, 46, 255)


def _load(item: Image.Image | str | Path) -> Image.Image:
    if isinstance(item, Image.Image):
        return item.convert("RGBA")
    return Image.open(item).convert("RGBA")


def _checkerboard(size: int, tile: int) -> Image.Image:
    bg = Image.new("RGBA", (size, size))
    px = bg.load()
    for y in range(size):
        for x in range(size):
            px[x, y] = _LIGHT if ((x // tile) + (y // tile)) % 2 == 0 else _DARK
    return bg


def auto_scale(native: int, target: int = 512) -> int:
    return max(1, target // max(1, native))


def montage(
    images: list[Image.Image | str | Path],
    scale: int = 0,
    cols: int = 0,
    pad: int = 8,
) -> Image.Image:
    """Upscale each image with NEAREST onto a checkerboard grid; never blurs pixels."""
    loaded = [_load(i) for i in images]
    if not loaded:
        raise ValueError("no images to preview")
    native = max(max(im.size) for im in loaded)
    factor = scale if scale > 0 else auto_scale(native)
    cell = native * factor
    count = len(loaded)
    columns = cols if cols > 0 else min(count, max(1, round(count**0.5)))
    rows = (count + columns - 1) // columns
    width = columns * (cell + pad) + pad
    height = rows * (cell + pad) + pad
    out = Image.new("RGBA", (width, height), _BG)
    for index, im in enumerate(loaded):
        scaled = im.resize((im.width * factor, im.height * factor), Image.NEAREST)
        tile = _checkerboard(cell, factor)
        offset = ((cell - scaled.width) // 2, (cell - scaled.height) // 2)
        tile.alpha_composite(scaled, offset)
        cx = pad + (index % columns) * (cell + pad)
        cy = pad + (index // columns) * (cell + pad)
        out.alpha_composite(tile, (cx, cy))
    return out
