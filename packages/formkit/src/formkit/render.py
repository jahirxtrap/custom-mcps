"""Software isometric/orthographic renderer for compiled primitives (flat-shaded, no GPU)."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

_LIGHT = np.array([-0.5, 0.85, 0.4])
_LIGHT = _LIGHT / np.linalg.norm(_LIGHT)
_OUTLINE = (28, 22, 18, 255)
_BOX_FACES = [
    (4, 5, 6, 7, (0, 0, 1)), (0, 1, 2, 3, (0, 0, -1)),
    (0, 3, 7, 4, (-1, 0, 0)), (1, 2, 6, 5, (1, 0, 0)),
    (2, 3, 7, 6, (0, 1, 0)), (0, 1, 5, 4, (0, -1, 0)),
]
_BOX_SIGNS = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
]


def _camera(az_deg: float, el_deg: float):
    az, el = math.radians(az_deg), math.radians(el_deg)
    forward = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
    forward = forward / np.linalg.norm(forward)
    right = np.cross(np.array([0.0, 1.0, 0.0]), forward)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    right = right / np.linalg.norm(right)
    up = np.cross(forward, right)
    return forward, right, up / np.linalg.norm(up)


def _faces(prims: list[dict[str, Any]]):
    out = []
    for prim in prims:
        color = tuple(prim["color"])
        if prim["type"] == "tri":
            verts = [np.array(v, dtype=float) for v in prim["verts"]]
            normal = np.cross(verts[1] - verts[0], verts[2] - verts[0])
            length = np.linalg.norm(normal)
            normal = normal / length if length > 1e-9 else np.array([0.0, 1.0, 0.0])
            out.append((verts, color, normal))
        else:
            center = np.array(prim["center"], dtype=float)
            half = np.array(prim["size"], dtype=float) / 2
            corners = [center + np.array(s, dtype=float) * half for s in _BOX_SIGNS]
            for a, b, c, d, nrm in _BOX_FACES:
                out.append(([corners[a], corners[b], corners[c], corners[d]], color, np.array(nrm, dtype=float)))
    return out


def render(prims: list[dict[str, Any]], view: str = "iso", size: int = 320, az: float = 45.0, el: float = 30.0,
           outline: bool = True) -> Image.Image:
    forward, right, up = _camera(az, el)
    silhouette = view == "silhouette"
    polys = []
    points: list[tuple[float, float]] = []
    for verts, color, normal in _faces(prims):
        sx = [float(np.dot(v, right)) for v in verts]
        sy = [float(np.dot(v, up)) for v in verts]
        depth = float(np.mean([np.dot(v, forward) for v in verts]))
        facing = normal if np.dot(normal, forward) >= 0 else -normal
        shade = 0.35 + 0.65 * max(0.0, float(np.dot(facing, _LIGHT)))
        shaded = tuple(max(0, min(255, int(c * shade))) for c in color)
        poly = list(zip(sx, sy, strict=True))
        polys.append((poly, depth, shaded))
        points += poly
    if not points:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    margin = 16
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-3)
    scale = (size - 2 * margin) / span
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def to_screen(point: tuple[float, float]) -> tuple[float, float]:
        return (size / 2 + (point[0] - cx) * scale, size / 2 - (point[1] - cy) * scale)

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    polys.sort(key=lambda item: item[1])
    for poly, _depth, shaded in polys:
        screen = [to_screen(p) for p in poly]
        fill = (0, 0, 0, 255) if silhouette else (*shaded, 255)
        edge = _OUTLINE if (outline and not silhouette) else None
        draw.polygon(screen, fill=fill, outline=edge)
    return image
