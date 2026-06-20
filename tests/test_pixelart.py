from __future__ import annotations

from pixelart_mcp.builder import build_from_spec, resolve_shape
from pixelart_mcp.imaging import image_to_payload, payload_to_grid, validate


def test_resolve_shape_union():
    pixels = resolve_shape([{"rect": [0, 0, 1, 0]}, {"pixels": [[5, 5]]}], 8)
    assert pixels == {(0, 0), (1, 0), (5, 5)}


def test_build_from_spec_outline_and_symmetry():
    spec = {
        "size": 8,
        "layers": [{"shape": {"rect": [2, 2, 3, 5]}, "fill": {"color": "#c83232"}}],
        "outline": "#101010",
        "symmetry": True,
    }
    grid = build_from_spec(spec)
    assert grid.get(2, 3) == (200, 50, 50)
    assert grid.get(5, 3) == (200, 50, 50)
    assert grid.get(1, 1) == (16, 16, 16)


def test_render_roundtrip_to_grid(tmp_path):
    spec = {
        "size": 8,
        "layers": [{"shape": {"rect": [3, 3, 4, 4]}, "fill": {"color": "#0a141e"}}],
    }
    out = tmp_path / "s.png"
    build_from_spec(spec).save(out)
    payload = image_to_payload(out, "hex")
    assert payload["size"] == 8
    assert payload["grid"][3][3] == "#0a141e"
    assert payload["grid"][0][0] is None


def test_payload_to_grid_with_palette(tmp_path):
    rows = [["a", "."], [".", "a"]]
    grid = payload_to_grid(rows, {"a": "#ffffff"}, 2)
    assert grid.get(0, 0) == (255, 255, 255)
    assert grid.get(1, 0) is None


def test_validate_flags_edge_and_budget(tmp_path):
    spec = {
        "size": 16,
        "layers": [{"shape": {"rect": [0, 0, 15, 15]}, "fill": {"ramp": {"base": "#3060a0", "steps": 5}}}],
    }
    out = tmp_path / "block.png"
    build_from_spec(spec).save(out)
    report = validate(out)
    assert "left" in report["edge_contact"]
    assert report["ok"] is False


def test_validate_clean_sprite(tmp_path):
    spec = {
        "size": 16,
        "layers": [{"shape": {"rect": [4, 4, 11, 11]}, "fill": {"color": "#3060a0"}}],
        "outline": "#101820",
    }
    out = tmp_path / "ok.png"
    build_from_spec(spec).save(out)
    report = validate(out)
    assert report["edge_contact"] == []
    assert report["antialiased_pixels"] == 0
