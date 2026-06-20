from __future__ import annotations

import json

import pytest
from i18nkit import (
    check_format,
    completeness,
    find_unused,
    flatten,
    list_locales,
    load_locale,
    locale_diff,
    pick_base,
)


def _write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def locales(tmp_path):
    d = tmp_path / "locales"
    d.mkdir()
    _write(d / "en.json", {"COMMON": {"SAVE": "Save", "HELLO": "Hi {name}"}, "BYE": "Bye"})
    _write(d / "es.json", {"COMMON": {"SAVE": "Guardar", "HELLO": "Hola"}, "EXTRA": "x"})
    return d


def test_flatten_nested():
    assert flatten({"A": {"B": "c"}, "D": "e"}) == {"A.B": "c", "D": "e"}


def test_load_locale(tmp_path):
    p = tmp_path / "en.json"
    _write(p, {"A": {"B": "c"}, "D": "e"})
    assert load_locale(p) == {"A.B": "c", "D": "e"}


def test_list_and_pick_base(locales):
    found = list_locales(locales)
    assert set(found) == {"en", "es"}
    assert pick_base(found, "") == "en"


def test_locale_diff(locales):
    report = locale_diff(str(locales))
    assert report["base"] == "en"
    es = report["diff"]["es"]
    assert "BYE" in es["missing"]
    assert "EXTRA" in es["extra"]
    assert es["in_sync"] is False
    assert report["all_in_sync"] is False


def test_completeness(locales):
    report = completeness(str(locales))
    assert report["completeness"]["en"]["percent"] == 100.0
    assert report["completeness"]["es"]["percent"] < 100.0


def test_check_format_placeholder(locales):
    report = check_format(str(locales))
    assert report["ok"] is False
    assert any(issue["key"] == "COMMON.HELLO" for issue in report["placeholder_issues"])


def test_find_unused(tmp_path):
    d = tmp_path / "loc"
    d.mkdir()
    _write(d / "en.json", {"USED": "u", "DEAD": "d"})
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.tsx").write_text('const x = t("USED"); const y = t("MISSING");', encoding="utf-8")
    report = find_unused(str(d), str(src))
    assert "MISSING" in report["used_not_defined"]
    assert "DEAD" in report["defined_not_used"]
