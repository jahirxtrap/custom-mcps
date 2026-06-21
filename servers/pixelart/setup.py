"""Optional, standalone setup for the pixelart server: install the pixel-art-sprites skill.

The server is self-contained; this only adds the complementary skill (reference-driven design,
sprite animation, Aseprite workflows). If the skill is already present it is left alone. Run:
    uv run python servers/pixelart/setup.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/omer-metin/skills-for-antigravity"
SKILL_DIR = Path.home() / ".claude" / "skills" / "pixel-art-sprites"


def main() -> int:
    if SKILL_DIR.exists():
        print("pixel-art-sprites: already installed")
        return 0
    npx = shutil.which("npx")
    if not npx:
        print(f"npx not found (install Node.js), then: npx skills add {REPO} --skill pixel-art-sprites")
        return 1
    print("installing pixel-art-sprites skill...")
    ok = subprocess.run([npx, "skills", "add", REPO, "--skill", "pixel-art-sprites"]).returncode == 0
    print(f"pixel-art-sprites: {'installed' if ok else 'install manually (see README)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
