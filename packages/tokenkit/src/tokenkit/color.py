"""Parse CSS colors and measure them the way WCAG defines: no dependencies, math only."""
from __future__ import annotations

import math
import re

Color = tuple[float, float, float, float]

_HEX = re.compile(r"^#?([0-9a-fA-F]{3,8})$")
_FUNC = re.compile(r"^(rgba?|hsla?|oklch|oklab)\(([^)]*)\)$", re.IGNORECASE)
_NAMED = {
    "black": (0.0, 0.0, 0.0, 1.0),
    "white": (255.0, 255.0, 255.0, 1.0),
    "transparent": (0.0, 0.0, 0.0, 0.0),
}


def _numbers(body: str) -> list[tuple[float, bool]]:
    out: list[tuple[float, bool]] = []
    for raw in re.split(r"[\s,/]+", body.strip()):
        if not raw:
            continue
        percent = raw.endswith("%")
        try:
            out.append((float(raw.rstrip("%")), percent))
        except ValueError:
            continue
    return out


def _from_hex(digits: str) -> Color | None:
    if len(digits) in (3, 4):
        digits = "".join(c * 2 for c in digits)
    if len(digits) == 6:
        digits += "ff"
    if len(digits) != 8:
        return None
    values = [int(digits[i:i + 2], 16) for i in (0, 2, 4, 6)]
    return (float(values[0]), float(values[1]), float(values[2]), values[3] / 255)


def _from_hsl(parts: list[tuple[float, bool]]) -> Color:
    hue = parts[0][0] % 360 / 360
    saturation = parts[1][0] / 100
    lightness = parts[2][0] / 100
    alpha = _alpha(parts, 3)
    if saturation == 0:
        channel = lightness * 255
        return (channel, channel, channel, alpha)
    second = lightness * (1 + saturation) if lightness < 0.5 else lightness + saturation - lightness * saturation
    first = 2 * lightness - second

    def channel(shift: float) -> float:
        value = (hue + shift) % 1
        if value < 1 / 6:
            result = first + (second - first) * 6 * value
        elif value < 1 / 2:
            result = second
        elif value < 2 / 3:
            result = first + (second - first) * (2 / 3 - value) * 6
        else:
            result = first
        return result * 255

    return (channel(1 / 3), channel(0), channel(-1 / 3), alpha)


def _alpha(parts: list[tuple[float, bool]], index: int) -> float:
    if len(parts) <= index:
        return 1.0
    value, percent = parts[index]
    return max(0.0, min(1.0, value / 100 if percent else value))


def _linear_to_srgb(value: float) -> float:
    value = 12.92 * value if value <= 0.0031308 else 1.055 * (value ** (1 / 2.4)) - 0.055
    return max(0.0, min(1.0, value)) * 255


def _from_oklab(lightness: float, a: float, b: float, alpha: float) -> Color:
    l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    red = 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    green = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    blue = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_
    return (_linear_to_srgb(red), _linear_to_srgb(green), _linear_to_srgb(blue), alpha)


def parse(value: str) -> Color | None:
    """Parse #hex, rgb(), hsl(), oklch() or oklab() into (r, g, b, alpha)."""
    text = str(value).strip()
    if text.lower() in _NAMED:
        return _NAMED[text.lower()]
    found = _HEX.match(text)
    if found:
        return _from_hex(found.group(1))
    call = _FUNC.match(text)
    if not call:
        return None
    name = call.group(1).lower()
    parts = _numbers(call.group(2))
    if len(parts) < 3:
        return None
    if name.startswith("rgb"):
        channels = [p[0] * 255 / 100 if p[1] else p[0] for p in parts[:3]]
        return (channels[0], channels[1], channels[2], _alpha(parts, 3))
    if name.startswith("hsl"):
        return _from_hsl(parts)
    lightness = parts[0][0] / 100 if parts[0][1] else parts[0][0]
    if name == "oklab":
        return _from_oklab(lightness, parts[1][0], parts[2][0], _alpha(parts, 3))
    chroma = parts[1][0] * 0.4 / 100 if parts[1][1] else parts[1][0]
    hue = math.radians(parts[2][0])
    return _from_oklab(lightness, chroma * math.cos(hue), chroma * math.sin(hue), _alpha(parts, 3))


def over(front: Color, back: Color) -> Color:
    """Composite a translucent color onto an opaque one."""
    alpha = front[3]
    if alpha >= 1.0:
        return (front[0], front[1], front[2], 1.0)
    return tuple(front[i] * alpha + back[i] * (1 - alpha) for i in range(3)) + (1.0,)  # type: ignore[return-value]


def luminance(color: Color) -> float:
    """Relative luminance as WCAG 2.x defines it."""
    channels = []
    for raw in color[:3]:
        value = max(0.0, min(255.0, raw)) / 255
        channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(front: Color, back: Color) -> float:
    """Contrast ratio between two colors, compositing the front one when translucent."""
    solid = over(front, back)
    first, second = luminance(solid), luminance(back)
    high, low = max(first, second), min(first, second)
    return (high + 0.05) / (low + 0.05)


def to_hex(color: Color) -> str:
    """Render a color back as #rrggbb, or #rrggbbaa when translucent."""
    parts = [f"{int(round(max(0.0, min(255.0, channel)))):02x}" for channel in color[:3]]
    if color[3] < 1.0:
        parts.append(f"{int(round(color[3] * 255)):02x}")
    return "#" + "".join(parts)
