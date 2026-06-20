"""Render a concept map / graphic organizer from a data spec, by Pillow."""
from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw, ImageFont

_PALETTE = ["#2d6cdf", "#e07b39", "#3a9d6b", "#9b5de5", "#c84b6b"]
_INK = (33, 37, 41)
_CENTRAL = (52, 58, 64)
_BG = (255, 255, 255)


def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def _tint(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(round(c + (255 - c) * factor) for c in rgb)


def _line_height(font: ImageFont.FreeTypeFont) -> int:
    box = font.getbbox("Agjpq")
    return (box[3] - box[1]) + 6


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        if draw.textlength(f"{current} {word}", font=font) <= max_w:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _block(draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.FreeTypeFont, pad: int) -> tuple[int, int]:
    width = max((draw.textlength(line, font=font) for line in lines), default=0)
    return int(width) + 2 * pad, _line_height(font) * len(lines) + 2 * pad


def _draw_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float, float, float],
    border: tuple[int, int, int],
    fill: tuple[int, int, int],
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    pad: int,
) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=fill, outline=border, width=2)
    line_h = _line_height(font)
    ty = y0 + pad
    for line in lines:
        lw = draw.textlength(line, font=font)
        draw.text((x0 + (x1 - x0 - lw) / 2, ty), line, font=font, fill=_INK)
        ty += line_h


def _item_text(item: Any) -> str:
    if isinstance(item, dict):
        label = str(item.get("label", "")).strip()
        text = str(item.get("text", "")).strip()
        return f"{label}: {text}".strip(": ").strip() or label or text
    return str(item)


def render_concept_map(spec: dict[str, Any]) -> Image.Image:
    central_text = str(spec.get("central") or spec.get("title") or "")
    branches = spec.get("branches") or []
    margin, pad, col_gap, v_gap, item_gap, item_max = 40, 12, 36, 46, 16, 190

    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f_central, f_branch, f_item = _font(26), _font(20), _font(15)

    c_lines = _wrap(probe, central_text, f_central, 320)
    c_w, c_h = _block(probe, c_lines, f_central, pad + 4)

    cols: list[dict[str, Any]] = []
    for index, branch in enumerate(branches):
        color = _hex_to_rgb(branch.get("color") or _PALETTE[index % len(_PALETTE)])
        b_lines = _wrap(probe, str(branch.get("label") or branch.get("title") or ""), f_branch, 200)
        b_w, b_h = _block(probe, b_lines, f_branch, pad)
        items = []
        for raw in branch.get("items") or []:
            i_lines = _wrap(probe, _item_text(raw), f_item, item_max)
            i_w, i_h = _block(probe, i_lines, f_item, pad)
            items.append({"lines": i_lines, "w": i_w, "h": i_h})
        col_w = max([b_w, *[it["w"] for it in items]])
        cols.append({"color": color, "lines": b_lines, "w": b_w, "h": b_h, "items": items, "col_w": col_w})

    total_cols = sum(c["col_w"] for c in cols) + col_gap * max(0, len(cols) - 1)
    width = max(total_cols, c_w) + 2 * margin
    branch_y = margin + c_h + v_gap
    branch_h = max((c["h"] for c in cols), default=0)
    items_h = max((sum(it["h"] + item_gap for it in c["items"]) for c in cols), default=0)
    height = branch_y + branch_h + v_gap + items_h + margin

    image = Image.new("RGB", (int(width), int(height)), _BG)
    draw = ImageDraw.Draw(image)

    cx = width / 2
    c_x0 = cx - c_w / 2
    _draw_box(
        draw, (c_x0, margin, c_x0 + c_w, margin + c_h),
        _CENTRAL, _tint(_CENTRAL, 0.9), c_lines, f_central, pad + 4,
    )

    x = margin + (width - 2 * margin - total_cols) / 2
    for col in cols:
        col_cx = x + col["col_w"] / 2
        b_x0 = col_cx - col["w"] / 2
        draw.line([(cx, margin + c_h), (col_cx, branch_y)], fill=col["color"], width=3)
        _draw_box(
            draw, (b_x0, branch_y, b_x0 + col["w"], branch_y + col["h"]),
            col["color"], _tint(col["color"], 0.85), col["lines"], f_branch, pad,
        )
        prev = (col_cx, branch_y + col["h"])
        iy = branch_y + col["h"] + v_gap
        for it in col["items"]:
            i_x0 = col_cx - it["w"] / 2
            draw.line([prev, (col_cx, iy)], fill=col["color"], width=2)
            _draw_box(
                draw, (i_x0, iy, i_x0 + it["w"], iy + it["h"]),
                col["color"], _tint(col["color"], 0.92), it["lines"], f_item, pad,
            )
            prev = (col_cx, iy + it["h"])
            iy += it["h"] + item_gap
        x += col["col_w"] + col_gap

    return image
