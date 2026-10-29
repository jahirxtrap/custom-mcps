from __future__ import annotations

import json

import pytest
from tokenkit import (
    check_contrast,
    contrast,
    contrast_of,
    declared_pairs,
    design_guide,
    find_pairs,
    guide_topics,
    luminance,
    over,
    parse,
    read_theme,
    read_tokens,
    to_hex,
    used_pairs,
    variant_pairs,
)
from tokenkit.pairs import canon

WHITE = (255.0, 255.0, 255.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_parse_hex_forms():
    assert parse("#fff") == WHITE
    assert parse("#ffffff") == WHITE
    assert parse("000000") == BLACK
    assert parse("#ffffff80")[3] == pytest.approx(0.502, abs=0.002)


def test_parse_functional_notations():
    assert parse("rgb(255, 255, 255)") == WHITE
    assert parse("rgba(0,0,0,0.5)")[3] == pytest.approx(0.5)
    assert parse("hsl(0, 0%, 100%)")[0] == pytest.approx(255, abs=0.5)
    red = parse("hsl(0, 100%, 50%)")
    assert red[0] == pytest.approx(255, abs=0.5) and red[1] == pytest.approx(0, abs=0.5)
    assert to_hex(parse("oklch(0% 0 0)")) == "#000000"
    assert to_hex(parse("oklch(100% 0 0)")) == "#ffffff"


def test_parse_rejects_nonsense():
    assert parse("not-a-color") is None
    assert parse("") is None


def test_luminance_and_contrast_extremes():
    assert luminance(WHITE) == pytest.approx(1.0)
    assert luminance(BLACK) == pytest.approx(0.0)
    assert contrast(BLACK, WHITE) == pytest.approx(21.0, abs=0.01)
    assert contrast(WHITE, WHITE) == pytest.approx(1.0)


def test_contrast_matches_the_known_aa_boundary():
    assert round(contrast(parse("#767676"), WHITE), 2) == 4.54


def test_over_composites_alpha():
    assert over(parse("#00000080"), WHITE)[0] == pytest.approx(127.5, abs=0.6)
    assert over(parse("#123456"), WHITE) == (18.0, 52.0, 86.0, 1.0)


def test_read_theme_source_object(tmp_path):
    path = tmp_path / "brand.ts"
    _write(path, 'export const t = {\n  light: {\n    surface: "#FFFFFF",\n'
                 '    text: "#0F1111",\n  },\n  dark: {\n    surface: "#15181E",\n'
                 '    text: "#F4F6F8",\n  },\n};\n')
    themes = read_theme(path)
    assert set(themes) == {"light", "dark"}
    assert to_hex(themes["dark"]["surface"]) == "#15181e"


def test_read_theme_pack_json(tmp_path):
    path = tmp_path / "dark.json"
    _write(path, json.dumps({"kind": "dark", "accent": "#3f51b5",
                             "colors": {"background": "#0a0a0a", "on-background": "#ededed"}}))
    theme = read_theme(path)["dark"]
    assert to_hex(theme["on-background"]) == "#ededed"
    assert "accent" in theme


def test_read_theme_css_variables(tmp_path):
    path = tmp_path / "tokens.css"
    _write(path, ":root { --surface: #ffffff; --text: #111111; }\n"
                 ".dark { --surface: #0a0a0a; --text: #eeeeee; }\n")
    themes = read_theme(path)
    assert "dark" in themes
    assert to_hex(themes["dark"]["surface"]) == "#0a0a0a"


def test_read_tokens_walks_a_folder(tmp_path):
    _write(tmp_path / "a" / "light.json", json.dumps({"kind": "light", "colors": {
        "background": "#ffffff", "surface": "#f5f5f5", "text": "#111111"}}))
    _write(tmp_path / "a" / "dark.json", json.dumps({"kind": "dark", "colors": {
        "background": "#000000", "surface": "#111111", "text": "#eeeeee"}}))
    read = read_tokens(tmp_path)
    assert set(read["themes"]) == {"light", "dark"}
    assert read["sources"]["dark"].endswith("dark.json")


def test_canon_spells_a_token_one_way():
    assert canon("primary-soft") == canon("primarySoft") == canon("primary_soft")


def test_declared_pairs_follow_the_on_prefix():
    tokens = {"surface": WHITE, "on-surface": BLACK, "accent": WHITE, "stray": BLACK}
    assert declared_pairs(tokens) == [("on-surface", "surface", "named on-*")]


def test_used_pairs_reads_classes_used_together(tmp_path):
    _write(tmp_path / "Card.tsx", '<Box className="bg-app-surface text-app-text-muted p-md">x</Box>\n')
    found = used_pairs(tmp_path, prefix="app")
    assert {"surface"} == {entry["back"] for entry in found}
    assert {"text-muted"} == {entry["front"] for entry in found}
    assert found[0]["where"][0].startswith("Card.tsx:")


def test_variant_pairs_tie_a_surface_to_its_ink(tmp_path):
    _write(tmp_path / "badge.tsx",
           "const style = tva({ variants: { variant: {\n"
           "      default: 'bg-app-primary-soft',\n"
           "      danger: 'bg-app-danger-soft',\n"
           "} } });\n"
           "const textStyle = tva({ parentVariants: { variant: {\n"
           "      default: 'text-app-primary',\n"
           "      danger: 'text-app-danger',\n"
           "} } });\n")
    found = {(entry["front"], entry["back"]) for entry in variant_pairs(tmp_path, prefix="app")}
    assert ("primary", "primary-soft") in found
    assert ("danger", "danger-soft") in found


def test_find_pairs_matches_kebab_classes_to_camel_tokens(tmp_path):
    _write(tmp_path / "Chip.tsx", '<Box className="bg-app-primary-soft text-app-primary" />\n')
    tokens = {"primary": parse("#2563EB"), "primarySoft": parse("#D6E2FF")}
    found = find_pairs(tokens, tmp_path, prefix="app")
    assert ("primary", "primarySoft") in {(e["front"], e["back"]) for e in found}


def test_check_contrast_reports_failures_with_their_ratio(tmp_path):
    _write(tmp_path / "theme" / "dark.json", json.dumps({"kind": "dark", "colors": {
        "background": "#0a0a0a", "surface": "#15181e",
        "on-surface": "#2a2f38", "text": "#f4f6f8"}}))
    report = check_contrast(tmp_path / "theme")
    assert report["all_pass"] is False
    entry = report["report"]["dark"]
    failure = entry["failures"][0]
    assert failure["front"] == "on-surface" and failure["back"] == "surface"
    assert failure["ratio"] < 4.5 and failure["required"] == 4.5


def test_check_contrast_skips_decorative_unless_asked(tmp_path):
    _write(tmp_path / "t.json", json.dumps({"kind": "dark", "colors": {
        "logo": "#1a1a1a", "on-logo": "#1b1b1b", "surface": "#000000", "text": "#ffffff"}}))
    plain = check_contrast(tmp_path / "t.json")
    assert plain["report"]["dark"]["pairs"] == 0
    asked = check_contrast(tmp_path / "t.json", include_decorative=True)
    assert asked["report"]["dark"]["pairs"] == 1


def test_borders_are_held_to_the_ui_threshold(tmp_path):
    _write(tmp_path / "t.json", json.dumps({"kind": "light", "colors": {
        "border": "#949494", "on-border": "#ffffff", "surface": "#ffffff"}}))
    row = check_contrast(tmp_path / "t.json")["report"]["light"]["measured"][0]
    assert row["required"] == 3.0 and row["kind"] == "ui"


def test_check_contrast_without_tokens(tmp_path):
    path = tmp_path / "empty.ts"
    _write(path, "export const label = 'nothing to measure here';\n")
    assert "error" in check_contrast(path)


def test_contrast_of_two_colors():
    report = contrast_of("#000000", "#ffffff")
    assert report["ratio"] == 21.0
    assert report["aa_text"] and report["aaa_text"]
    assert contrast_of("#777777", "#ffffff")["aa_text"] is False
    assert "error" in contrast_of("nope", "#fff")


def test_design_guide_topics_and_aliases():
    assert {"heuristics", "laws", "contrast", "targets", "tokens"} == set(guide_topics())
    assert "Nielsen" in design_guide("heuristics")
    assert design_guide("nielsen") == design_guide("heuristics")
    assert design_guide("wcag") == design_guide("contrast")
    assert "4.5:1" in design_guide("contrast")
    assert "Fitts" in design_guide("laws")
    assert "Unknown topic" in design_guide("nope")
