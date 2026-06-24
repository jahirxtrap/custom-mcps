"""buildkit MCP server: design low-poly 3D structures by data (guide, references, preview, check)."""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from formkit import (
    check as _check,
    compile_spec,
    design_guide as _design_guide,
    godot_def as _godot_def,
    reference_brief,
    render,
)

mcp = FastMCP(name="buildkit")


def _scratch(prefix: str, out_dir: str = "") -> Path:
    base = Path(out_dir) if out_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{prefix}_{uuid.uuid4().hex[:8]}.png"


@mcp.tool
def design_guide(topic: str = "") -> str:
    """Embedded low-poly 3D design principles, all of them or one topic: method (blockout first) /
    silhouette / proportion / composition / color / light / consistency / subjects. Grounded in
    established game-art practice."""
    return _design_guide(topic)


@mcp.tool
def search_reference(subject: str, kind: str = "") -> str:
    """Build a reference brief before modeling: targeted web-search queries for `subject` (photos,
    low-poly refs, and for buildings plans/elevations), what to extract (masses, proportions, opening
    positions, palette) and how to translate it to the spec. kind = building/house/tree/prop. It does
    NOT fetch images: run the queries with your own web search."""
    return json.dumps(reference_brief(subject, kind))


@mcp.tool(output_schema=None)
def render_preview(spec: str, view: str = "iso", out_dir: str = "") -> list[Any]:
    """Render a blockout preview of a 3D spec and return the image plus a 'path=' line. spec is JSON:
    {type:building|house|tree|group, ...}. building = {footprint:[w,d], storeys, storey_height, roof,
    openings:{door,windows}, palette}. view='iso' (flat-shaded) or 'silhouette' (the readability test).
    It's a massing/proportion preview, not a final render (Godot does that)."""
    data = json.loads(spec)
    image = render(compile_spec(data), view=view)
    target = Path(data["out"]) if data.get("out") else _scratch(f"buildkit_{view}", out_dir)
    image.save(target)
    return [Image(path=str(target)), f"path={target} mime=image/png size={image.width}x{image.height} view={view}"]


@mcp.tool
def check(spec: str) -> str:
    """Validate a 3D spec against low-poly blockout rules: proportion and scale (storey, door fit,
    footprint ratio) and palette size, plus the silhouette-test reminder. spec is JSON."""
    return json.dumps(_check(json.loads(spec)))


@mcp.tool
def godot_def(spec: str) -> str:
    """Emit a Godot-ready def from the spec: for a building, a `house_builder`-style def (size/height/
    roof_height/wall_color/roof_color/door) ready for HouseBuilder.build; otherwise a generic
    primitives def plus a GDScript FormBuilder that builds it. spec is JSON."""
    return json.dumps(_godot_def(json.loads(spec)))


def main() -> None:
    mcp.run()
