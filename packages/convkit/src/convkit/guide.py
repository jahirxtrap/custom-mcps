"""Embedded developer conventions by topic (verified against the user's real projects)."""
from __future__ import annotations

_TOPICS: dict[str, list[str]] = {
    "commit": [
        "Conventional commits: feat / fix / chore / refactor / docs. Short, lowercase subject "
        "(e.g. 'feat: tab system', 'fix: some fixes').",
        "NEVER add Co-Authored-By or any attribution footer.",
        "Changelog: plain past-tense bullets (Added/Fixed/Updated/Removed), no headers/versions/"
        "dates, derived from the commits since the last release; replace the whole file.",
        "Match the repo's existing style before committing (run commit_style).",
    ],
    "code": [
        "No comments. Self-explanatory names; a short docstring only when a constraint cannot be "
        "expressed in code itself.",
        "English for code and diagnostics; respond to the user in Spanish.",
        "Latest stable versions of everything; nothing obsolete.",
        "Terse, expression-oriented; trust platform guarantees over defensive boilerplate.",
        "Imports at the top of the file.",
    ],
    "dry": [
        "Extract LOGIC into reusable modules; keep UI construction where it is (do not over-extract widgets).",
        "Check the component/util catalog before building anything new -- most primitives already exist.",
        "No duplicated code; unify into shared methods/components.",
        "Thin routers/handlers delegate to services; the UI never calls the network (axios/fetch) "
        "directly -- it goes through a service.",
    ],
    "hardcoding": [
        "No hardcoded user-facing text -- use i18n keys (t()/tr()); never t('KEY') || 'fallback'.",
        "No hardcoded colors or sizes -- use tokens from one place (themes.ts / Palette.kt). No "
        "scattered #hex, Color(0xFF...), .dp/.sp, or raw Tailwind palette classes.",
        "New content is data (JSON) + a registry, not a new class; no magic numbers.",
        "Icons come from a library, not inline <svg>.",
    ],
    "design": [
        "Centralize tokens (colors, sizes, accents) in one file; expose a semantic palette.",
        "Unified, catalogued components so the whole system looks consistent (Form*/Modal* on web, "
        "SettingsGroup/PreferenceRow on Compose).",
        "One accent/theme system; everything else stays neutral and token-driven.",
    ],
    "patterns": [
        "Unified API response envelope: {success, status, message, data}; clients read .success, never .ok.",
        "Auto-discovery: drop a file (router / MCP tool / server) and it registers itself; no manual wiring.",
        "Data-driven: add content via JSON + a registry, with base/patch inheritance; never a class per item.",
        "Extract logic to reusable modules (services / RefCounted); the UI stays in the panel.",
        "Version contract for client/server apps (pyproject supported-app / supported-cli).",
        "Storage/config lives in a single module, not scattered.",
    ],
    "docs": [
        "README is the public showcase (prose, capabilities); CLAUDE.md is the internal guide "
        "(architecture, how to extend, hard rules).",
        "README style: no em-dash; parentheses for inline info; '=>' for 'leads to'; ':' after bold names.",
        "No trailing newline in README or data JSON (last byte is the last visible character).",
    ],
    "naming": [
        "Consistent, prose-based names with related words; do not mix get/fetch/load (or build/make/"
        "create) for the same idea -- names should read as one coherent system.",
        "By context: components PascalCase; hooks useXxx; vars/functions camelCase; locale keys "
        "UPPER_SNAKE with dot namespacing; backend wire fields snake_case; Java vars named by type.",
    ],
}


def topics() -> list[str]:
    return list(_TOPICS)


def guide(topic: str = "") -> str:
    """Render all conventions, or a single topic (commit/code/dry/hardcoding/design/patterns/docs/naming)."""
    selected = {topic: _TOPICS[topic]} if topic in _TOPICS else _TOPICS
    lines = ["# Developer conventions"]
    for name, items in selected.items():
        lines += ["", f"## {name}"]
        lines += [f"- {item}" for item in items]
    return "\n".join(lines)
