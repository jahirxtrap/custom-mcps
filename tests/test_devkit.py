from __future__ import annotations

import asyncio

from devkit_mcp.server import mcp
from fastmcp import Client


def test_devkit_registers_tools():
    async def run():
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == [
        "commit_context",
        "commit_style",
        "conventions",
        "find_duplication",
        "find_format",
        "find_hardcoded",
        "find_inconsistent",
    ]


def test_conventions_tool():
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool("conventions", {"topic": "commit"})
            return result.content[0].text

    out = asyncio.run(run())
    assert "Co-Authored-By" in out
