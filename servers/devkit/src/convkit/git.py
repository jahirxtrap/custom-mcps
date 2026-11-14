"""Git commit-style analysis and commit-message context."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

_CONVENTIONAL = re.compile(r"^(feat|fix|chore|refactor|docs|test|perf|build|ci|style|revert)(\([^)]+\))?!?:")


def _git(repo: str | Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repo or "."), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    return result.stdout


def recent_subjects(repo: str | Path, count: int) -> list[str]:
    out = _git(repo, ["log", f"-{count}", "--pretty=format:%s"])
    return [line for line in out.splitlines() if line.strip()]


def commit_style(repo: str = "", count: int = 30) -> dict[str, Any]:
    """Summarize the repo's recent commit-subject style: prefixes, conventional %, length, case."""
    subjects = recent_subjects(repo, count)
    if not subjects:
        return {"error": "no commits found (is this a git repo?)", "repo": str(repo or ".")}
    conventional = [s for s in subjects if _CONVENTIONAL.match(s)]
    prefixes: dict[str, int] = {}
    for subject in conventional:
        prefix = _CONVENTIONAL.match(subject).group(1)
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    lengths = [len(s) for s in subjects]
    lowercase = sum(1 for s in subjects if not s[:1].isalpha() or s[:1].islower())
    return {
        "repo": str(repo or "."),
        "sampled": len(subjects),
        "conventional_percent": round(100 * len(conventional) / len(subjects), 1),
        "prefixes": dict(sorted(prefixes.items(), key=lambda kv: kv[1], reverse=True)),
        "avg_subject_length": round(sum(lengths) / len(lengths), 1),
        "lowercase_percent": round(100 * lowercase / len(subjects), 1),
        "recent": subjects[:10],
    }


def commit_context(repo: str = "", rev_range: str = "") -> dict[str, Any]:
    """Gather context to write a commit message in the repo's style (diffstat, files, style)."""
    scope = [rev_range] if rev_range else ["--cached"]
    diffstat = _git(repo, ["diff", "--stat", *scope]).strip()
    name_only = _git(repo, ["diff", "--name-only", *scope])
    if not diffstat:
        diffstat = _git(repo, ["diff", "--stat"]).strip()
        name_only = _git(repo, ["diff", "--name-only"])
    files = [line.strip() for line in name_only.splitlines() if line.strip()]
    return {
        "repo": str(repo or "."),
        "diffstat": diffstat,
        "files": files[:100],
        "style": commit_style(repo, 15),
        "note": "Draft a subject in the repo's style (see style.prefixes / style.recent). No Co-Authored-By.",
    }
