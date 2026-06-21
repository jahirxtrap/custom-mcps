"""Optional, standalone setup for the sfx server: install ffmpeg.

ffmpeg is optional (the server falls back to soundfile); installing it widens format and codec
coverage. If ffmpeg is already on PATH it is left alone. Run:
    uv run python servers/sfx/setup.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys

PACKAGES = {"win": ("winget", "Gyan.FFmpeg"), "mac": ("brew", "ffmpeg"), "linux": ("apt", "ffmpeg")}


def _platform() -> str:
    return "win" if sys.platform.startswith("win") else "mac" if sys.platform == "darwin" else "linux"


def _install(manager: str, package: str) -> bool:
    if not shutil.which(manager):
        print(f"  {manager} not found; install ffmpeg manually")
        return False
    if manager == "winget":
        command = [
            "winget", "install", "--id", package, "-e", "--source", "winget",
            "--accept-package-agreements", "--accept-source-agreements",
        ]
    elif manager == "brew":
        command = ["brew", "install", package]
    else:
        command = ["sudo", "apt", "install", "-y", package]
    return subprocess.run(command).returncode == 0


def main() -> int:
    if shutil.which("ffmpeg"):
        print("ffmpeg: already installed")
        return 0
    manager, package = PACKAGES[_platform()]
    print(f"ffmpeg not found; installing with {manager}...")
    ok = _install(manager, package)
    print(f"ffmpeg: {'installed' if ok else 'install manually (winget/brew/apt)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
