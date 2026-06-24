from __future__ import annotations

import asyncio
import json

from buildkit_mcp.server import mcp
from fastmcp import Client


def test_buildkit_registers_tools():
    async def run():
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == [
        "check",
        "design_guide",
        "godot_def",
        "render_preview",
        "search_reference",
    ]


def test_godot_def_tool():
    async def run():
        async with Client(mcp) as client:
            spec = json.dumps({"type": "building", "footprint": [6, 5], "door": "north"})
            result = await client.call_tool("godot_def", {"spec": spec})
            return json.loads(result.content[0].text)

    out = asyncio.run(run())
    assert out["format"] == "house_builder"
    assert out["def"]["door"] == "north"


def test_render_preview_returns_image(tmp_path):
    async def run():
        async with Client(mcp) as client:
            spec = json.dumps({"type": "building", "footprint": [6, 5]})
            result = await client.call_tool("render_preview", {"spec": spec, "out_dir": str(tmp_path)})
            return result.content

    kinds = {getattr(part, "type", None) for part in asyncio.run(run())}
    assert "image" in kinds
