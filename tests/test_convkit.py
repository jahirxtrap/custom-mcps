from __future__ import annotations

import shutil
import subprocess

import pytest
from convkit import (
    commit_context,
    commit_style,
    find_duplication,
    find_hardcoded,
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
    assert {"commit", "hardcoding", "patterns", "naming"} <= set(found)


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
