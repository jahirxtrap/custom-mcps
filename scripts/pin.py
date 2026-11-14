"""Write each server's constraints.txt: the third-party versions the workspace lock pins for it."""
from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSTRAINTS = "constraints.txt"
EXPORT = ["uv", "export", "--frozen", "--no-hashes", "--no-dev", "--no-emit-workspace", "--no-header", "--no-annotate"]


def servers() -> list[Path]:
    return sorted(pyproject.parent for pyproject in ROOT.glob("servers/*/pyproject.toml"))


def pinned(server: Path) -> str:
    package = tomllib.loads((server / "pyproject.toml").read_text(encoding="utf-8"))["project"]["name"]
    return subprocess.run(
        [*EXPORT, "--package", package],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        stdin=subprocess.DEVNULL,
    ).stdout


def main() -> None:
    for server in servers():
        (server / CONSTRAINTS).write_text(pinned(server), encoding="utf-8", newline="\n")
        print(f"{server.name}: pinned")


if __name__ == "__main__":
    main()
