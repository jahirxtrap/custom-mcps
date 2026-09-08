"""Embedded i18n conventions (self-contained guidance)."""
from __future__ import annotations

_RULES = [
    "All user-facing text comes from the translation files. Never hardcode a string and never "
    't("KEY") || "default" -- a missing key is added, not patched at the call site.',
    "Keys are camelCase, grouped per feature namespace: t(\"product:addToCart\"). The underscore "
    "is the library's reserved grammar (_one, _other, _male), so keep it out of the key body.",
    "A default namespace (usually 'common') holds the generic strings -- actions, field labels, "
    "validation, states -- and is read with no prefix. Look there first; a namespace restating it "
    "is a second copy that drifts. It may hold keys nothing uses yet: it is the catalogue.",
    "A key is a meaning, not a string: two features saying the same word each keep their own.",
    "Pluralization belongs to the library: t(\"cart:units\", {count}) resolves units_one / "
    "units_other. A count === 1 ternary breaks on the first locale with more than two forms; CLDR "
    "defines up to six (zero, one, two, few, many, other) and the categories come from the "
    "standard, not from you.",
    "Interpolate, never concatenate -- one string with {{placeholders}}. Word order and grammar "
    "differ per language, and a translator cannot fix a sentence they never see whole.",
    "Placeholders must match across every locale of a key.",
    "Money, numbers and dates are formatted per locale at render time; store raw values.",
    "Enum values are never displayed as they arrive: one key per value.",
    "Every locale stays in sync, and adding a language is data only -- a folder of JSON and "
    "nothing else, no code change on either side.",
    "Spanish: neutral, no voseo ('Pega' not 'Pegá', 'Aquí' not 'Acá').",
    "Where a source or vanilla locale exists, match its phrasing and capitalization.",
]


def guide() -> str:
    """Render the embedded i18n conventions."""
    return "\n".join(["# i18n conventions", *(f"- {rule}" for rule in _RULES)])
