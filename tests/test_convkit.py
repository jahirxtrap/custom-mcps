from __future__ import annotations

import shutil
import subprocess

import pytest
from convkit import (
    commit_context,
    commit_style,
    find_duplication,
    find_format,
    find_hardcoded,
    find_inconsistent,
    guide,
    topics,
)

_HAS_GIT = shutil.which("git") is not None


def _make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def g(*args):
        subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)

    g("init", "-q")
    g("config", "user.email", "x@y.z")
    g("config", "user.name", "x")
    (repo / "a.txt").write_text("a", encoding="utf-8")
    g("add", "-A")
    g("commit", "-q", "-m", "feat: first thing")
    (repo / "b.txt").write_text("b", encoding="utf-8")
    g("add", "-A")
    g("commit", "-q", "-m", "fix: second thing")
    return repo


def test_topics():
    found = topics()
    assert {"commit", "hardcoding", "spacing", "format", "patterns", "naming"} <= set(found)
    assert {"ssot", "boundaries", "scope", "data", "i18n", "runtime", "verify"} <= set(found)


def test_guide_commit_issue_footers():
    text = guide("commit")
    assert "Closes: #12" in text
    assert "Refs: #12" in text
    assert "closes only the first" in text
    assert "interpret-trailers" in text
    assert "BREAKING CHANGE" in text
    assert "Co-Authored-By" in text


def test_guide_multistore_principles():
    assert "No emoji or pictographs" in guide("code")
    assert "Each layer knows only the one below" in guide("boundaries")
    assert "Derived values are computed by the database" in guide("data")
    runtime = guide("runtime")
    assert "No console.* in the frontend" in runtime
    assert "State is a row, not a log line" in runtime
    patterns = guide("patterns")
    assert "response_model on EVERY endpoint" in patterns
    assert "diff IS the review" in patterns
    assert "regenerated, never authored" in patterns
    verify = guide("verify")
    assert "A silenced rule is not a passing rule" in verify
    assert "put it in the linter" in verify
    assert "touch no database" in verify


def test_guide_new_principles():
    assert "authoritative definition per fact" in guide("ssot")
    assert "exclusive capability" in guide("boundaries")
    assert "dead code" in guide("scope")
    assert "does production need this row" in guide("data")
    assert "while True: sleep(n); check()" in guide("runtime")
    assert "not evidence" in guide("verify")


def test_guide_i18n_pluralization():
    text = guide("i18n")
    assert "key_one / key_other" in text
    assert "Intl.PluralRules" in text
    assert "Interpolate, never concatenate" in text
    assert "name_es / name_en" in text
    assert "camelCase names the KEY, never the suffix" in text
    assert "countOne" in text


def test_guide_never_mentions_an_envelope():
    text = guide()
    assert "envelope" not in text.lower()
    patterns = guide("patterns")
    assert "returns its typed model directly" in patterns
    assert "response_model on EVERY endpoint" in patterns


def test_guide_all_and_topic():
    full = guide()
    assert "## commit" in full and "## naming" in full
    one = guide("hardcoding")
    assert "## hardcoding" in one and "## commit" not in one


def test_find_hardcoded_flags(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "Screen.kt").write_text("val c = Color(0xFFAA1133)\nval s = 16.dp\n", encoding="utf-8")
    markup = '<div className="bg-blue-500" style={{padding: "12px"}}>#ffffff</div>\n'
    (src / "ui.tsx").write_text(markup, encoding="utf-8")
    (src / "themes.ts").write_text('export const c = "#ffffff"\n', encoding="utf-8")
    report = find_hardcoded(str(src))
    files = {h["file"] for h in report["hits"]}
    assert any("Screen.kt" in f for f in files)
    assert any("ui.tsx" in f for f in files)
    assert not any("themes.ts" in f for f in files)
    kinds = {k for h in report["hits"] for k in h["kinds"]}
    assert {"color-literal", "size", "raw-tailwind"} <= kinds


def test_find_hardcoded_skips_vendored(tmp_path):
    vendor = tmp_path / "node_modules"
    vendor.mkdir()
    (vendor / "lib.ts").write_text('const c = "#ffffff"\n', encoding="utf-8")
    assert find_hardcoded(str(tmp_path))["scanned_files"] == 0


def test_find_hardcoded_skips_token_folder_and_vendored_components(tmp_path):
    tokens = tmp_path / "theme" / "themes"
    tokens.mkdir(parents=True)
    (tokens / "brand.ts").write_text('export const bg = "#1B1E24"\n', encoding="utf-8")
    ui = tmp_path / "app" / "components" / "ui" / "badge"
    ui.mkdir(parents=True)
    (ui / "index.tsx").write_text('const c = "#ffffff"\n', encoding="utf-8")
    mine = tmp_path / "app" / "screens"
    mine.mkdir(parents=True)
    (mine / "Home.tsx").write_text('const c = "#ffffff"\n', encoding="utf-8")

    report = find_hardcoded(str(tmp_path))
    files = {hit["file"] for hit in report["hits"]}
    assert any("Home.tsx" in f for f in files)
    assert not any("brand.ts" in f for f in files)
    assert not any("badge" in f for f in files)


def test_find_hardcoded_exclude_fragment(tmp_path):
    data = tmp_path / "data" / "shared"
    data.mkdir(parents=True)
    (data / "dump.ts").write_text('const c = "#ffffff"\n', encoding="utf-8")
    assert find_hardcoded(str(tmp_path))["hit_count"] == 1
    assert find_hardcoded(str(tmp_path), exclude="data/")["hit_count"] == 0


def test_find_inconsistent_reads_utility_classes(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    markup = (
        '<Box className="gap-md px-lg py-md">\n'
        '<Text className="gap-md px-lg text-sm">x</Text>\n'
        '<View className="gap-xxl gap-x-md space-y-lg" />\n'
    )
    (src / "Screen.tsx").write_text(markup, encoding="utf-8")
    report = find_inconsistent(str(src), rare=1)
    used = dict(report["utility_spacing"]["values"])
    assert used["md"] == 4
    assert used["lg"] == 3
    assert "x" not in used and "y" not in used
    assert "xxl" in report["utility_spacing"]["outliers"]
    assert dict(report["utility_text"]["values"])["sm"] == 1


def test_find_inconsistent(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    kt = "Spacer(Modifier.height(8.dp))\nrow(16.dp)\nText(fontSize = 13.sp)\nfoo(5.dp)\n"
    (src / "Screen.kt").write_text(kt, encoding="utf-8")
    (src / "ui.tsx").write_text('<div className="p-[13px]">x</div>\n', encoding="utf-8")
    report = find_inconsistent(str(src), rare=1, grid=4)
    spacing = dict(report["spacing"]["values"])
    assert {"8", "16", "5"} <= set(spacing)
    assert "5" in report["spacing"]["off_grid"]
    assert "13" in dict(report["text_size"]["values"])
    assert report["arbitrary"] and "p-[13px]" in report["arbitrary"][0]["text"]


def test_find_format(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    java = (
        "package com.x;\n"
        "import java.util.List;\n"
        "import java.util.Map;\n"
        "class Foo {\n"
        "    List<String> a = new java.util.ArrayList<>();\n"
        "}\n"
    )
    (src / "Foo.java").write_text(java, encoding="utf-8")
    (src / "two.json").write_text('{\n  "a": 1\n}\n', encoding="utf-8")
    (src / "four.json").write_text('{\n    "a": 1\n}\n', encoding="utf-8")
    (src / "b.json").write_text('{\n  "b": 2\n}\n', encoding="utf-8")
    report = find_format(str(src))
    assert any("ArrayList" in h["match"] for h in report["inline_fqn"])
    assert any(u["name"] == "Map" for u in report["unused_imports"])
    assert report["json_style"]["majority"] == "2sp"
    assert any("four.json" in o["file"] for o in report["json_style"]["outliers"])


def test_find_duplication(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    block = "\n".join(f"line content number {i} here" for i in range(6))
    (src / "a.py").write_text(block + "\nunique a\n", encoding="utf-8")
    (src / "b.py").write_text("unique b\n" + block + "\n", encoding="utf-8")
    report = find_duplication(str(src), window=6)
    assert report["duplicate_blocks"] >= 1


@pytest.mark.skipif(not _HAS_GIT, reason="git not available")
def test_commit_style(tmp_path):
    report = commit_style(str(_make_repo(tmp_path)), 30)
    assert report["sampled"] == 2
    assert "feat" in report["prefixes"] and "fix" in report["prefixes"]
    assert report["conventional_percent"] == 100.0


@pytest.mark.skipif(not _HAS_GIT, reason="git not available")
def test_commit_context(tmp_path):
    repo = _make_repo(tmp_path)
    (repo / "c.txt").write_text("c", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True, text=True)
    report = commit_context(str(repo))
    assert "c.txt" in report["files"]
    assert report["style"]["sampled"] == 2
