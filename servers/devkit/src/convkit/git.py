"""Git commit-style analysis."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

_CONVENTIONAL = re.compile(r"^(feat|fix|chore|refactor|docs|test|perf|build|ci|style|revert)(\([^)]+\))?!?:")


def _git(path: str | Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(path or "."), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    return result.stdout


def recent_subjects(path: str | Path, count: int) -> list[str]:
    out = _git(path, ["log", f"-{count}", "--pretty=format:%s"])
    return [line for line in out.splitlines() if line.strip()]


def commit_style(path: str = "", count: int = 30) -> dict[str, Any]:
    """Summarize the repo's recent commit-subject style: prefixes, conventional %, length, case."""
    subjects = recent_subjects(path, count)
    if not subjects:
        return {"error": "no commits found (is this a git repo?)", "path": str(path or ".")}
    conventional = [s for s in subjects if _CONVENTIONAL.match(s)]
    prefixes: dict[str, int] = {}
    for subject in conventional:
        prefix = _CONVENTIONAL.match(subject).group(1)
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    lengths = [len(s) for s in subjects]
    lowercase = sum(1 for s in subjects if not s[:1].isalpha() or s[:1].islower())
    return {
        "path": str(path or "."),
        "sampled": len(subjects),
        "conventional_percent": round(100 * len(conventional) / len(subjects), 1),
        "prefixes": dict(sorted(prefixes.items(), key=lambda kv: kv[1], reverse=True)),
        "avg_subject_length": round(sum(lengths) / len(lengths), 1),
        "lowercase_percent": round(100 * lowercase / len(subjects), 1),
        "recent": subjects[:10],
    }
