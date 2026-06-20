"""convkit: developer-convention guidance plus git and static-analysis checks."""
from __future__ import annotations

from .analyze import find_duplication, find_hardcoded
from .git import commit_context, commit_style, recent_subjects
from .guide import guide, topics

__all__ = [
    "guide",
    "topics",
    "commit_style",
    "commit_context",
    "recent_subjects",
    "find_hardcoded",
    "find_duplication",
]
