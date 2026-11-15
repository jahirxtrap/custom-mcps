"""Create and manage a multi-area study workspace on disk."""
from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from .assets import (
    APA_CSL_README,
    BIB_HEADER,
    CITATION_APA,
    CONCEPT_MAP_EXAMPLE,
    INDEX_TEMPLATE,
    KNOWLEDGE_TEMPLATE,
    MEMORY_LOG,
    MEMORY_PROFILE,
    PAPER_APA7_TEX,
    TOOLS_README,
    VISUAL_GUIDE,
    WORKS_README,
    WORKSPACE_CLAUDE,
    WRITING_RULES,
)
from .cite import bibtex_entry, bibtex_key
from .normalize import normalize_extracted

_PLAINTEXT = ("md", "markdown", "txt")
_PANDOC = ("docx", "odt", "rtf", "html", "htm", "epub", "tex")
_WORK_FOLDERS = ("documents", "slides")
_OUT = "out"
_LIBRARY = "library"
_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)
_DOCSTRING = re.compile(r'^\s*(?:r|u)?(?:"""|\'\'\')\s*([^\n"\']+)', re.MULTILINE)


def _slug(name: str) -> str:
    norm = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    norm = re.sub(r"[^a-z0-9]+", "-", norm.strip().lower()).strip("-")
    return norm or "area"


def _write_if_absent(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def _run(command: list[str]) -> bool:
    try:
        return subprocess.run(command, capture_output=True, text=True, stdin=subprocess.DEVNULL).returncode == 0
    except OSError:
        return False


def _to_markdown(src: Path, key: str, md_dir: Path) -> str | None:
    md_dir.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower().lstrip(".")
    out = md_dir / f"{key}.md"
    if ext in _PLAINTEXT:
        out.write_text(src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8", newline="\n")
        return str(out)
    if ext == "pdf" and shutil.which("pdftotext") and _run(["pdftotext", str(src), str(out)]):
        extracted = out.read_text(encoding="utf-8", errors="replace")
        out.write_text(normalize_extracted(extracted), encoding="utf-8", newline="\n")
        return str(out)
    if ext in _PANDOC and shutil.which("pandoc"):
        media = md_dir / f"media-{key}"
        if _run(["pandoc", str(src), "-t", "gfm", "--wrap=none", f"--extract-media={media}", "-o", str(out)]):
            return str(out)
    return None


def _create_area(root: Path, name: str) -> str:
    slug = _slug(name)
    base = root / "areas" / slug
    (base / "library" / "sources").mkdir(parents=True, exist_ok=True)
    (base / "library" / "md").mkdir(parents=True, exist_ok=True)
    _write_if_absent(base / "knowledge.md", KNOWLEDGE_TEMPLATE.format(area=name))
    _write_if_absent(base / "references.bib", BIB_HEADER.format(area=name))
    _write_if_absent(base / "library" / "INDEX.md", INDEX_TEMPLATE.format(area=name))
    return slug


def workspace_init(path: str, areas: list[str] | None = None) -> dict[str, Any]:
    root = Path(path)
    for name in ("conventions", "styles", "memory/works", "areas", "templates", "tools"):
        (root / name).mkdir(parents=True, exist_ok=True)
    files = {
        root / "CLAUDE.md": WORKSPACE_CLAUDE,
        root / "conventions" / "writing-rules.md": f"{WRITING_RULES}\n\n{VISUAL_GUIDE}",
        root / "conventions" / "citation-apa.md": CITATION_APA,
        root / "styles" / "README.md": APA_CSL_README,
        root / "memory" / "profile.md": MEMORY_PROFILE,
        root / "memory" / "log.md": MEMORY_LOG,
        root / "memory" / "works" / "README.md": WORKS_README,
        root / "templates" / "paper-apa7.tex": PAPER_APA7_TEX,
        root / "templates" / "concept-map-example.json": CONCEPT_MAP_EXAMPLE,
        root / "tools" / "README.md": TOOLS_README,
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

    source_copied = None
    markdown = None
    if file:
        src = Path(file)
        if src.exists():
            dest = base / "library" / "sources" / src.name
            shutil.copy2(src, dest)
            source_copied = str(dest)
            markdown = _to_markdown(src, key, base / "library" / "md")

    title = str(data.get("title", "")).strip()
    summary = str(data.get("summary", data.get("abstract", ""))).strip().replace("\n", " ")[:120]
    md_cell = f"md/{key}.md" if markdown else ""
    row = f"| {key} | {title} | {data.get('type', '')} | {md_cell} | {summary} |\n"
    with (base / "library" / "INDEX.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(row)

    return {"area": slug, "key": key, "bibtex": entry, "source_copied": source_copied, "markdown": markdown}


def _frontmatter(path: Path) -> dict[str, str]:
    match = _FRONTMATTER.match(path.read_text(encoding="utf-8", errors="replace"))
    fields: dict[str, str] = {}
    if match:
        for line in match.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "-")):
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip()
    return fields


def _docstring_line(path: Path) -> str:
    match = _DOCSTRING.search(path.read_text(encoding="utf-8", errors="replace"))
    return match.group(1).strip() if match else ""


def _by_suffix(files: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for file in files:
        suffix = file.suffix.lower().lstrip(".") or "none"
        counts[suffix] = counts.get(suffix, 0) + 1
    return dict(sorted(counts.items()))


def _works(root: Path) -> dict[str, Any]:
    folder = root / "memory" / "works"
    files = [p for p in folder.glob("*.md") if p.name.lower() != "readme.md"] if folder.exists() else []
    by_status: dict[str, int] = {}
    for file in files:
        status = _frontmatter(file).get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
    return {"count": len(files), "by_status": dict(sorted(by_status.items()))}


def _tools(root: Path) -> list[dict[str, str]]:
    folder = root / "tools"
    if not folder.exists():
        return []
    return [{"module": p.stem, "does": _docstring_line(p)} for p in sorted(folder.glob("*.py")) if p.stem != "__init__"]


def _templates(root: Path) -> dict[str, list[str]]:
    folder = root / "templates"
    grouped: dict[str, list[str]] = {}
    if folder.exists():
        for file in sorted(folder.iterdir()):
            if file.is_file():
                grouped.setdefault(file.suffix.lower().lstrip(".") or "none", []).append(file.name)
    return grouped


def _area_status(entry: Path) -> dict[str, Any]:
    bib = entry / "references.bib"
    refs = len(re.findall(r"(?m)^@", bib.read_text(encoding="utf-8"))) if bib.exists() else 0
    sources = entry / _LIBRARY / "sources"
    source_count = len([p for p in sources.iterdir() if p.is_file()]) if sources.exists() else 0
    works = {
        name: sorted(p.name for p in (entry / name).iterdir() if p.is_dir())
        for name in _WORK_FOLDERS
        if (entry / name).exists()
    }
    scripts = [p for p in entry.rglob("*.py") if _LIBRARY not in p.relative_to(entry).parts]
    out = entry / _OUT
    deliverables = _by_suffix([p for p in out.iterdir() if p.is_file()]) if out.exists() else {}
    return {
        "area": entry.name,
        "references": refs,
        "sources": source_count,
        "has_knowledge": (entry / "knowledge.md").exists(),
        "works": works,
        "scripts": len(scripts),
        "deliverables": deliverables,
    }


def workspace_status(path: str) -> dict[str, Any]:
    root = Path(path)
    area_dir = root / "areas"
    areas = [_area_status(entry) for entry in sorted(area_dir.iterdir()) if entry.is_dir()] if area_dir.exists() else []
    return {
        "workspace": str(root),
        "exists": root.exists(),
        "area_count": len(areas),
        "areas": areas,
        "templates": _templates(root),
        "tools": _tools(root),
        "works": _works(root),
    }
