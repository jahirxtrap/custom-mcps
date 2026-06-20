"""Register every server in this workspace with Claude Code at user scope."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = shutil.which("claude") or "claude"


def entry_points() -> list[str]:
    names: list[str] = []
    for pyproject in sorted(ROOT.glob("servers/*/pyproject.toml")):
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        names.extend(data.get("project", {}).get("scripts", {}))
    return names


def register(entry: str) -> bool:
    name = entry.removesuffix("-mcp")
    subprocess.run([CLAUDE, "mcp", "remove", name, "-s", "user"], capture_output=True, text=True)
    done = subprocess.run(
        [CLAUDE, "mcp", "add", name, "-s", "user", "--", "uv", "run", "--project", str(ROOT), entry],
        capture_output=True,
        text=True,
    )
    ok = done.returncode == 0
    print(f"{name}: {'registered' if ok else 'FAILED — ' + (done.stderr or done.stdout).strip()}")
    return ok


def main() -> int:
    entries = entry_points()
    if not entries:
        print("no servers found under servers/*")
        return 1
    results = [register(entry) for entry in entries]
    print(f"\n{sum(results)}/{len(results)} server(s) registered at user scope.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
