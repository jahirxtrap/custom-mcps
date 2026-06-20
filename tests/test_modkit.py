from __future__ import annotations

import asyncio
import json

from fastmcp import Client
from modkit_mcp.server import mcp


def test_modkit_registers_all_tools():
    async def run():
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == [
        "check_access",
        "check_json",
        "check_structure",
        "find_symbol",
        "list_mods",
        "loader_sync",
        "mod_info",
    ]


def test_list_mods_tool_returns_json(tmp_path):
    vd = tmp_path / "Demo" / "demo-26.2-multi"
    (vd / "fabric" / "src" / "main" / "java").mkdir(parents=True)
    (vd / "settings.gradle").write_text("include 'fabric'\n", encoding="utf-8")
    (vd / "gradle.properties").write_text("mod_id=demo\n", encoding="utf-8")

    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool("list_mods", {"root": str(tmp_path)})
            return result.content[0].text

    data = json.loads(asyncio.run(run()))
    assert data[0]["mod"] == "Demo"
    assert data[0]["latest"]["version"] == "26.2"
