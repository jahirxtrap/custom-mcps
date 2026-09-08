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

mcp = FastMCP(
    name="i18n",
    instructions=(
        "Translation locales kept in sync, complete and consistent. Read-only: it reports, it "
        "never edits a locale.\n"
        "Tools: locale_diff, completeness, check_format, find_unused, i18n_guide.\n"
        "Reach for it whenever locale files change or a language is added. It reads both layouts "
        "-- one file per locale (en.json, es.json) and one folder per locale holding a file per "
        "namespace, addressed as 'namespace:key' -- and it compares keys without their plural "
        "suffix, so a locale with more CLDR forms than the base is not a diff."
    ),
)


@mcp.tool
def locale_diff(path: str, base: str = "") -> str:
    """Compare every locale under `path` against the base (auto en/en_us, or `base`): keys missing
    from each locale, keys the base lacks, and plural_mismatch (a key pluralized on one side only,
    which breaks the count lookup). Plural suffixes are ignored when matching, so a locale holding
    more CLDR forms than the base is not reported. Reads both the one-file-per-locale layout and
    the one-folder-per-locale one (keys become 'namespace:key')."""
    return json.dumps(_locale_diff(path, base))


@mcp.tool
def completeness(path: str, base: str = "") -> str:
    """Report the percentage of base keys translated in each locale under `path`, counting a key
    as present when any of its plural forms is."""
    return json.dumps(_completeness(path, base))


@mcp.tool
def check_format(path: str, base: str = "") -> str:
    """Report keys whose placeholders ({{name}}, {name}, {0}, %s) differ from the base locale,
    plus empty translation values, across the locales under `path`."""
    return json.dumps(_check_format(path, base))


@mcp.tool
def find_unused(path: str, src: str, patterns: str = "", default_ns: str = "common",
                ignore: str = "") -> str:
    """Cross the keys the code asks for with the keys the locales declare: used_not_declared
    (renders as the key at runtime) and declared_not_used (dead). A plural resolves through any of
    its forms. On the namespaced layout an unprefixed t("save") resolves to `default_ns`, and that
    namespace is exempt from the dead-key report because it is the shared catalogue. `ignore` is a
    comma-separated list of keys only a variable names (one per enum value). `patterns` is an
    optional JSON array of regexes; the default matches t("KEY") and tr("KEY")."""
    parsed = json.loads(patterns) if patterns else None
    return json.dumps(_find_unused(path, src, parsed, default_ns, ignore))


@mcp.tool
def i18n_guide() -> str:
    """Return the embedded i18n conventions: text is data, camelCase keys per namespace with a
    shared default one, pluralization through the library, interpolation over concatenation,
    locale-formatted numbers and dates, and adding a language as data only."""
    return _guide()


def main() -> None:
    mcp.run()
