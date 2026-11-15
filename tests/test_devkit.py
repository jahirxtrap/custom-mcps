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
        "find_comments",
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


def test_post_tool_use_hook_warns_only_about_new_comments(tmp_path):
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    handler = hooks["PostToolUse"][0]
    assert handler["matcher"] == "Edit|Write|MultiEdit"
    assert handler["hooks"][0]["args"][-1] == "${CLAUDE_PLUGIN_ROOT}/hooks/comments.py"
    target = tmp_path / "app.py"
    target.write_text("# legacy note\nLIMIT = 10  # bytes\n", encoding="utf-8")

    def run(tool_input):
        event = {"tool_name": "Edit", "tool_input": {"file_path": str(target), **tool_input}}
        return subprocess.run(
            [sys.executable, "-I", str(PLUGIN / "hooks" / "comments.py")],
            input=json.dumps(event), capture_output=True, text=True, encoding="utf-8",
        )

    noisy = run({"old_string": "LIMIT = 10", "new_string": "LIMIT = 10  # bytes"})
    assert noisy.returncode == 0
    reason = json.loads(noisy.stdout)["reason"]
    assert "line 2" in reason and "# bytes" in reason and "legacy" not in reason
    quiet = run({"old_string": "# legacy note", "new_string": "LIMIT = 10"})
    assert quiet.returncode == 0 and quiet.stdout == ""

    first = "# " + "the queue drains one plugin at a time " * 4
    long_block = f"{first}\n# " + "so every client draws the same state " * 3
    target.write_text(f"LIMIT = 10\n{long_block}\nSTEP = 1\n", encoding="utf-8")
    block = run({"old_string": "STEP = 1", "new_string": f"{long_block}\nSTEP = 1"})
    reason = json.loads(block.stdout)["reason"]
    excerpt = reason.splitlines()[1]
    assert excerpt.startswith("- lines 2-3, comment: # the queue drains") and "…" in excerpt
    assert excerpt.endswith("draws the same state") and len(excerpt) < 110
