"""Software isometric/orthographic renderer for compiled primitives (z-buffer, flat-shaded, no GPU)."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from PIL import Image

_LIGHT = np.array([-0.5, 0.85, 0.4])
_LIGHT = _LIGHT / np.linalg.norm(_LIGHT)
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


def _raster(zbuf, rgb, alpha, a, b, c, color):
    size = zbuf.shape[0]
    min_x = max(0, int(math.floor(min(a[0], b[0], c[0]))))
    max_x = min(size - 1, int(math.ceil(max(a[0], b[0], c[0]))))
    min_y = max(0, int(math.floor(min(a[1], b[1], c[1]))))
    max_y = min(size - 1, int(math.ceil(max(a[1], b[1], c[1]))))
    if min_x > max_x or min_y > max_y:
        return
    denom = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denom) < 1e-9:
        return
    ys, xs = np.mgrid[min_y:max_y + 1, min_x:max_x + 1]
    px, py = xs + 0.5, ys + 0.5
    w0 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / denom
    w1 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / denom
    w2 = 1.0 - w0 - w1
    inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
    depth = w0 * a[2] + w1 * b[2] + w2 * c[2]
    region = zbuf[min_y:max_y + 1, min_x:max_x + 1]
    mask = inside & (depth > region)
    region[mask] = depth[mask]
    rgb[min_y:max_y + 1, min_x:max_x + 1][mask] = color
    alpha[min_y:max_y + 1, min_x:max_x + 1][mask] = True


def render(prims: list[dict[str, Any]], view: str = "iso", size: int = 320, az: float = 45.0,
           el: float = 30.0) -> Image.Image:
    forward, right, up = _camera(az, el)
    silhouette = view == "silhouette"
    faces = []
    points: list[tuple[float, float]] = []
    for verts, color, normal in _faces(prims):
        pv = [(float(np.dot(v, right)), float(np.dot(v, up)), float(np.dot(v, forward))) for v in verts]
        facing = normal if np.dot(normal, forward) >= 0 else -normal
        shade = 0.35 + 0.65 * max(0.0, float(np.dot(facing, _LIGHT)))
        shaded = (0, 0, 0) if silhouette else tuple(max(0, min(255, int(c * shade))) for c in color)
        faces.append((pv, shaded))
        points += [(p[0], p[1]) for p in pv]
    if not points:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    margin = 16
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-3)
    scale = (size - 2 * margin) / span
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def screen(p: tuple[float, float, float]) -> tuple[float, float, float]:
        return (size / 2 + (p[0] - cx) * scale, size / 2 - (p[1] - cy) * scale, p[2])

    zbuf = np.full((size, size), -np.inf)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)
    alpha = np.zeros((size, size), dtype=bool)
    for pv, shaded in faces:
        sv = [screen(p) for p in pv]
        for i in range(1, len(sv) - 1):
            _raster(zbuf, rgb, alpha, sv[0], sv[i], sv[i + 1], shaded)
    out = np.zeros((size, size, 4), dtype=np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(alpha, 255, 0)
    return Image.fromarray(out, "RGBA")
