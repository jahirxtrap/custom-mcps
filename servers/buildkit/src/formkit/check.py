"""Validate a 3D spec against low-poly blockout rules (proportion, scale, openings, palette)."""
from __future__ import annotations

from typing import Any

from .compile import compile_spec, hex_to_rgb


def _palette_colors(spec: dict[str, Any], kind: str) -> set:
    if kind in ("building", "house"):
        pal = spec.get("palette", {})
        keys = [pal.get("wall", "#b8a884"), pal.get("roof", "#7a3b2a"),
                pal.get("door", "#5a3b2a"), pal.get("window", "#3a4a55")]
        return {hex_to_rgb(k) for k in keys}
    if kind == "tree":
        pal = spec.get("palette", {})
        return {hex_to_rgb(pal.get("trunk", "#5a3b2a")), hex_to_rgb(pal.get("leaves", "#3a6b3a"))}
    if kind == "group":
        return {hex_to_rgb(p.get("color", "#888888")) for p in spec.get("parts", [])}
    return {tuple(p["color"]) for p in compile_spec(dict(spec))}


def check(spec: dict[str, Any]) -> dict[str, Any]:
    kind = str(spec.get("type", "building")).lower()
    prims = compile_spec(dict(spec))
    colors = _palette_colors(spec, kind)
    issues: list[str] = []
    if kind in ("building", "house"):
        fp = spec.get("footprint", spec.get("size", [6, 6]))
        w = float(fp[0])
        d = float(fp[1] if len(fp) > 1 else fp[0])
        sh = float(spec.get("storey_height", 3.0))
        if not 2.2 <= sh <= 4.0:
            issues.append(f"storey_height {sh} m is outside the human range ~2.4-3.2")
        door = spec.get("openings", {}).get("door", {})
        dw = float(door.get("width", 1.8))
        side = str(door.get("side", spec.get("door", "south")))
        wall_len = w if side in ("north", "south") else d
        if dw > wall_len - 0.6:
            issues.append(f"door width {dw} m does not fit the {side} wall ({wall_len} m)")
        ratio = max(w, d) / max(1e-3, min(w, d))
        if ratio > 4:
            issues.append(f"footprint ratio {ratio:.1f}:1 is very elongated; check the proportion")
    if len(colors) > 5:
        issues.append(f"{len(colors)} colors; low-poly reads best with <=4-5 (limit the palette)")
    return {
        "type": kind,
        "primitive_count": len(prims),
        "colors": len(colors),
        "ok": not issues,
        "issues": issues,
        "note": "Heuristic blockout check (proportion/scale, door fit, palette). For the silhouette "
        "test, render with view='silhouette' and confirm it reads from every angle.",
    }
