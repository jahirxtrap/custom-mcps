"""Compile a high-level 3D spec into flat primitives (axis-aligned boxes + triangles)."""
from __future__ import annotations

from typing import Any

WALL_THICK = 0.3
DOOR_W = 1.8
DOOR_H = 2.2
OVERHANG = 0.5

Color = tuple[int, int, int]


def hex_to_rgb(value: Any, default: Color = (180, 160, 140)) -> Color:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    text = str(value).lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) >= 6:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    return default


def rgb_to_hex(color: Color) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(c))) for c in color))


def _shade(color: Color, factor: float) -> Color:
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def _box(center: list[float], size: list[float], color: Color) -> dict[str, Any]:
    return {"type": "box", "center": [float(v) for v in center], "size": [float(v) for v in size], "color": color}


def _tri(a: list[float], b: list[float], c: list[float], color: Color) -> dict[str, Any]:
    return {"type": "tri", "verts": [list(map(float, a)), list(map(float, b)), list(map(float, c))], "color": color}


def _wall(side: str, center: list[float], size: list[float], color: Color, door: str, door_color: Color):
    if side != door:
        return [_box(center, size, color)]
    along_x = side in ("north", "south")
    length = size[0] if along_x else size[2]
    seg = (length - DOOR_W) / 2
    out: list[dict[str, Any]] = []
    if seg <= 0.15:
        out.append(_box(center, size, color))
        return out
    offset = DOOR_W / 2 + seg / 2
    for sign in (-1.0, 1.0):
        if along_x:
            out.append(_box([center[0] + sign * offset, center[1], center[2]], [seg, size[1], size[2]], color))
        else:
            out.append(_box([center[0], center[1], center[2] + sign * offset], [size[0], size[1], seg], color))
    door_h = min(DOOR_H, size[1] - 0.2)
    header = size[1] - door_h
    if header > 0.05:
        hc = [center[0], door_h + header / 2, center[2]]
        hs = [DOOR_W, header, size[2]] if along_x else [size[0], header, DOOR_W]
        out.append(_box(hc, hs, color))
    leaf = [center[0], door_h / 2, center[2]]
    ls = [DOOR_W, door_h, WALL_THICK * 0.6] if along_x else [WALL_THICK * 0.6, door_h, DOOR_W]
    out.append(_box(leaf, ls, _shade(door_color, 1.0)))
    return out


def _windows(spec: dict[str, Any], w: float, h: float, door: str, color: Color) -> list[dict[str, Any]]:
    win = spec.get("openings", {}).get("windows")
    if not win:
        return []
    grid = win.get("grid", [2, 1])
    cols = int(grid[0])
    rows = int(grid[1] if len(grid) > 1 else 1)
    ww, wh = (float(v) for v in win.get("size", [1.0, 1.2]))
    sill = float(win.get("sill", 0.9))
    out: list[dict[str, Any]] = []
    for side, zc in (("south", h * 0 + spec["_hd"]), ("north", -spec["_hd"])):
        if side == door:
            continue
        for r in range(rows):
            y = sill + wh / 2 + r * (wh + 0.4)
            if y + wh / 2 > spec["_h"] - 0.3:
                continue
            for c in range(cols):
                x = -w / 2 + w / (cols + 1) * (c + 1)
                out.append(_box([x, y, zc], [ww, wh, WALL_THICK * 1.2], color))
    return out


def _roof(spec: dict[str, Any], w: float, d: float, h: float, color: Color) -> list[dict[str, Any]]:
    roof = spec.get("roof", {})
    rtype = str(roof.get("type", "gable")).lower()
    rh = float(roof.get("height", 1.6))
    ov = float(roof.get("overhang", OVERHANG))
    hw, hd = w / 2 + ov, d / 2 + ov
    out = [_box([0, h, 0], [w, 0.1, d], _shade(color, 0.7))]
    c0, c1, c2, c3 = [-hw, h, -hd], [hw, h, -hd], [hw, h, hd], [-hw, h, hd]
    if rtype == "flat":
        out.append(_box([0, h + 0.15, 0], [w + ov, 0.3, d + ov], color))
        return out
    if rtype in ("pyramid", "hip"):
        apex = [0, h + rh, 0]
        for a, b in (((c0, c1)), (c1, c2), (c2, c3), (c3, c0)):
            out.append(_tri(a, b, apex, color))
        return out
    ra, rb = [-hw, h + rh, 0], [hw, h + rh, 0]
    out.append(_tri(c3, c2, rb, color))
    out.append(_tri(c3, rb, ra, color))
    out.append(_tri(c1, c0, ra, color))
    out.append(_tri(c1, ra, rb, color))
    out.append(_tri(c3, c0, ra, _shade(color, 0.85)))
    out.append(_tri(c1, c2, rb, _shade(color, 0.85)))
    return out


def _building(spec: dict[str, Any]) -> list[dict[str, Any]]:
    fp = spec.get("footprint", spec.get("size", [6, 6]))
    w = float(fp[0])
    d = float(fp[1] if len(fp) > 1 else fp[0])
    storeys = int(spec.get("storeys", 1))
    sh = float(spec.get("storey_height", 3.0))
    h = float(spec.get("height", storeys * sh))
    pal = spec.get("palette", {})
    wall = hex_to_rgb(pal.get("wall", "#b8a884"))
    roof_c = hex_to_rgb(pal.get("roof", "#7a3b2a"))
    door_c = hex_to_rgb(pal.get("door", "#5a3b2a"))
    win_c = hex_to_rgb(pal.get("window", "#3a4a55"))
    door = str(spec.get("openings", {}).get("door", {}).get("side", spec.get("door", "south")))
    hw, hd = w / 2, d / 2
    spec["_h"], spec["_hd"] = h, hd
    prims = [_box([0, 0.1, 0], [w, 0.2, d], _shade(wall, 0.55))]
    walls = [
        ("north", [0, h / 2, -hd], [w, h, WALL_THICK]),
        ("south", [0, h / 2, hd], [w, h, WALL_THICK]),
        ("west", [-hw, h / 2, 0], [WALL_THICK, h, d]),
        ("east", [hw, h / 2, 0], [WALL_THICK, h, d]),
    ]
    for side, center, size in walls:
        prims += _wall(side, center, size, wall, door, door_c)
    prims += _windows(spec, w, h, door, win_c)
    prims += _roof(spec, w, d, h, roof_c)
    return prims


def _tree(spec: dict[str, Any]) -> list[dict[str, Any]]:
    trunk = spec.get("trunk", {})
    th = float(trunk.get("height", 2.5))
    tr = float(trunk.get("radius", 0.25))
    pal = spec.get("palette", {})
    trunk_c = hex_to_rgb(pal.get("trunk", "#5a3b2a"))
    leaf_c = hex_to_rgb(pal.get("leaves", "#3a6b3a"))
    out = [_box([0, th / 2, 0], [tr * 2, th, tr * 2], trunk_c)]
    foliage = spec.get("foliage", [{"shape": "cone", "radius": 1.4, "height": 2.0, "y": th}])
    for f in foliage:
        shape = str(f.get("shape", "cone")).lower()
        rad = float(f.get("radius", 1.2))
        fh = float(f.get("height", 1.6))
        y = float(f.get("y", th))
        if shape == "cone":
            base = [[-rad, y, -rad], [rad, y, -rad], [rad, y, rad], [-rad, y, rad]]
            apex = [0, y + fh, 0]
            for i in range(4):
                out.append(_tri(base[i], base[(i + 1) % 4], apex, leaf_c))
        else:
            out.append(_box([0, y + fh / 2, 0], [rad * 2, fh, rad * 2], leaf_c))
    return out


def _group(spec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for part in spec.get("parts", []):
        color = hex_to_rgb(part.get("color", "#888888"))
        at = part.get("at", [0, 0, 0])
        if "box" in part:
            s = part["box"]
            out.append(_box([at[0], at[1], at[2]], [s[0], s[1], s[2]], color))
        elif "prism" in part:
            prism = part["prism"]
            base = prism.get("base", [1, 1])
            ph = float(prism.get("height", 1))
            hw, hd = base[0] / 2, base[1] / 2
            corners = [
                [at[0] - hw, at[1], at[2] - hd], [at[0] + hw, at[1], at[2] - hd],
                [at[0] + hw, at[1], at[2] + hd], [at[0] - hw, at[1], at[2] + hd],
            ]
            apex = [at[0], at[1] + ph, at[2]]
            for i in range(4):
                out.append(_tri(corners[i], corners[(i + 1) % 4], apex, color))
        elif "tri" in part:
            v = part["tri"]
            out.append(_tri(v[0], v[1], v[2], color))
    return out


def compile_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    kind = str(spec.get("type", "building")).lower()
    if kind in ("building", "house"):
        return _building(dict(spec))
    if kind == "tree":
        return _tree(spec)
    if kind == "group":
        return _group(spec)
    raise ValueError(f"unknown spec type '{kind}' (building/house/tree/group)")
