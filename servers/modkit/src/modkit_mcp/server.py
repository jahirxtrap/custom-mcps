"""modkit MCP server: read-only helpers for multiloader mod workspaces."""
from __future__ import annotations

import json

from fastmcp import FastMCP
from loaderkit import (
    check_json as _check_json,
    check_structure as _check_structure,
    find_symbol as _find_symbol,
    list_mods as _list_mods,
    loader_sync as _loader_sync,
    mod_info as _mod_info,
)

mcp = FastMCP(name="modkit")


@mcp.tool
def list_mods(root: str = ".") -> str:
    """List every multiloader mod under `root` (default cwd) with its version folders and the
    most recent one. Detects mods by the <modid>-<version>-multi convention; no names hardcoded."""
    return json.dumps(_list_mods(root or "."))


@mcp.tool
def mod_info(path: str) -> str:
    """Read a version folder's gradle.properties (MC version, loader versions, mod version, deps)
    plus the Java version expected for that MC version."""
    return json.dumps(_mod_info(path))


@mcp.tool
def loader_sync(path: str) -> str:
    """Compare the Java source of fabric/forge/neoforge in a version folder; report files missing
    from a loader or differing between loaders (catches a loader left with a stale copy)."""
    return json.dumps(_loader_sync(path))


@mcp.tool
def check_structure(path: str) -> str:
    """Validate multiloader structure and conventions: common/ has no .java, loaders present,
    gradle files in place, javaVersion matches the MC version, repositories only in the root build."""
    return json.dumps(_check_structure(path))


@mcp.tool
def check_json(path: str) -> str:
    """Scan assets/ and data/ JSON in a version folder for byte-level convention breaks:
    a trailing newline (the file must end in } or ]) and CRLF line endings."""
    return json.dumps(_check_json(path))


@mcp.tool
def find_symbol(path: str, symbol: str) -> str:
    """Find a symbol (API, class, method) in the Java source of all loaders in a version folder;
    returns file + line + text per hit. Useful to locate what to change during a migration."""
    return json.dumps(_find_symbol(path, symbol))


def main() -> None:
    mcp.run()
