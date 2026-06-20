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
    """Report Java files that are missing from a loader or differ between loaders."""
    base = Path(version_path)
    present = [loader for loader in LOADERS if (base / loader).is_dir()]
    trees = {loader: _java_hashes(base / loader) for loader in present}
    all_files: set[str] = set()
    for tree in trees.values():
        all_files |= set(tree)
    missing: dict[str, list[str]] = {}
    differing: list[str] = []
    for rel in sorted(all_files):
        hashes = {loader: trees[loader].get(rel) for loader in present}
        absent = [loader for loader in present if hashes[loader] is None]
        if absent:
            missing[rel] = absent
        if len({h for h in hashes.values() if h is not None}) > 1:
            differing.append(rel)
    return {
        "loaders": present,
        "in_sync": not missing and not differing,
        "differing": differing,
        "missing": missing,
        "file_count": len(all_files),
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
