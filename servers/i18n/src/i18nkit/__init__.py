"""i18nkit: read-only translation checks — locale diff, completeness, placeholders, unused keys."""
from __future__ import annotations

from .diff import completeness, locale_diff
from .format import check_format, placeholders
from .parse import (
    PLURAL_FORMS,
    base_key,
    flatten,
    layout,
    list_locales,
    load_catalog,
    load_locale,
    pick_base,
    plural_form,
    roots,
)
from .rules import guide
from .scan import find_unused, used_keys

__all__ = [
    "load_locale",
    "load_catalog",
    "flatten",
    "layout",
    "list_locales",
    "pick_base",
    "base_key",
    "plural_form",
    "roots",
    "PLURAL_FORMS",
    "locale_diff",
    "completeness",
    "check_format",
    "placeholders",
    "find_unused",
    "used_keys",
    "guide",
]
