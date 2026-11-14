"""Emit a Godot-ready def (house_builder style) or a generic primitives def + GDScript builder."""
from __future__ import annotations

from typing import Any

from .compile import compile_spec, rgb_to_hex

_BUILDER_GD = '''class_name FormBuilder

static func build(root: Node3D, def: Dictionary) -> void:
\tfor part: Dictionary in def.get("parts", []):
\t\tvar color := Color(str(part.get("color", "#888888")))
\t\tif part.has("box"):
\t\t\tvar at: Array = part.get("at", [0, 0, 0])
\t\t\tvar s: Array = part["box"]
\t\t\t_box(root, Vector3(s[0], s[1], s[2]), Vector3(at[0], at[1], at[2]), color)
\t\telif part.has("tri"):
\t\t\t_tri(root, part["tri"], color)

static func _box(root: Node3D, size: Vector3, center: Vector3, color: Color) -> void:
\tvar view := MeshInstance3D.new()
\tview.position = center
\tvar mesh := BoxMesh.new()
\tmesh.size = size
\tview.mesh = mesh
\tvar mat := StandardMaterial3D.new()
\tmat.albedo_color = color
\tview.material_override = mat
\troot.add_child(view)

static func _tri(root: Node3D, verts: Array, color: Color) -> void:
\tvar surface := SurfaceTool.new()
\tsurface.begin(Mesh.PRIMITIVE_TRIANGLES)
\tfor v: Array in verts:
\t\tsurface.add_vertex(Vector3(v[0], v[1], v[2]))
\tsurface.generate_normals()
\tvar view := MeshInstance3D.new()
\tview.mesh = surface.commit()
\tvar mat := StandardMaterial3D.new()
\tmat.albedo_color = color
\tmat.cull_mode = BaseMaterial3D.CULL_DISABLED
\tview.material_override = mat
\troot.add_child(view)
'''


def godot_def(spec: dict[str, Any]) -> dict[str, Any]:
    kind = str(spec.get("type", "building")).lower()
    if kind in ("building", "house"):
        fp = spec.get("footprint", spec.get("size", [6, 6]))
        w = float(fp[0])
        d = float(fp[1] if len(fp) > 1 else fp[0])
        storeys = int(spec.get("storeys", 1))
        sh = float(spec.get("storey_height", 3.0))
        pal = spec.get("palette", {})
        house = {
            "size": [w, d],
            "height": float(spec.get("height", storeys * sh)),
            "roof_height": float(spec.get("roof", {}).get("height", 1.6)),
            "wall_color": pal.get("wall", "#b8a884"),
            "roof_color": pal.get("roof", "#7a3b2a"),
            "door": str(spec.get("openings", {}).get("door", {}).get("side", spec.get("door", "south"))),
        }
        return {
            "format": "house_builder",
            "def": house,
            "note": "Feed to HouseBuilder.build(root, def) (matches Vorenth's house_builder.gd keys).",
        }
    parts: list[dict[str, Any]] = []
    for prim in compile_spec(dict(spec)):
        if prim["type"] == "box":
            parts.append({"box": prim["size"], "at": prim["center"], "color": rgb_to_hex(prim["color"])})
        else:
            parts.append({"tri": prim["verts"], "color": rgb_to_hex(prim["color"])})
    return {
        "format": "primitives",
        "def": {"parts": parts},
        "gdscript": _BUILDER_GD,
        "note": "Save the gdscript as form_builder.gd; call FormBuilder.build(root, def) with the def.",
    }
