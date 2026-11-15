"""devkit MCP server: the user's development conventions, consultable and verifiable."""
from __future__ import annotations

import json

from convkit import (
    commit_style as _commit_style,
    find_comments as _find_comments,
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
        "Tools: conventions, commit_style, find_hardcoded, find_inconsistent, find_format, "
        "find_duplication, find_comments.\n"
        "The conventions are these, never what the code you see happens to do: do not infer them "
        "from the code. The core ones (code, commit, ssot, dry) arrive in your context when the "
        "session starts and after every compaction, so call conventions(topic) only for the other "
        "topics. Run commit_style on the repo before committing. Run the find_* checks once over "
        "the code you touched when the task is done, not after every edit. An edit that adds a "
        "comment, or a docstring over one line, repeating its name or explaining why, gets a notice "
        "from the plugin's PostToolUse hook: remove what it names."
    ),
)


@mcp.tool
def conventions(topic: str = "") -> str:
    """Return the developer conventions of one topic: commit / code / ssot / dry / boundaries / scope /
    hardcoding / data / i18n / runtime / verify / design / spacing / format / patterns / docs /
    naming. Without a topic it returns the index of topics, one line each. The core topics (code,
    commit, ssot, dry) are already in your context from the session start."""
    return _guide(topic)


@mcp.tool
def commit_style(path: str = "", count: int = 30) -> str:
    """Analyze a git repo's recent commit subjects: prefixes used, % conventional, average length,
    lowercase rate, recent samples. The style to imitate when committing there. `path` is the repo
    (or any folder inside it)."""
    return json.dumps(_commit_style(path, count))


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
def find_format(path: str, exclude: str = "", detail: bool = False) -> str:
    """Flag AI-typical format breaks that formatters miss: inline fully-qualified class names
    (Java/Kotlin -- import them), unused imports (Java/Kotlin/TS), tab+space mixed indentation, and
    JSON files whose indent style differs from the tree majority. Read-only, multi-stack. Every count
    is complete; each list shows 25 entries, or 100 with detail=true. `exclude` adds path fragments
    to skip."""
    return json.dumps(_find_format(path, exclude, detail))


@mcp.tool
def find_duplication(path: str, window: int = 6, exclude: str = "", detail: bool = False) -> str:
    """Find repeated normalized line blocks (~window lines) across the code -- candidates to unify
    (DRY). Heuristic; some matches may be legit boilerplate. Answers the occurrences per file and the
    ten largest blocks with a short sample; detail=true lists up to fifty blocks with every
    occurrence. `exclude` adds path fragments to skip, which matters on a tree carrying generated or
    uploaded files."""
    return json.dumps(_find_duplication(path, window, exclude, detail))


@mcp.tool
def find_comments(path: str, exclude: str = "", detail: bool = False) -> str:
    """Find what the no-comments convention forbids in the code under `path`: every comment line or
    block (directives such as noqa, ts-expect-error, shebangs and attributes excepted) and the
    docstrings that run over one line, only repeat the name they describe or carry rationale
    (because, so that, workaround, TODO). Python is read with its tokenizer and ast, so a `#` inside
    a string never counts and the docstring of a decorated definition (a tool's description, a
    route's) is data, not checked; Java/Kotlin/TS/JS/Rust/Go/C#/CSS (`//`, `/* */`), HTML/Svelte/Vue
    (`<!-- -->`), SQL (`--`) and GDScript/shell (`#`) by line. Complete counts; each list shows 25
    entries, or 100 with detail=true. `exclude` adds path fragments to skip."""
    return json.dumps(_find_comments(path, exclude, detail))


def main() -> None:
    mcp.run()
