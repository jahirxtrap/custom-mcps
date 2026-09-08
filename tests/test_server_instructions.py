from __future__ import annotations

import asyncio

import pytest
from buildkit_mcp.server import mcp as buildkit
from devkit_mcp.server import mcp as devkit
from fastmcp import Client
from i18n_mcp.server import mcp as i18n
from modkit_mcp.server import mcp as modkit
from pixelart_mcp.server import mcp as pixelart
from sfx_mcp.server import mcp as sfx
from study_mcp.server import mcp as study

SERVERS = [buildkit, devkit, i18n, modkit, pixelart, sfx, study]


def _tool_names(server) -> set[str]:
    async def run():
        async with Client(server) as client:
            return {tool.name for tool in await client.list_tools()}

    return asyncio.run(run())


@pytest.mark.parametrize("server", SERVERS, ids=lambda s: s.name)
def test_every_server_declares_instructions(server):
    text = server.instructions
    assert text and text.strip()
    assert "Tools:" in text
    assert len(text.splitlines()) >= 3


@pytest.mark.parametrize("server", SERVERS, ids=lambda s: s.name)
def test_instructions_name_every_registered_tool(server):
    listed = server.instructions.split("Tools:", 1)[1]
    missing = {name for name in _tool_names(server) if name not in listed}
    assert not missing
