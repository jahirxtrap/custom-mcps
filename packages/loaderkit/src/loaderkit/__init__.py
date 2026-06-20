"""loaderkit: read-only toolkit for multiloader mod workspaces (scan, parse, compare, checks)."""
from __future__ import annotations

from .checks import check_access, check_json, check_structure
from .compare import find_symbol, loader_sync
from .props import java_for_mc, parse_mc_version, parse_properties
from .scan import LOADERS, find_version_dirs, list_mods, mod_info, parse_version_dir

__all__ = [
    "LOADERS",
    "list_mods",
    "mod_info",
    "find_version_dirs",
    "parse_version_dir",
    "parse_properties",
    "parse_mc_version",
    "java_for_mc",
    "loader_sync",
    "find_symbol",
    "check_structure",
    "check_json",
    "check_access",
]
