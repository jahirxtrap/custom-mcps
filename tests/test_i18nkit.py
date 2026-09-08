from __future__ import annotations

import json

import pytest
from i18nkit import (
    base_key,
    check_format,
    completeness,
    find_unused,
    flatten,
    layout,
    list_locales,
    load_catalog,
    load_locale,
    locale_diff,
    pick_base,
    plural_form,
)


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def locales(tmp_path):
    d = tmp_path / "locales"
    d.mkdir()
    _write(d / "en.json", {"COMMON": {"SAVE": "Save", "HELLO": "Hi {name}"}, "BYE": "Bye"})
    _write(d / "es.json", {"COMMON": {"SAVE": "Guardar", "HELLO": "Hola"}, "EXTRA": "x"})
    return d


@pytest.fixture
def namespaced(tmp_path):
    d = tmp_path / "ns-locales"
    _write(d / "en" / "common.json", {"save": "Save", "cancel": "Cancel"})
    _write(d / "en" / "cart.json", {"units_one": "{{count}} unit", "units_other": "{{count}} units"})
    _write(d / "es" / "common.json", {"save": "Guardar", "cancel": "Cancelar"})
    _write(
        d / "es" / "cart.json",
        {
            "units_one": "{{count}} unidad",
            "units_many": "{{count}} de unidades",
            "units_other": "{{count}} unidades",
        },
    )
    return d


def test_flatten_nested():
    assert flatten({"A": {"B": "c"}, "D": "e"}) == {"A.B": "c", "D": "e"}


def test_load_locale(tmp_path):
    p = tmp_path / "en.json"
    _write(p, {"A": {"B": "c"}, "D": "e"})
    assert load_locale(p) == {"A.B": "c", "D": "e"}


def test_plural_helpers():
    assert base_key("units_many") == "units"
    assert base_key("status_other_thing") == "status_other_thing"
    assert plural_form("units_many") == "many"
    assert plural_form("units") == ""


def test_list_and_pick_base(locales):
    found = list_locales(locales)
    assert set(found) == {"en", "es"}
    assert pick_base(found, "") == "en"


def test_layout_detection(locales, namespaced):
    assert layout(locales) == "flat"
    assert layout(namespaced) == "namespaced"


def test_load_catalog_namespaces_keys(namespaced):
    catalog = load_catalog(namespaced)
    assert set(catalog) == {"en", "es"}
    assert catalog["en"]["common:save"] == "Save"
    assert "cart:units_one" in catalog["en"]


def test_locale_diff(locales):
    report = locale_diff(str(locales))
    assert report["base"] == "en"
    assert report["layout"] == "flat"
    es = report["diff"]["es"]
    assert "BYE" in es["missing"]
    assert "EXTRA" in es["extra"]
    assert report["all_in_sync"] is False


def test_locale_diff_extra_plural_form_is_not_a_diff(namespaced):
    report = locale_diff(str(namespaced))
    assert report["layout"] == "namespaced"
    es = report["diff"]["es"]
    assert es["missing"] == []
    assert es["extra"] == []
    assert es["plural_mismatch"] == []
    assert report["all_in_sync"] is True


def test_locale_diff_flags_plural_mismatch(tmp_path):
    d = tmp_path / "loc"
    _write(d / "en" / "cart.json", {"units_one": "unit", "units_other": "units"})
    _write(d / "es" / "cart.json", {"units": "unidades"})
    mismatch = locale_diff(str(d))["diff"]["es"]["plural_mismatch"]
    assert any(entry["key"] == "cart:units" for entry in mismatch)


def test_completeness(locales, namespaced):
    assert completeness(str(locales))["completeness"]["es"]["percent"] < 100.0
    assert completeness(str(namespaced))["completeness"]["es"]["percent"] == 100.0


def test_check_format_placeholder(locales):
    report = check_format(str(locales))
    assert report["ok"] is False
    assert any(issue["key"] == "COMMON.HELLO" for issue in report["placeholder_issues"])


def test_check_format_reads_double_braces(namespaced):
    from i18nkit import placeholders

    assert placeholders("{{count}} units") == {"{{count}}"}
    assert check_format(str(namespaced))["ok"] is True


def test_find_unused(tmp_path):
    d = tmp_path / "loc"
    d.mkdir()
    _write(d / "en.json", {"USED": "u", "DEAD": "d"})
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.tsx").write_text('const x = t("USED"); const y = t("MISSING");', encoding="utf-8")
    report = find_unused(str(d), str(src))
    assert "MISSING" in report["used_not_declared"]
    assert "DEAD" in report["declared_not_used"]


def test_find_unused_resolves_namespaces_plurals_and_catalogue(namespaced, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.tsx").write_text(
        't("save"); t("cart:units", { count }); t("cart:gone");', encoding="utf-8"
    )
    report = find_unused(str(namespaced), str(src))
    assert report["default_namespace"] == "common"
    assert report["used_not_declared"] == ["cart:gone"]
    assert "cart:units_one" not in report["declared_not_used"]
    assert "common:cancel" not in report["declared_not_used"]


def test_find_unused_ignore_list(namespaced, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.tsx").write_text('t("save");', encoding="utf-8")
    report = find_unused(str(namespaced), str(src), ignore="cart:units_one,cart:units_other")
    assert report["declared_not_used"] == []
