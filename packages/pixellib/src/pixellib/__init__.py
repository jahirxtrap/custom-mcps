"""pixellib: engine-agnostic pixel-art primitives (grid, ramps, shading, outline, preview)."""
from __future__ import annotations

from .color import (
    Ramp,
    build_ramp,
    grayscale_ramp,
    hair_ramp,
    hex_to_rgb,
    pick,
    ramp,
    rgb_to_hex,
    skin_ramp,
)
from .grid import Color, Coord, Grid, disc, from_rows, rect
from .outline import edge_contact, outline
from .preview import auto_scale, montage
from .reference import reference_brief
from .rules import COLOR_LIMITS, color_limit, guide
from .shade import inner_rim, shade, sphere

__all__ = [
    "Color",
    "Coord",
    "Grid",
    "Ramp",
    "rect",
    "disc",
    "from_rows",
    "hex_to_rgb",
    "rgb_to_hex",
    "ramp",
    "skin_ramp",
    "hair_ramp",
    "grayscale_ramp",
    "build_ramp",
    "pick",
    "shade",
    "sphere",
    "inner_rim",
    "outline",
    "edge_contact",
    "montage",
    "auto_scale",
    "guide",
    "color_limit",
    "COLOR_LIMITS",
    "reference_brief",
]
