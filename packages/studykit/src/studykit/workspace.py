"""Create and manage a multi-area study workspace on disk."""
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

from .assets import (
    APA_CSL_README,
    BIB_HEADER,
    CITATION_APA,
    INDEX_TEMPLATE,
    KNOWLEDGE_TEMPLATE,
    MEMORY_LOG,
    MEMORY_PROFILE,
    VISUAL_GUIDE,
    WORKSPACE_CLAUDE,
    WRITING_RULES,
)
from .cite import bibtex_entry, bibtex_key


def _slug(name: str) -> str:
    norm = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    norm = re.sub(r"[^a-z0-9]+", "-", norm.strip().lower()).strip("-")
    return norm or "area"


def _write_if_absent(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def _create_area(root: Path, name: str) -> str:
    slug = _slug(name)
    base = root / "areas" / slug
    (base / "library" / "sources").mkdir(parents=True, exist_ok=True)
    (base / "library" / "notes").mkdir(parents=True, exist_ok=True)
    _write_if_absent(base / "knowledge.md", KNOWLEDGE_TEMPLATE.format(area=name))
    _write_if_absent(base / "references.bib", BIB_HEADER.format(area=name))
    _write_if_absent(base / "library" / "INDEX.md", INDEX_TEMPLATE.format(area=name))
    return slug


def workspace_init(path: str, areas: list[str] | None = None) -> dict[str, Any]:
    root = Path(path)
    for name in ("conventions", "styles", "memory", "areas"):
        (root / name).mkdir(parents=True, exist_ok=True)
    files = {
        root / "CLAUDE.md": WORKSPACE_CLAUDE,
        root / "conventions" / "writing-rules.md": f"{WRITING_RULES}\n\n{VISUAL_GUIDE}",
        root / "conventions" / "citation-apa.md": CITATION_APA,
        root / "styles" / "README.md": APA_CSL_README,
        root / "memory" / "profile.md": MEMORY_PROFILE,
        root / "memory" / "log.md": MEMORY_LOG,
    }
    created = [str(p.relative_to(root)) for p, content in files.items() if _write_if_absent(p, content)]
    slugs = [_create_area(root, name) for name in (areas or [])]
    return {"workspace": str(root), "created": created, "areas": slugs}


def area_add(path: str, name: str) -> dict[str, Any]:
    root = Path(path)
    if not (root / "areas").exists():
        raise FileNotFoundError("not a study workspace (missing areas/); run workspace_init first")
    return {"workspace": str(root), "area": _create_area(root, name)}


def reference_add(path: str, area: str, fields: dict[str, Any], file: str = "") -> dict[str, Any]:
    root = Path(path)
    slug = _slug(area)
    base = root / "areas" / slug
    if not base.exists():
        raise FileNotFoundError(f"area '{slug}' not found; add it with area_add")

    data = dict(fields)
    key = str(data.get("key", "")).strip() or bibtex_key(data)
    data["key"] = key
    entry = bibtex_entry(data)

    bib = base / "references.bib"
    existing = bib.read_text(encoding="utf-8") if bib.exists() else ""
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    with bib.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{prefix}{entry}\n")

    title = str(data.get("title", "")).strip()
    summary = str(data.get("summary", data.get("abstract", ""))).strip().replace("\n", " ")[:120]
    row = f"| {key} | {title} | {data.get('type', '')} | {summary} |\n"
    with (base / "library" / "INDEX.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(row)

    source_copied = None
    if file:
        src = Path(file)
        if src.exists():
            dest = base / "library" / "sources" / src.name
            shutil.copy2(src, dest)
            source_copied = str(dest)
            _write_if_absent(
                base / "library" / "notes" / f"{key}.md",
                f"# {title or key}\n\nSource: {src.name}\nKey: {key}\n\nNotes:\n",
            )

    return {"area": slug, "key": key, "bibtex": entry, "source_copied": source_copied}


def workspace_status(path: str) -> dict[str, Any]:
    root = Path(path)
    areas: list[dict[str, Any]] = []
    area_dir = root / "areas"
    if area_dir.exists():
        for entry in sorted(area_dir.iterdir()):
            if not entry.is_dir():
                continue
            bib = entry / "references.bib"
            refs = len(re.findall(r"(?m)^@", bib.read_text(encoding="utf-8"))) if bib.exists() else 0
            sources = entry / "library" / "sources"
            source_count = len([p for p in sources.iterdir() if p.is_file()]) if sources.exists() else 0
            areas.append(
                {
                    "area": entry.name,
                    "references": refs,
                    "sources": source_count,
                    "has_knowledge": (entry / "knowledge.md").exists(),
                }
            )
    return {"workspace": str(root), "exists": root.exists(), "area_count": len(areas), "areas": areas}
