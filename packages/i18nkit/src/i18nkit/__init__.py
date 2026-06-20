"""i18nkit: read-only translation checks — locale diff, completeness, placeholders, unused keys."""
from __future__ import annotations

from .diff import completeness, locale_diff
from .format import check_format, placeholders
from .parse import flatten, list_locales, load_locale, pick_base
from .rules import guide
from .scan import find_unused, used_keys

__all__ = [
    "load_locale",
    "flatten",
    "list_locales",
    "pick_base",
    "locale_diff",
    "completeness",
    "check_format",
    "placeholders",
    "find_unused",
    "used_keys",
    "guide",
]
