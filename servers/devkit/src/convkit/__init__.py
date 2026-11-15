"""convkit: developer-convention guidance plus git and static-analysis checks."""
from __future__ import annotations

from .analyze import find_duplication, find_format, find_hardcoded, find_inconsistent
from .git import commit_style, recent_subjects
from .guide import digest, guide, index, topics

__all__ = [
    "guide",
    "index",
    "digest",
    "topics",
    "commit_style",
    "recent_subjects",
    "find_hardcoded",
    "find_duplication",
    "find_inconsistent",
    "find_format",
]
