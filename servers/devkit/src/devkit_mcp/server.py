"""devkit MCP server: the user's development conventions, consultable and verifiable."""
from __future__ import annotations

import json

from convkit import (
    commit_context as _commit_context,
    commit_style as _commit_style,
    find_duplication as _find_duplication,
    find_hardcoded as _find_hardcoded,
    guide as _guide,
)
from fastmcp import FastMCP

mcp = FastMCP(name="devkit")


@mcp.tool
def conventions(topic: str = "") -> str:
    """Return the embedded developer conventions, all of them or one topic:
    commit / code / dry / hardcoding / design / patterns / docs / naming."""
    return _guide(topic)


@mcp.tool
def commit_style(repo: str = "", count: int = 30) -> str:
    """Analyze a git repo's recent commit subjects: prefixes used, % conventional, average length,
    lowercase rate, recent samples. The style to imitate when committing here."""
    return json.dumps(_commit_style(repo, count))


@mcp.tool
def commit_context(repo: str = "", rev_range: str = "") -> str:
    """Gather what's needed to write a commit message in the repo's style: staged (or rev_range)
    diffstat, changed files, recent subjects, and the commit_style summary. Never add Co-Authored-By."""
    return json.dumps(_commit_context(repo, rev_range))


@mcp.tool
def find_hardcoded(path: str, allow: str = "") -> str:
    """Scan code for hardcoded colors (hex, Color(0xFF...) on any stack) plus web px/rem size values
    and raw Tailwind palette classes that should live in a token/theme file. Compose .dp/.sp spacing
    is idiomatic and not flagged. `allow` = comma-separated extra filename substrings to skip."""
    extra = [token.strip() for token in allow.split(",") if token.strip()] if allow else None
    return json.dumps(_find_hardcoded(path, extra))


@mcp.tool
def find_duplication(path: str, window: int = 6) -> str:
    """Find repeated normalized line blocks (~window lines) across the code -- candidates to unify
    (DRY). Heuristic; some matches may be legit boilerplate."""
    return json.dumps(_find_duplication(path, window))


def main() -> None:
    mcp.run()
