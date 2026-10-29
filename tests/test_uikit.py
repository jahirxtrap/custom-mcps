from __future__ import annotations

import asyncio
import json

from fastmcp import Client
from uikit_mcp.server import mcp


def _call(name, args):
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(name, args)
            return result.content[0].text

    return asyncio.run(run())


def test_uikit_registers_tools():
    async def run():
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == [
        "check_contrast",
        "contrast",
        "design_guide",
        "find_pairs",
        "read_tokens",
    ]


def test_contrast_tool():
    report = json.loads(_call("contrast", {"front": "#000000", "back": "#ffffff"}))
    assert report["ratio"] == 21.0
    assert report["aa_text"] is True


def test_design_guide_tool():
    assert "Nielsen" in _call("design_guide", {"topic": "heuristics"})


def test_check_contrast_tool(tmp_path):
    theme = tmp_path / "dark.json"
    theme.write_text(
        json.dumps({"kind": "dark", "colors": {
            "background": "#0a0a0a", "surface": "#15181e",
            "on-surface": "#2a2f38", "text": "#f4f6f8"}}),
        encoding="utf-8",
    )
    report = json.loads(_call("check_contrast", {"path": str(theme)}))
    assert report["all_pass"] is False
    assert report["report"]["dark"]["failing"] == 1


def test_read_tokens_tool(tmp_path):
    theme = tmp_path / "light.json"
    theme.write_text(
        json.dumps({"kind": "light", "colors": {"surface": "#ffffff", "text": "#111111"}}),
        encoding="utf-8",
    )
    report = json.loads(_call("read_tokens", {"path": str(theme)}))
    assert "light" in report["themes"]
