"""Structure and JSON-convention checks for a multiloader mod version folder."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .props import java_for_mc, parse_properties
from .scan import LOADERS, parse_version_dir

_REPOSITORIES = re.compile(r"\brepositories\s*\{")


def check_structure(version_path: str | Path) -> dict[str, Any]:
    """Validate multiloader structure and conventions; return a structured report."""
    base = Path(version_path)
    issues: list[str] = []

    for required in ("gradle.properties", "settings.gradle", "build.gradle"):
        if not (base / required).exists():
            issues.append(f"missing {required}")

    common_src = base / "common" / "src"
    if common_src.is_dir():
        java_in_common = list(common_src.rglob("*.java"))
        if java_in_common:
            issues.append(f"{len(java_in_common)} .java file(s) in common/ (common must be resources only)")

    present = [loader for loader in LOADERS if (base / loader).is_dir()]
    if not present:
        issues.append("no loaders found")
    elif "fabric" not in present:
        issues.append("missing fabric loader")

    _modid, version = parse_version_dir(base.name)
    expected_java = java_for_mc(version) if version else None
    props = parse_properties(base / "gradle.properties") if (base / "gradle.properties").is_file() else {}
    declared = props.get("javaVersion") or props.get("java_version")
    if expected_java and declared and declared.isdigit() and int(declared) != expected_java:
        issues.append(f"javaVersion={declared} but MC {version} expects Java {expected_java}")

    for loader in present:
        build = base / loader / "build.gradle"
        if build.is_file() and _REPOSITORIES.search(build.read_text(encoding="utf-8", errors="replace")):
            issues.append(f"{loader}/build.gradle has a 'repositories' block (canonical: root-only)")

    return {
        "path": str(base),
        "mc_version": version,
        "loaders": present,
        "expected_java": expected_java,
        "ok": not issues,
        "issues": issues,
    }


def check_json(version_path: str | Path) -> dict[str, Any]:
    """Scan assets/ and data/ JSON for trailing newline and CRLF (byte-level conventions)."""
    base = Path(version_path)
    roots = [base / loader for loader in LOADERS] + [base / "common"]
    violations: list[dict[str, Any]] = []
    checked = 0
    for module in roots:
        resources = module / "src" / "main" / "resources"
        for sub in ("assets", "data"):
            tree = resources / sub
            if not tree.is_dir():
                continue
            for f in tree.rglob("*.json"):
                checked += 1
                raw = f.read_bytes()
                problems: list[str] = []
                if not raw:
                    problems.append("empty")
                else:
                    if raw[-1:] == b"\n":
                        problems.append("trailing newline")
                    if b"\r" in raw:
                        problems.append("CRLF")
                if problems:
                    violations.append({"file": f.relative_to(base).as_posix(), "problems": problems})
    return {"checked": checked, "clean": not violations, "violations": violations[:200]}
