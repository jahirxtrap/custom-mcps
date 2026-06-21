from __future__ import annotations

import pytest
from pixellib import (
    Grid,
    build_ramp,
    color_limit,
    disc,
    edge_contact,
    from_rows,
    grayscale_ramp,
    hex_to_rgb,
    montage,
    outline,
    pick,
    ramp,
    rect,
    rgb_to_hex,
    shade,
)


def test_grid_put_get_and_bounds():
    grid = Grid(8)
    assert grid.get(0, 0) is None
    grid.put(2, 3, (10, 20, 30))
    assert grid.get(2, 3) == (10, 20, 30)
    grid.put(99, 99, (1, 1, 1))
    assert grid.bounds() == (2, 3, 2, 3)


def test_hex_roundtrip():
    assert rgb_to_hex(hex_to_rgb("#1a2b3c")) == "#1a2b3c"


def test_hex_rejects_bad_input():
    with pytest.raises(ValueError):
        hex_to_rgb("#fff")


def test_ramp_is_dark_to_light_and_clamped():
    colors = ramp((120, 90, 60), steps=5)
    assert len(colors) == 5
    assert sum(colors[0]) < sum(colors[-1])
    for channel in colors[-1]:
        assert 0 <= channel <= 255


def test_grayscale_ramp_is_neutral():
    for r, g, b in grayscale_ramp(8):
        assert r == g == b


def test_pick_clamps_brightness():
    colors = ramp((100, 100, 100), steps=4)
    assert pick(colors, -5) == colors[0]
    assert pick(colors, 5) == colors[-1]


def test_rect_and_disc_and_from_rows():
    assert rect(0, 0, 1, 1) == {(0, 0), (1, 0), (0, 1), (1, 1)}
    assert (4, 4) in disc(4, 4, 2, 8)
    pixels = from_rows([".#.", "###"])
    assert pixels == {(1, 0), (0, 1), (1, 1), (2, 1)}


def test_outline_wraps_content_8_connected():
    grid = Grid(5)
    grid.put(2, 2, (200, 200, 200))
    outline(grid, (0, 0, 0))
    assert grid.get(1, 1) == (0, 0, 0)
    assert grid.get(2, 1) == (0, 0, 0)
    assert grid.get(2, 2) == (200, 200, 200)


def test_edge_contact_detects_border():
    grid = Grid(4)
    grid.put(0, 1, (1, 1, 1))
    assert "left" in edge_contact(grid)
    assert "right" not in edge_contact(grid)


def test_shade_fills_region_with_ramp_colors():
    grid = Grid(6)
    region = rect(1, 1, 4, 4)
    colors = build_ramp(hex_to_rgb("#406080"), "art", 5)
    shade(grid, region, colors)
    painted = grid.filled()
    assert painted == region
    assert all(grid.get(x, y) in colors for x, y in region)


def test_montage_upscales_nearest():
    grid = Grid(8)
    grid.paint(rect(2, 2, 5, 5), (255, 0, 0))
    image = montage([grid.to_image()], scale=10)
    assert image.width >= 80
    assert image.height >= 80


def test_color_limit_buckets():
    assert color_limit(16) == (8, 12)
    assert color_limit(32) == (12, 16)


def test_guide_mentions_related_skill():
    from pixellib import guide

    assert "pixel-art-sprites" in guide()


def test_reference_brief():
    from pixellib import reference_brief

    brief = reference_brief("fox", 32, "creature")
    assert any("fox" in q for q in brief["queries"])
    assert any("pixel art" in q for q in brief["queries"])
    assert brief["color_budget"] == list(color_limit(32))
