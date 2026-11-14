"""Compare loader source trees (sync) and search for a symbol across loaders."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .scan import LOADERS


def _java_hashes(loader_dir: Path) -> dict[str, str]:
    src = loader_dir / "src" / "main" / "java"
    if not src.is_dir():
        return {}
    return {
        f.relative_to(src).as_posix(): hashlib.sha1(f.read_bytes()).hexdigest()
        for f in src.rglob("*.java")
    }


def loader_sync(version_path: str | Path) -> dict[str, Any]:
    """Compare shared Java files across loaders.

    Files that live in only one loader (loader-specific entrypoints) are ignored.
    `differing` = same path in >=2 loaders but different content (the real drift bug).
    `partial` = same path in >=2 loaders but not all of them (a likely missed copy).
    """
    base = Path(version_path)
    present = [loader for loader in LOADERS if (base / loader).is_dir()]
    trees = {loader: _java_hashes(base / loader) for loader in present}
    all_files: set[str] = set()
    for tree in trees.values():
        all_files |= set(tree)
    differing: list[str] = []
    partial: dict[str, list[str]] = {}
    for rel in sorted(all_files):
        owners = [loader for loader in present if rel in trees[loader]]
        if len(owners) < 2:
            continue
        if len({trees[loader][rel] for loader in owners}) > 1:
            differing.append(rel)
        if len(owners) < len(present):
            partial[rel] = owners
    return {
        "loaders": present,
        "differing": differing,
        "differing_count": len(differing),
        "partial": partial,
        "file_count": len(all_files),
        "note": "Same path, different content across loaders. Entrypoints differ by design; "
        "focus on files you expect to be identical, or compare against a previous run.",
    }


def find_symbol(version_path: str | Path, symbol: str) -> dict[str, Any]:
    """Find a symbol (API, class, method) in the Java source of every loader."""
    base = Path(version_path)
    hits: list[dict[str, Any]] = []
    for loader in LOADERS:
        src = base / loader / "src" / "main" / "java"
        if not src.is_dir():
            continue
        for f in src.rglob("*.java"):
            for number, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if symbol in line:
                    rel = f.relative_to(base).as_posix()
                    hits.append({"loader": loader, "file": rel, "line": number, "text": line.strip()[:160]})
    return {"symbol": symbol, "count": len(hits), "hits": hits[:200]}
