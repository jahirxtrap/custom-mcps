"""i18n MCP server: keep translations in sync. Engine-agnostic."""
from __future__ import annotations

import json

from fastmcp import FastMCP
from i18nkit import (
    check_format as _check_format,
    completeness as _completeness,
    find_unused as _find_unused,
    guide as _guide,
    locale_diff as _locale_diff,
)

mcp = FastMCP(name="i18n")


@mcp.tool
def locale_diff(path: str, base: str = "") -> str:
    """Compare every locale JSON under `path` against the base (auto en/en_us, or `base`):
    report keys missing from each locale and keys it has that the base lacks. Handles flat and
    nested JSON (nested is flattened to dot-paths)."""
    return json.dumps(_locale_diff(path, base))


@mcp.tool
def completeness(path: str, base: str = "") -> str:
    """Report the percentage of base keys translated in each locale under `path`."""
    return json.dumps(_completeness(path, base))


@mcp.tool
def check_format(path: str, base: str = "") -> str:
    """Report keys whose placeholders ({name}, {0}, %s) differ from the base locale, plus empty
    translation values, across the locales under `path`."""
    return json.dumps(_check_format(path, base))


@mcp.tool
def find_unused(path: str, src: str, patterns: str = "") -> str:
    """Cross the base locale keys with translation calls in `src` code: report keys used but not
    defined (broken at runtime) and defined but not used (dead). `patterns` is an optional JSON
    array of regexes; the default matches t("KEY") and tr("KEY")."""
    parsed = json.loads(patterns) if patterns else None
    return json.dumps(_find_unused(path, src, parsed))


@mcp.tool
def i18n_guide() -> str:
    """Return the embedded i18n conventions (no hardcoded strings, locales in sync,
    placeholder consistency, key naming, Spanish neutral)."""
    return _guide()


def main() -> None:
    mcp.run()
