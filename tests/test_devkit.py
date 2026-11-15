from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from devkit_mcp.server import mcp
from fastmcp import Client

PLUGIN = Path(__file__).resolve().parents[1] / "servers" / "devkit"


def test_devkit_registers_tools():
    async def run():
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == [
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


def test_session_start_hook_prints_the_core_digest():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    handler = hooks["SessionStart"][0]["hooks"][0]
    assert handler["command"] == "uv"
    assert handler["args"][-1] == "${CLAUDE_PLUGIN_ROOT}/hooks/digest.py"

    done = subprocess.run(
        [sys.executable, "-I", str(PLUGIN / "hooks" / "digest.py")],
        capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
    )
    assert done.returncode == 0
    for section in ("## code", "## commit", "## ssot", "## dry"):
        assert section in done.stdout
    assert "## naming" not in done.stdout and "conventions(topic)" in done.stdout
    assert len(done.stdout) < 10000
