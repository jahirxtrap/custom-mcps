"""pixelart: a standalone, engine-agnostic MCP server for drawing and verifying pixel art."""
from __future__ import annotations

from .server import main, mcp

__all__ = ["mcp", "main"]
