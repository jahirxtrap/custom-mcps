"""Structure, JSON, and access-control checks for a multiloader mod version folder."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .props import java_for_mc, parse_mc_version, parse_properties
from .scan import LOADERS, parse_version_dir

_AT_REL = ("src", "main", "resources", "META-INF", "accesstransformer.cfg")


def _mod_id(base: Path) -> str:
    props = parse_properties(base / "gradle.properties") if (base / "gradle.properties").is_file() else {}
    if props.get("mod_id"):
        return props["mod_id"]
    modid, _ = parse_version_dir(base.name)
    return modid or ""


def check_structure(version_path: str | Path) -> dict[str, Any]:
    """Validate multiloader structure and conventions; return a structured report."""
    base = Path(version_path)
    issues: list[str] = []

    for required in ("gradle.properties", "settings.gradle", "build.gradle"):
        if not (base / required).exists():
            issues.append(f"missing {required}")

    common_src = base / "common" / "src"
    if common_src.is_dir() and list(common_src.rglob("*.java")):
        count = len(list(common_src.rglob("*.java")))
        issues.append(f"{count} .java file(s) in common/ (common must be resources only)")

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

    mod_id = _mod_id(base)
    if mod_id:
        mixin_present = {
            loader: (base / loader / "src" / "main" / "resources" / f"{mod_id}.mixins.json").is_file()
            for loader in present
        }
        if any(mixin_present.values()):
            for loader in present:
                if not mixin_present[loader]:
                    issues.append(f"{loader} missing {mod_id}.mixins.json (other loaders have it)")
        prefix = f"{mod_id}$"
        for loader in present:
            src = base / loader / "src" / "main" / "java"
            if not src.is_dir():
                continue
            for f in src.rglob("*.java"):
                if prefix in f.read_text(encoding="utf-8", errors="replace"):
                    rel = f.relative_to(base).as_posix()
                    issues.append(f"{loader}: '{prefix}' prefix in {rel} (mixin convention forbids it)")
                    break

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


def check_access(version_path: str | Path) -> dict[str, Any]:
    """Check Access Widener / Access Transformer presence, cross-loader parity, and AW header."""
    base = Path(version_path)
    _modid, version = parse_version_dir(base.name)
    mod_id = _mod_id(base)
    present = [loader for loader in LOADERS if (base / loader).is_dir()]

    aw_path = base / "fabric" / "src" / "main" / "resources" / f"{mod_id}.aw"
    has_aw = "fabric" in present and bool(mod_id) and aw_path.is_file()
    has_at = {
        loader: (base.joinpath(loader, *_AT_REL)).is_file()
        for loader in present
        if loader in ("forge", "neoforge")
    }

    issues: list[str] = []
    if has_aw or any(has_at.values()):
        if "fabric" in present and not has_aw:
            issues.append("fabric missing <mod_id>.aw while other loaders declare access")
        for loader, ok in has_at.items():
            if not ok:
                issues.append(f"{loader} missing META-INF/accesstransformer.cfg while other loaders declare access")

    aw_header: str | None = None
    if has_aw and version:
        lines = aw_path.read_text(encoding="utf-8", errors="replace").splitlines()
        first = lines[0] if lines else ""
        parts = first.split("\t")
        want_version = "v2" if parse_mc_version(version) >= (26, 1) else "v1"
        want_ns = "official" if want_version == "v2" else "named"
        if len(parts) < 3 or parts[0] != "accessWidener":
            issues.append(f"AW header must be TAB-separated 'accessWidener<TAB>vN<TAB>ns' (got {first!r})")
        else:
            aw_header = first
            if parts[1] != want_version or parts[2] != want_ns:
                issues.append(f"AW header {parts[1]}/{parts[2]} but MC {version} expects {want_version}/{want_ns}")

    return {
        "path": str(base),
        "mod_id": mod_id,
        "has_aw": has_aw,
        "has_at": has_at,
        "aw_header": aw_header,
        "ok": not issues,
        "issues": issues,
    }
