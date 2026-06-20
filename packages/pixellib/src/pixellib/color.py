"""Color ramps for pixel art: hue-shifted, skin, hair and neutral grayscale."""
from __future__ import annotations

from .grid import Color

Ramp = list[Color]


def clamp(value: float) -> int:
    return 0 if value < 0 else (255 if value > 255 else int(round(value)))


def hex_to_rgb(value: str) -> Color:
    text = value.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"expected #rrggbb, got {value!r}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def rgb_to_hex(color: Color) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def _factors(steps: int, low: float, high: float) -> list[float]:
    if steps == 1:
        return [1.0]
    return [low + (high - low) * i / (steps - 1) for i in range(steps)]


def ramp(base: Color, steps: int = 5, shift: float = 0.12) -> Ramp:
    """Volumetric ramp dark to light, hue-shifted: cool shadows, warm highlights."""
    r, g, b = base
    out: Ramp = []
    for i, factor in enumerate(_factors(steps, 0.55, 1.5)):
        warm = (i / (steps - 1) - 0.5) * 2 * shift if steps > 1 else 0.0
        out.append((clamp(r * factor * (1 + warm)), clamp(g * factor), clamp(b * factor * (1 - warm))))
    return out


def skin_ramp(base: Color, steps: int = 5) -> Ramp:
    """Narrow warm ramp: warm shadows, highlights that never reach white."""
    r, g, b = base
    out: Ramp = []
    for i, factor in enumerate(_factors(steps, 0.72, 1.15)):
        t = i / (steps - 1) if steps > 1 else 0.5
        k = (0.5 - t) * 2 * 0.1 if t < 0.5 else 0.0
        rr = clamp(r * factor * (1 + 0.04 * k))
        gg = clamp(g * factor * (1 - 0.18 * k))
        bb = clamp(b * factor * (1 - 0.45 * k))
        out.append((rr, gg, bb))
    return out


def hair_ramp(base: Color, steps: int = 5) -> Ramp:
    """Subtle sheen ramp: highlights lift only slightly toward white."""
    r, g, b = base
    lifts = _factors(steps, -0.36, 0.11)
    out: Ramp = []
    for lift in lifts:
        if lift < 0:
            out.append((clamp(r * (1 + lift)), clamp(g * (1 + lift)), clamp(b * (1 + lift) * 1.06)))
        else:
            out.append((clamp(r + (255 - r) * lift), clamp(g + (255 - g) * lift), clamp(b + (255 - b) * (lift - 0.01))))
    return out


def grayscale_ramp(steps: int = 8) -> Ramp:
    """Neutral gray ramp (no hue) for tint-colorable sprites."""
    low, high = 32, 238
    out: Ramp = []
    for i in range(steps):
        v = clamp(low + (high - low) * i / (steps - 1)) if steps > 1 else 135
        out.append((v, v, v))
    return out


def pick(ramp_colors: Ramp, brightness: float) -> Color:
    b = 0.0 if brightness < 0 else (1.0 if brightness > 1 else brightness)
    return ramp_colors[int(round(b * (len(ramp_colors) - 1)))]


def build_ramp(base: Color, kind: str = "art", steps: int = 5) -> Ramp:
    if kind == "skin":
        return skin_ramp(base, steps)
    if kind == "hair":
        return hair_ramp(base, steps)
    if kind in ("gray", "grayscale"):
        return grayscale_ramp(steps)
    return ramp(base, steps)
