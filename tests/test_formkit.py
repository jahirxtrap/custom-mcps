from __future__ import annotations

from formkit import (
    check,
    compile_spec,
    design_guide,
    godot_def,
    reference_brief,
    render,
)

_HOUSE = {
    "type": "building",
    "footprint": [6, 5],
    "storeys": 2,
    "storey_height": 3.0,
    "roof": {"type": "gable", "height": 1.6},
    "openings": {"door": {"side": "south", "width": 1.8}, "windows": {"grid": [3, 1]}},
    "palette": {"wall": "#b8a884", "roof": "#7a3b2a"},
}


def test_compile_building_has_boxes_and_roof_tris():
    prims = compile_spec(_HOUSE)
    kinds = {p["type"] for p in prims}
    assert "box" in kinds
    assert "tri" in kinds
    assert len(prims) > 6


def test_compile_tree():
    prims = compile_spec({"type": "tree", "trunk": {"height": 2.0}, "foliage": [{"shape": "cone"}]})
    assert any(p["type"] == "tri" for p in prims)
    assert any(p["type"] == "box" for p in prims)


def test_render_iso_and_silhouette_produce_visible_pixels():
    prims = compile_spec(_HOUSE)
    iso = render(prims, view="iso", size=128)
    sil = render(prims, view="silhouette", size=128)
    assert iso.size == (128, 128)
    assert iso.getextrema()[3][1] > 0
    assert sil.getextrema()[3][1] > 0


def test_check_flags_door_and_palette():
    ok = check(_HOUSE)
    assert ok["ok"] is True
    bad = dict(_HOUSE)
    bad["openings"] = {"door": {"side": "south", "width": 9.0}}
    report = check(bad)
    assert report["ok"] is False
    assert any("door" in issue for issue in report["issues"])


def test_godot_def_building_matches_house_builder():
    result = godot_def(_HOUSE)
    assert result["format"] == "house_builder"
    assert set(result["def"]) >= {"size", "height", "roof_height", "wall_color", "roof_color", "door"}
    assert result["def"]["door"] == "south"


def test_godot_def_group_emits_gdscript():
    result = godot_def({"type": "group", "parts": [{"box": [1, 2, 1], "at": [0, 1, 0], "color": "#888888"}]})
    assert result["format"] == "primitives"
    assert "FormBuilder" in result["gdscript"]
    assert result["def"]["parts"][0]["box"] == [1.0, 2.0, 1.0]


def test_guide_and_reference():
    assert "blockout" in design_guide("method").lower()
    assert "silhouette" in design_guide().lower()
    brief = reference_brief("watchtower", "building")
    assert any("floor plan" in q for q in brief["queries"])
    assert brief["look_for"]
