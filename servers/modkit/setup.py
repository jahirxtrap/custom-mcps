"""Optional, standalone setup for the modkit server: register the minecraft-dev MCP.

minecraft-dev (@mcdxai/minecraft-dev-mcp) is the tool modkit's decompile_guide points to: reading
the MC/loader API and decompiling mods. If it is already registered it is left alone. Run:
    uv run python servers/modkit/setup.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys

CLAUDE = shutil.which("claude") or "claude"
PACKAGE = "@mcdxai/minecraft-dev-mcp"


def _registered(name: str) -> bool:
    done = subprocess.run([CLAUDE, "mcp", "list"], capture_output=True, text=True)
    return name in done.stdout


def main() -> int:
    if _registered("minecraft-dev"):
        print("minecraft-dev: already registered")
        return 0
    if not shutil.which("npx"):
        print(f"npx not found (install Node.js), then: claude mcp add minecraft-dev -s user -- npx -y {PACKAGE}")
        return 1
    ok = subprocess.run(
        [CLAUDE, "mcp", "add", "minecraft-dev", "-s", "user", "--", "npx", "-y", PACKAGE]
    ).returncode == 0
    print(f"minecraft-dev: {'registered' if ok else 'FAILED (need claude + npx)'}")
    print("note: it builds the native better-sqlite3 module (needs Node + C++ build tools); if it")
    print("fails at runtime, recompile better-sqlite3 for your Node version.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
