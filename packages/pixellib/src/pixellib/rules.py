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

_SILHOUETTE = [
    "Silhouette test: fill the whole sprite with one solid color. Is it still recognizable? "
    "Can you tell front from back and read the pose? If not, fix the shape before adding detail.",
    "Lock the silhouette first; internal detail only earns its place once the outline reads.",
    "Readable shape beats internal detail every time: detail that vanishes at 1x is wasted pixels.",
]

_SIZES = [
    "8x8: items, bullets, tiny props.",
    "16x16: classic icons and props -- the clarity sweet spot.",
    "32x32: characters and detailed sprites (modern standard).",
    "64x64: large enemies, bosses, portraits.",
    "Chibi proportions: head ~50% of height. Realistic proportions: head ~1/6 to 1/8 of height.",
]

_LIGHT = [
    "Commit to one light direction (top-left ~45deg) and keep it across the whole set.",
    "Highlights on top surfaces and faces toward the light; midtones on the sides; "
    "shadows on bottom surfaces and faces away from the light.",
    "Hue-shift while shading: push shadows toward cool (blue/purple), highlights toward warm "
    "(yellow/orange). Just darkening the same hue looks flat.",
    "A small cast shadow under an object grounds it.",
]

_RAMP_NOTES = [
    "skin: narrow warm ramp; shadows warm, highlights never reach pure white.",
    "hair: subtle sheen, lift toward white only ~5-11%.",
    "clothing/armor/props: wide hue-shifted ramp so volume reads.",
    "Color variants from one sprite: draw NEUTRAL grayscale (no hue) and recolor via tint; "
    "a baked hue makes the tint muddy.",
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

_OUTLINE_STYLES = [
    "none: softer, painted look -- best for larger or atmospheric sprites.",
    "selective: outline only the outer edge -- clean and readable, a solid default.",
    "full: outline every edge including internal -- bold, cartoon, high visibility.",
    "colored: outline in the darkest shade of the adjacent color (not pure black) -- soft, integrated.",
    "Pick one style and keep 1px weight consistent across a set; mixed weights look amateur.",
]

_DITHERING = [
    "For a gradient inside a limited palette, use ORDERED dithering (checkerboard / 25% / diagonal), "
    "never random noise -- noise looks messy at pixel scale.",
    "Prefer one more ramp step over heavy dithering when the color budget allows it.",
]

_ANTIPATTERNS = [
    "Pillow shading: darkening all edges uniformly (looks inflated, no light direction).",
    "Detail invisible at 1x.",
    "Non-integer scaling (always scale by whole numbers).",
    "Mixing pixel resolutions in one sprite.",
    "Anti-aliasing against a background color (causes halos on other backgrounds).",
]


def guide(size: int = 0) -> str:
    """Render the embedded pixel-art guidance, with the color budget for `size` if given."""
    sections = [
        ("Hard rules", _HARD_RULES),
        ("Silhouette first", _SILHOUETTE),
        ("Sizes & proportions", _SIZES),
        ("Shading & light", _LIGHT),
        ("Ramps", _RAMP_NOTES),
        ("Outline gotchas", _OUTLINE_GOTCHAS),
        ("Outline exceptions", _OUTLINE_EXCEPTIONS),
        ("Outline styles", _OUTLINE_STYLES),
        ("Dithering", _DITHERING),
        ("Anti-patterns", _ANTIPATTERNS),
    ]
    lines = ["# Pixel-art guide"]
    for title, items in sections:
        lines += ["", f"## {title}"]
        lines += [f"- {item}" for item in items]
    lines += ["", "## Color budget by size"]
    for s, (lo, hi) in COLOR_LIMITS.items():
        lines.append(f"- {s}x{s}: {lo}-{hi} colors")
    if size > 0:
        lo, hi = color_limit(size)
        lines += ["", f"For {size}x{size}: aim for {lo}-{hi} distinct colors."]
    return "\n".join(lines)
