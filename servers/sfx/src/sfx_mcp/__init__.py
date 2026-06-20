"""sfx: a standalone, engine-agnostic MCP server for synthesizing sound effects."""
from __future__ import annotations

from .server import main, mcp

__all__ = ["mcp", "main"]
