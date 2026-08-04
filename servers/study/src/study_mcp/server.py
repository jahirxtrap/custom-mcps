"""study MCP server: area- and language-agnostic academic-work toolkit."""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from studykit import (
    area_add as _area_add,
    bibtex_entry,
    burstiness as _burstiness,
    doi_to_bibtex,
    format_citation,
    image_search as _image_search,
    in_text_citation,
    reference_add as _reference_add,
    render_concept_map,
    render_document as _render_document,
    study_guide as _study_guide,
    toolkit as _toolkit,
    workspace_init as _workspace_init,
    workspace_status as _workspace_status,
    writing_check as _writing_check,
)

mcp = FastMCP(name="study")


def _scratch(prefix: str, out_dir: str = "", suffix: str = "png") -> Path:
    base = Path(out_dir) if out_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{prefix}_{uuid.uuid4().hex[:8]}.{suffix}"


@mcp.tool
def writing_check(text: str) -> str:
    """Detect AI 'tells' in academic text (English and Spanish): em dashes, AI filler, negative
    parallelism, the rule of three, tell-tale vocabulary, vague attributions, meta-commentary,
    chained transitions, and stacked hedging. Returns a 0-100 score and hits by category."""
    return json.dumps(_writing_check(text))


@mcp.tool
def burstiness(text: str) -> str:
    """Measure sentence-length variation, what AI detectors penalize when it is low. Returns mean,
    standard deviation, coefficient of variation, uniform percentage, and a 0-100 score. Language
    agnostic."""
    return json.dumps(_burstiness(text))


@mcp.tool
def study_guide(topic: str = "") -> str:
    """Return embedded, area-agnostic study guidance, all of it or one topic: writing (human voice /
    anti-AI) / citations (APA 7) / structure (academic) / visual (organizers) / images (search free
    sources first, AI only on request) / slides (Marp, ask PDF vs editable PPTX)."""
    return _study_guide(topic)


@mcp.tool
def toolkit(topic: str = "") -> str:
    """List the ecosystem to install for full academic work (documents, slides, research, citations,
    diagrams, latex, images, video, humanize): install commands, which need an API key, how to get
    it and how to configure it. Pass a group name to filter. Run servers/study/setup.py to automate it."""
    return _toolkit(topic)


@mcp.tool
def image_search(subject: str, kind: str = "") -> str:
    """Build a brief for sourcing a real image of `subject` from free, openly licensed providers
    (Wikimedia Commons, Openverse, Google reusable, Flickr Commons): ready search/API URLs, a
    licensing and attribution checklist, and the rule to generate with AI only when the user
    explicitly asks. kind = photo/diagram/illustration/map/portrait/logo. It does NOT fetch images:
    run the URLs with your own web search/fetch. For AI generation, see study_guide('images')."""
    return json.dumps(_image_search(subject, kind))


@mcp.tool(output_schema=None)
def concept_map(spec: str, out_dir: str = "") -> list[Any]:
    """Render a concept map / graphic organizer from a JSON spec and return the image plus a 'path='
    line. Spec: {central, branches:[{label, color?, items:[str | {label, text}]}], out?}. It follows
    the anti-AI visual rules (no meta labels, 2-4 colors). The PNG goes to spec.out or out_dir/temp."""
    data = json.loads(spec)
    image = render_concept_map(data)
    target = Path(data["out"]) if data.get("out") else _scratch("conceptmap", out_dir)
    image.save(target)
    return [Image(path=str(target)), f"path={target} mime=image/png size={image.width}x{image.height}"]


@mcp.tool
def render_document(spec: str, out_dir: str = "") -> str:
    """Typeset a professional PDF with ReportLab from a JSON spec. ASK the user which engine to use
    before building (see study_guide('documents') and study_guide('slides')): ReportLab is the
    technical, precisely typeset option; Marp is the visual, Markdown-fast one; pandoc/LaTeX own
    .docx and automatic APA bibliographies. Spec: {format:'report'|'slides', title, subtitle?,
    author?, date?, palette?, font:'serif'|'sans', out?, ...}. report adds {abstract?, toc?,
    watermark?, blocks:[{type:heading|text|quote|list|table|chart|references|columns|pagebreak}]}
    with a navigable outline and 'page / total'. slides adds {slides:[{layout:cover|bullets|table|
    chart|closing, ...}]} at 16:9, with progress bar and optional 'reveal' builds."""
    data = json.loads(spec)
    fmt = str(data.get("format", "report")).lower()
    target = Path(data["out"]) if data.get("out") else _scratch(fmt, out_dir, "pdf")
    return json.dumps(_render_document(data, target))


@mcp.tool
def cite(fields: str = "", doi: str = "") -> str:
    """Build a citation. With 'doi': resolve it to BibTeX (uses the network). With 'fields' (JSON:
    type/authors/year/title/journal/volume/issue/pages/publisher/doi/url): return the APA 7
    reference, the in-text citation, and a BibTeX entry. type = article/book/chapter/web."""
    if doi:
        try:
            return json.dumps({"doi": doi, "bibtex": doi_to_bibtex(doi)})
        except Exception as error:
            return json.dumps({"error": str(error)})
    if not fields:
        return json.dumps({"error": "provide 'fields' (JSON) or 'doi'"})
    data = json.loads(fields)
    return json.dumps(
        {"apa": format_citation(data), "in_text": in_text_citation(data), "bibtex": bibtex_entry(data)}
    )


@mcp.tool
def workspace_init(path: str, areas: str = "") -> str:
    """Scaffold a multi-area study workspace at 'path': conventions (anti-AI + APA), styles, memory,
    and areas/. 'areas' is a comma-separated list of subjects to seed (a student can be multi-area).
    Also writes a CLAUDE.md that tells Claude how to work in the workspace."""
    names = [name.strip() for name in areas.split(",") if name.strip()] if areas else []
    return json.dumps(_workspace_init(path, names))


@mcp.tool
def area_add(path: str, name: str) -> str:
    """Add a study area to an existing workspace: a folder with its knowledge base, BibTeX
    bibliography, and reference library (INDEX.md, sources/, notes/)."""
    return json.dumps(_area_add(path, name))


@mcp.tool
def reference_add(path: str, area: str, fields: str, file: str = "") -> str:
    """Register a reference in an area's library: append a BibTeX entry and an index row, copy the
    original into library/sources, and convert it to readable Markdown in library/md (txt/md by copy;
    pdf via pdftotext; docx/odt/rtf/html/epub/tex via pandoc, if on PATH). 'fields' is JSON
    (type/authors/year/title/...); 'file' is an optional path to the source document."""
    data = json.loads(fields)
    return json.dumps(_reference_add(path, area, data, file))


@mcp.tool
def workspace_status(path: str) -> str:
    """Summarize a study workspace: each area with its reference count, stored sources, and whether
    a knowledge base exists."""
    return json.dumps(_workspace_status(path))


def main() -> None:
    mcp.run()
