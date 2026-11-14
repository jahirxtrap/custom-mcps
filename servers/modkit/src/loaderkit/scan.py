"""Scan a workspace for multiloader mods and their version folders."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .props import java_for_mc, parse_mc_version, parse_properties

LOADERS = ("fabric", "forge", "neoforge")
_VERSION_DIR = re.compile(r"^(?P<modid>.+)-(?P<version>\d[\w.]*)-multi$")


def parse_version_dir(name: str) -> tuple[str | None, str | None]:
    match = _VERSION_DIR.match(name)
    if match:
        return match.group("modid"), match.group("version")
    return None, None


def is_version_dir(path: Path) -> bool:
    return (
        path.is_dir()
        and path.name.endswith("-multi")
        and (path / "gradle.properties").is_file()
        and (path / "settings.gradle").exists()
    )


def find_version_dirs(mod_dir: Path) -> list[Path]:
    return sorted(p for p in mod_dir.iterdir() if is_version_dir(p))


def list_mods(root: str | Path) -> list[dict[str, Any]]:
    """List every mod under `root` with its version folders and the most recent one."""
    base = Path(root)
    mods: list[dict[str, Any]] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        version_dirs = find_version_dirs(child)
        if not version_dirs:
            continue
        versions = []
        for vd in version_dirs:
            modid, version = parse_version_dir(vd.name)
            versions.append({"version": version, "modid": modid, "dir": vd.name, "path": str(vd)})
        versions.sort(key=lambda item: parse_mc_version(item["version"] or "0"))
        mods.append({"mod": child.name, "versions": versions, "latest": versions[-1] if versions else None})
    return mods


def mod_info(version_path: str | Path) -> dict[str, Any]:
    """Read a version folder's gradle.properties plus its expected Java version."""
    base = Path(version_path)
    props = parse_properties(base / "gradle.properties") if (base / "gradle.properties").is_file() else {}
    modid, version = parse_version_dir(base.name)
    return {
        "path": str(base),
        "modid": modid,
        "mc_version": version,
        "expected_java": java_for_mc(version) if version else None,
        "loaders": [loader for loader in LOADERS if (base / loader).is_dir()],
        "properties": props,
    }
