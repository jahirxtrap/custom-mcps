from __future__ import annotations

import pytest
from loaderkit import (
    check_json,
    check_structure,
    find_symbol,
    java_for_mc,
    list_mods,
    loader_sync,
    mod_info,
    parse_mc_version,
)

_CODE = "package com.x;\nclass Foo {}\n"
_STALE = "package com.x;\nclass Foo { int stale; }\n"


def _make_mod(root, mod_name, modid, version, java_version, *, sync=True, java_in_common=False, bad_json=False):
    vd = root / mod_name / f"{modid}-{version}-multi"
    vd.mkdir(parents=True)
    (vd / "settings.gradle").write_text("include 'fabric'\n", encoding="utf-8")
    (vd / "build.gradle").write_text("subprojects {}\n", encoding="utf-8")
    (vd / "gradle.properties").write_text(
        f"mod_id={modid}\njavaVersion={java_version}\nminecraft_version={version}\n", encoding="utf-8"
    )
    for loader in ("fabric", "forge", "neoforge"):
        jdir = vd / loader / "src" / "main" / "java" / "com" / "x"
        jdir.mkdir(parents=True)
        content = _STALE if (loader == "forge" and not sync) else _CODE
        (jdir / "Foo.java").write_text(content, encoding="utf-8")
    lang_dir = vd / "common" / "src" / "main" / "resources" / "assets" / modid / "lang"
    lang_dir.mkdir(parents=True)
    body = '{\n  "key": "value"\n}'
    payload = (body + "\n") if bad_json else body
    (lang_dir / "en_us.json").write_bytes(payload.encode("utf-8"))
    if java_in_common:
        cj = vd / "common" / "src" / "main" / "java" / "com" / "x"
        cj.mkdir(parents=True)
        (cj / "Bad.java").write_text("package com.x;\nclass Bad {}\n", encoding="utf-8")
    return vd


@pytest.fixture
def workspace(tmp_path):
    _make_mod(tmp_path, "Foo Mod", "foomod", "26.1.2", 25)
    _make_mod(tmp_path, "Foo Mod", "foomod", "26.2", 25)
    _make_mod(tmp_path, "Bar Mod", "barmod", "1.21.11", 21, sync=False, java_in_common=True, bad_json=True)
    return tmp_path


def test_java_for_mc():
    assert java_for_mc("1.17.1") == 16
    assert java_for_mc("1.20.1") == 17
    assert java_for_mc("1.20.5") == 21
    assert java_for_mc("1.21.11") == 21
    assert java_for_mc("26.1.2") == 25
    assert java_for_mc("26.2") == 25


def test_parse_mc_version_order():
    assert parse_mc_version("1.21.11") > parse_mc_version("1.20.5")
    assert parse_mc_version("26.2") > parse_mc_version("1.21.11")


def test_list_mods_and_latest(workspace):
    mods = list_mods(workspace)
    assert sorted(m["mod"] for m in mods) == ["Bar Mod", "Foo Mod"]
    foo = next(m for m in mods if m["mod"] == "Foo Mod")
    assert len(foo["versions"]) == 2
    assert foo["latest"]["version"] == "26.2"


def test_mod_info(workspace):
    info = mod_info(workspace / "Foo Mod" / "foomod-26.1.2-multi")
    assert info["mc_version"] == "26.1.2"
    assert info["expected_java"] == 25
    assert info["properties"]["mod_id"] == "foomod"
    assert set(info["loaders"]) == {"fabric", "forge", "neoforge"}


def test_loader_sync_detects_drift(workspace):
    report = loader_sync(workspace / "Bar Mod" / "barmod-1.21.11-multi")
    assert report["in_sync"] is False
    assert "com/x/Foo.java" in report["differing"]


def test_loader_sync_clean(workspace):
    assert loader_sync(workspace / "Foo Mod" / "foomod-26.2-multi")["in_sync"] is True


def test_check_structure_flags_common_java(workspace):
    report = check_structure(workspace / "Bar Mod" / "barmod-1.21.11-multi")
    assert report["ok"] is False
    assert any("common" in issue for issue in report["issues"])


def test_check_structure_java_mismatch(tmp_path):
    vd = _make_mod(tmp_path, "Baz", "baz", "26.2", 21)
    report = check_structure(vd)
    assert any("Java 25" in issue for issue in report["issues"])


def test_check_json_detects_trailing_newline(workspace):
    report = check_json(workspace / "Bar Mod" / "barmod-1.21.11-multi")
    assert report["clean"] is False
    assert any("trailing newline" in v["problems"] for v in report["violations"])


def test_check_json_clean(workspace):
    assert check_json(workspace / "Foo Mod" / "foomod-26.2-multi")["clean"] is True


def test_find_symbol(workspace):
    report = find_symbol(workspace / "Foo Mod" / "foomod-26.2-multi", "class Foo")
    assert report["count"] >= 3
