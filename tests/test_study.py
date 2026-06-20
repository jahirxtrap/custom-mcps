from __future__ import annotations

import asyncio
import json

from fastmcp import Client
from study_mcp.server import mcp


def test_study_registers_tools():
    async def run():
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == [
        "area_add",
        "burstiness",
        "cite",
        "concept_map",
        "reference_add",
        "study_guide",
        "toolkit",
        "workspace_init",
        "workspace_status",
        "writing_check",
    ]


def test_writing_check_tool():
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool("writing_check", {"text": "We delve into the topic."})
            return json.loads(result.content[0].text)

    report = asyncio.run(run())
    assert report["score"] < 100


def test_concept_map_tool_returns_image(tmp_path):
    async def run():
        async with Client(mcp) as client:
            spec = json.dumps({"central": "Topic", "branches": [{"label": "A", "items": ["x"]}]})
            result = await client.call_tool("concept_map", {"spec": spec, "out_dir": str(tmp_path)})
            return result.content

    content = asyncio.run(run())
    kinds = {getattr(part, "type", None) for part in content}
    assert "image" in kinds
