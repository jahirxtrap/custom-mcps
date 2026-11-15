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
    final_check as _final_check,
    format_citation,
    grammar_check as _grammar_check,
    image_search as _image_search,
    in_text_citation,
    inspect_template as _inspect_template,
    reference_add as _reference_add,
    render_concept_map,
    render_document as _render_document,
    study_guide as _study_guide,
    toolkit as _toolkit,
    workspace_init as _workspace_init,
    workspace_status as _workspace_status,
    writing_check as _writing_check,
)

mcp = FastMCP(
    name="study",
    instructions=(
        "Academic and study work by data, for any field and any language. It carries no subject "
        "knowledge.\n"
        "Tools: writing_check, burstiness, grammar_check, final_check, study_guide, concept_map, "
        "render_document, template_inspect, cite, image_search, toolkit, workspace_init, area_add, "
        "reference_add, workspace_status.\n"
        "Work inside a workspace: workspace_init scaffolds one (conventions, styles, templates, "
        "tools, memory and per-area knowledge and bibliography) and writes its own CLAUDE.md; "
        "area_add adds a subject to it. render_document builds PDFs (report, slides) and editable "
        "Word and PowerPoint (docx, pptx) on the institution's own template, which template_inspect "
        "describes first. The external dependencies live outside this server -- toolkit is the "
        "catalog of what to install (pandoc, LaTeX, Marp, diagram CLIs, LanguageTool) and which "
        "ones need a key. Read study_guide before writing or building anything, and "
        "study_guide('assignment') before reading a brief that arrives as a photo. final_check runs "
        "the three text checks once over the finished text before delivering, never paragraph by "
        "paragraph."
    ),
)


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
def grammar_check(text: str, language: str) -> str:
    """Spelling and grammar through a local LanguageTool, in any of its 30+ languages ('es', 'en-US',
    'de-DE', 'pt-BR'; 'auto' detects). Run it once over the finished text, never per paragraph. Markdown
    and pandoc markup (headings, emphasis, links, images, citation keys, code, tables) is removed before
    checking and every finding points back to the original line: line, column, flagged text, message,
    replacements, rule, category, plus counts by category. It judges nothing, so spelling hits on
    names, technical terms and citations are the author's call. Needs LanguageTool: the plugin options
    languagetool_url (a running server) or languagetool_home (its unzipped folder, Java 17+ on PATH),
    or the same values in LANGUAGETOOL_URL / LANGUAGETOOL_HOME; otherwise it answers available=false
    (see toolkit('grammar'))."""
    return json.dumps(_grammar_check(text, language))


@mcp.tool
def final_check(text: str, language: str) -> str:
    """Run writing_check, burstiness and grammar_check together, once over the finished text, and
    return one report: a summary line plus the three results. 'language' is LanguageTool's code
    ('es', 'en-US', 'pt-BR'...). Use it instead of three separate calls before delivering; names
    and technical terms flagged as spelling are the author's call."""
    return json.dumps(_final_check(text, language))


@mcp.tool
def study_guide(topic: str = "") -> str:
    """Return embedded, area-agnostic study guidance, all of it or one topic: writing (human voice /
    anti-AI) / citations (APA 7) / structure (academic) / visual (organizers) / images (search free
    sources first, AI only on request) / slides (pptx on a template, Marp, ReportLab) / documents
    (docx on a template, pandoc, LaTeX, ReportLab) / assignment (reading a brief that arrives as a
    photo, confirming it, recording it)."""
    return _study_guide(topic)


@mcp.tool
def template_inspect(path: str) -> str:
    """Read a .docx or .pptx an institution hands out and report what a render_document spec can use.
    Word: sections and margins, paragraph and table styles, and the texts of body, headers, footers
    and text boxes (the cover texts go in 'replace', sample paragraphs in 'remove'). PowerPoint: slide
    size, every layout with its name and placeholders, and the sample slides. It changes nothing."""
    return json.dumps(_inspect_template(path))


@mcp.tool
def toolkit(topic: str = "") -> str:
    """List the ecosystem to install for full academic work (documents, slides, research, citations,
    diagrams, latex, images, video, humanize, grammar): install commands, which need an API key, how
    to get it and how to configure it. Pass a group name to filter. Run servers/study/setup.py to
    automate it."""
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
    """Build a document or deck from a JSON spec. ASK the user what the institution expects before
    building (see study_guide('documents') and study_guide('slides')). format='docx' writes editable
    Word on the institution's template: {template?, replace:{text:text}, remove:[texts], font?,
    margins_cm?, toc?, blocks:[{type:heading|text|quote|list|table|image|references|pagebreak}]};
    the template keeps its cover, logos, headers and styles and the content follows them. format=
    'pptx' writes editable PowerPoint on a template's layouts: {template?, keep_slides?, replace?,
    slides:[{layout:<name from template_inspect>|cover|bullets|two|image|table|closing, title,
    subtitle?, items?, text?, image?, table?, notes?}]}. format='report' and 'slides' are the
    ReportLab PDFs: report {abstract?, toc?, watermark?, palette?, font:'serif'|'sans', blocks:[...
    chart|columns]} with navigable outline and 'page / total'; slides {slides:[{layout:cover|bullets|
    table|chart|closing}]} at 16:9 with progress bar and 'reveal' builds. Run template_inspect on a
    template first."""
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
