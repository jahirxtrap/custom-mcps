"""Embedded pixel-art guidance and per-size constraints (self-contained, no external skill)."""
from __future__ import annotations

COLOR_LIMITS: dict[int, tuple[int, int]] = {
    8: (4, 6),
    16: (8, 12),
    32: (12, 16),
    64: (16, 32),
}


def color_limit(size: int) -> tuple[int, int]:
    """Recommended (min, max) distinct colors per sprite for the nearest standard size."""
    nearest = min(COLOR_LIMITS, key=lambda s: abs(s - size))
    return COLOR_LIMITS[nearest]


_HARD_RULES = [
    "Readable silhouette first; design so it reads at 1x.",
    "Hard edges, NO anti-aliasing: every pixel is fully opaque or fully transparent.",
    "Limited palette per sprite, hue-shifted ramps: cooler/darker shadows, warmer/lighter highlights.",
    "One consistent light source, top-left (~45 degrees).",
    "A dark 1px outline, 8-connected, drawn last.",
    "No floating pixels: content stays wrapped by its own border.",
]

_OUTLINE_GOTCHAS = [
    "The outline cannot draw past the canvas edge: keep content >=1px away from every border, "
    "or the border will be incomplete on that side.",
    "A 1px diagonal stroke gets visually doubled by the 8-connected outline: keep diagonal cores thin.",
]

_OUTLINE_EXCEPTIONS = [
    "Overlays mounted on top of another sprite: NO outer outline (it grows the silhouette 1px). "
    "Use inner-rim edge darkening instead.",
    "Composed/mounted figures: NO inner-rim (it creates neck/waist seams). Use shading for volume.",
    "Standalone blobs / distinct parts: inner-rim is fine.",
]

_RAMP_NOTES = [
    "skin: narrow warm ramp; shadows warm, highlights never reach pure white.",
    "hair: subtle sheen, lift toward white only ~5-11%.",
    "clothing/armor/props: wide hue-shifted ramp so volume reads.",
    "Color variants from one sprite: draw NEUTRAL grayscale (no hue) and recolor via tint; "
    "a baked hue makes the tint muddy.",
]

_ANTIPATTERNS = [
    "Pillow shading: darkening all edges uniformly (looks inflated, no light direction).",
    "Detail invisible at 1x.",
    "Non-integer scaling.",
    "Mixing pixel resolutions in one sprite.",
]


def guide(size: int = 0) -> str:
    """Render the embedded pixel-art guidance, with the color budget for `size` if given."""
    lines = ["# Pixel-art guide", "", "## Hard rules"]
    lines += [f"- {r}" for r in _HARD_RULES]
    lines += ["", "## Outline gotchas"]
    lines += [f"- {g}" for g in _OUTLINE_GOTCHAS]
    lines += ["", "## Outline exceptions"]
    lines += [f"- {e}" for e in _OUTLINE_EXCEPTIONS]
    lines += ["", "## Ramps"]
    lines += [f"- {n}" for n in _RAMP_NOTES]
    lines += ["", "## Anti-patterns"]
    lines += [f"- {a}" for a in _ANTIPATTERNS]
    lines += ["", "## Color budget by size"]
    for s, (lo, hi) in COLOR_LIMITS.items():
        lines.append(f"- {s}x{s}: {lo}-{hi} colors")
    if size > 0:
        lo, hi = color_limit(size)
        lines += ["", f"For {size}x{size}: aim for {lo}-{hi} distinct colors."]
    return "\n".join(lines)
