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
    in_text_citation,
    reference_add as _reference_add,
    render_concept_map,
    study_guide as _study_guide,
    toolkit as _toolkit,
    workspace_init as _workspace_init,
    workspace_status as _workspace_status,
    writing_check as _writing_check,
)

mcp = FastMCP(name="study")


def _scratch(prefix: str, out_dir: str = "") -> Path:
    base = Path(out_dir) if out_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{prefix}_{uuid.uuid4().hex[:8]}.png"


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
    """Return embedded, area-agnostic study guidance, all of it or one topic:
    writing (human voice / anti-AI) / citations (APA 7) / structure (academic) / visual (organizers)."""
    return _study_guide(topic)


@mcp.tool
def toolkit(topic: str = "") -> str:
    """List the ecosystem to install for full academic work (documents, research, citations,
    diagrams, latex, images, video, humanize): install commands, which need an API key, how to get
    it and how to configure it. Pass a group name to filter. Run scripts/setup.py to automate it."""
    return _toolkit(topic)


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
    Also writes a CLAUDE.md that tells Claude how to work in the workspace. Idempotent."""
    names = [name.strip() for name in areas.split(",") if name.strip()] if areas else []
    return json.dumps(_workspace_init(path, names))


@mcp.tool
def area_add(path: str, name: str) -> str:
    """Add a study area to an existing workspace: a folder with its knowledge base, BibTeX
    bibliography, and reference library (INDEX.md, sources/, notes/)."""
    return json.dumps(_area_add(path, name))


@mcp.tool
def reference_add(path: str, area: str, fields: str, file: str = "") -> str:
    """Register a reference in an area's library: append a BibTeX entry and an index row, and
    optionally copy the original file into the library. 'fields' is JSON (type/authors/year/title/...);
    'file' is an optional path to the source document."""
    data = json.loads(fields)
    return json.dumps(_reference_add(path, area, data, file))


@mcp.tool
def workspace_status(path: str) -> str:
    """Summarize a study workspace: each area with its reference count, stored sources, and whether
    a knowledge base exists."""
    return json.dumps(_workspace_status(path))


def main() -> None:
    mcp.run()
