"""devkit MCP server: the user's development conventions, consultable and verifiable."""
from __future__ import annotations

import json

from convkit import (
    commit_context as _commit_context,
    commit_style as _commit_style,
    find_duplication as _find_duplication,
    find_format as _find_format,
    find_hardcoded as _find_hardcoded,
    find_inconsistent as _find_inconsistent,
    guide as _guide,
)
from fastmcp import FastMCP

mcp = FastMCP(
    name="devkit",
    instructions=(
        "Development conventions and the checks that verify them, across stacks "
        "(Java, Kotlin/Compose, TypeScript/React, Python, GDScript). Read-only.\n"
        "Tools: conventions, commit_style, commit_context, find_hardcoded, find_inconsistent, "
        "find_format, find_duplication.\n"
        "Read conventions before writing code and again before committing; run the find_* checks "
        "over the code you touched."
    ),
)


@mcp.tool
def conventions(topic: str = "") -> str:
    """Return the embedded developer conventions, all of them or one topic: commit / code / ssot /
    dry / boundaries / scope / hardcoding / data / i18n / runtime / verify / design / spacing /
    format / patterns / docs / naming."""
    return _guide(topic)


@mcp.tool
def commit_style(repo: str = "", count: int = 30) -> str:
    """Analyze a git repo's recent commit subjects: prefixes used, % conventional, average length,
    lowercase rate, recent samples. The style to imitate when committing here."""
    return json.dumps(_commit_style(repo, count))


@mcp.tool
def commit_context(repo: str = "", rev_range: str = "") -> str:
    """Gather what's needed to write a commit message in the repo's style: staged (or rev_range)
    diffstat, changed files, recent subjects, and the commit_style summary. Never add Co-Authored-By.
    When the change answers an issue, add the required footer (conventions('commit'))."""
    return json.dumps(_commit_context(repo, rev_range))


@mcp.tool
def find_hardcoded(path: str, allow: str = "", exclude: str = "") -> str:
    """Scan code for hardcoded colors (hex, Color(0xFF...) on any stack) plus web px/rem size values
    and raw Tailwind palette classes that should live in a token/theme file. Compose .dp/.sp spacing
    is idiomatic and not flagged. Token files are skipped by name or by a theme/tokens/palette
    parent folder. `allow` = extra filename substrings to skip; `exclude` = extra path fragments
    (vendored trees, data folders) on top of node_modules/.venv/build/generated and
    components/ui, components/rnr, src/generated."""
    extra = [token.strip() for token in allow.split(",") if token.strip()] if allow else None
    return json.dumps(_find_hardcoded(path, extra, exclude))


@mcp.tool
def find_inconsistent(path: str, rare: int = 2, grid: int = 4, exclude: str = "") -> str:
    """Snapshot the spacing and text-size scales in use and flag what breaks consistency. Numeric
    scales (Compose .dp/.sp, CSS font-size) carry the rare-value and off-`grid` checks; the
    Tailwind/NativeWind classes in use (p/m/gap/space, text-*) come back under utility_* where the
    tokens ARE the scale, so only rare one-offs matter. Arbitrary `-[Npx]` values are listed
    separately. `exclude` adds path fragments to skip."""
    return json.dumps(_find_inconsistent(path, rare, grid, exclude))


@mcp.tool
def find_format(path: str, exclude: str = "") -> str:
    """Flag AI-typical format breaks that formatters miss: inline fully-qualified class names
    (Java/Kotlin -- import them), unused imports (Java/Kotlin/TS), tab+space mixed indentation, and
    JSON files whose indent style differs from the tree majority. Read-only, multi-stack.
    `exclude` adds path fragments to skip."""
    return json.dumps(_find_format(path, exclude))


@mcp.tool
def find_duplication(path: str, window: int = 6, exclude: str = "") -> str:
    """Find repeated normalized line blocks (~window lines) across the code -- candidates to unify
    (DRY). Heuristic; some matches may be legit boilerplate. `exclude` adds path fragments to skip,
    which matters on a tree carrying generated or uploaded files."""
    return json.dumps(_find_duplication(path, window, exclude))


def main() -> None:
    mcp.run()
