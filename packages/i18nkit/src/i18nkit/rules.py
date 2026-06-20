"""Embedded i18n conventions (self-contained guidance)."""
from __future__ import annotations

_RULES = [
    "All user-facing text comes from translation files; never hardcode strings, and never use a "
    'fallback like t("KEY") || "default".',
    "Every locale must stay in sync: a key present in one must exist in all of them.",
    "Keys: stable and namespaced (dot paths or dotted UPPER_SNAKE); reuse existing groups before adding one.",
    "Placeholders ({name}, {0}, %s) must match across every locale of a key.",
    "Spanish: neutral, no voseo (e.g. 'Pega' not 'Pegá', 'Aquí' not 'Acá').",
    "Match the source/vanilla phrasing and capitalization of the target locale where one exists.",
]


def guide() -> str:
    """Render the embedded i18n conventions."""
    return "\n".join(["# i18n conventions", *(f"- {rule}" for rule in _RULES)])
