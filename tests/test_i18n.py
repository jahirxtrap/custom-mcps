from __future__ import annotations

import asyncio
import json

from fastmcp import Client
from i18n_mcp.server import mcp


def test_i18n_registers_tools():
    async def run():
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == [
        "check_format",
        "completeness",
        "find_unused",
        "i18n_guide",
        "locale_diff",
    ]


def test_locale_diff_tool(tmp_path):
    d = tmp_path / "locales"
    d.mkdir()
    (d / "en.json").write_text('{"A": "a", "B": "b"}', encoding="utf-8")
    (d / "es.json").write_text('{"A": "x"}', encoding="utf-8")

    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool("locale_diff", {"path": str(d)})
            return result.content[0].text

    report = json.loads(asyncio.run(run()))
    assert report["base"] == "en"
    assert "B" in report["diff"]["es"]["missing"]
