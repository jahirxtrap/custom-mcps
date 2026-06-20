"""Install the study ecosystem and store optional API keys in a gitignored .env.

Idempotent and best-effort: it checks what is already on PATH, installs what it can
(npm globals, winget/brew/apt where available), prints manual steps otherwise, and
registers the external MCPs at user scope. Run: uv run python scripts/setup.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
CLAUDE = shutil.which("claude") or "claude"
PLATFORM = "win" if sys.platform.startswith("win") else "mac" if sys.platform == "darwin" else "linux"
INTERACTIVE = sys.stdin.isatty()

CLI_TOOLS = [
    {"bin": "pandoc", "win": "JohnMacFarlane.Pandoc", "mac": "pandoc", "linux": "pandoc"},
    {"bin": "ffmpeg", "win": "Gyan.FFmpeg", "mac": "ffmpeg", "linux": "ffmpeg"},
    {"bin": "dot", "win": "Graphviz.Graphviz", "mac": "graphviz", "linux": "graphviz"},
]

NPM_TOOLS = [
    {"bin": "mmdc", "pkg": "@mermaid-js/mermaid-cli"},
    {"bin": "markmap", "pkg": "markmap-cli"},
]

OPTIONAL_KEYS = [
    ("OPENALEX_API_KEY", "OpenAlex contact email for the polite pool (free; blank to skip)"),
    ("SEMANTIC_SCHOLAR_API_KEY", "Semantic Scholar API key to raise limits (blank to skip)"),
]


def run(command: list[str]) -> bool:
    done = subprocess.run(command, capture_output=True, text=True)
    return done.returncode == 0


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def write_env(values: dict[str, str]) -> None:
    lines = [f"{key}={value}" for key, value in values.items() if value]
    ENV_PATH.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8", newline="\n")


def confirm(prompt: str) -> bool:
    if not INTERACTIVE:
        return False
    return input(f"{prompt} [Y/n] ").strip().lower() in ("", "y", "yes")


def install_cli() -> None:
    print("\n== CLI tools ==")
    for tool in CLI_TOOLS:
        if shutil.which(tool["bin"]):
            print(f"{tool['bin']}: already installed")
            continue
        installed = False
        if PLATFORM == "win" and shutil.which("winget") and confirm(f"install {tool['bin']} with winget?"):
            installed = run([
                "winget", "install", "--id", tool["win"], "-e", "--source", "winget",
                "--accept-package-agreements", "--accept-source-agreements",
            ])
        elif PLATFORM == "mac" and shutil.which("brew") and confirm(f"install {tool['bin']} with brew?"):
            installed = run(["brew", "install", tool["mac"]])
        elif PLATFORM == "linux" and shutil.which("apt") and confirm(f"install {tool['bin']} with apt?"):
            installed = run(["sudo", "apt", "install", "-y", tool["linux"]])
        print(f"{tool['bin']}: {'installed' if installed else 'install manually (see toolkit)'}")


def install_npm() -> None:
    print("\n== npm tools ==")
    if not shutil.which("npm"):
        print("npm not found; install Node.js to get mmdc and markmap")
        return
    for tool in NPM_TOOLS:
        if shutil.which(tool["bin"]):
            print(f"{tool['bin']}: already installed")
            continue
        if confirm(f"install {tool['pkg']} globally with npm?"):
            ok = run(["npm", "install", "-g", tool["pkg"]])
            print(f"{tool['bin']}: {'installed' if ok else 'FAILED'}")
        else:
            print(f"{tool['bin']}: skipped")


def collect_keys() -> dict[str, str]:
    print("\n== API keys (optional) -> .env ==")
    values = read_env()
    if not INTERACTIVE:
        print("non-interactive; keeping existing .env values")
        return values
    for key, description in OPTIONAL_KEYS:
        current = values.get(key, "")
        shown = f" [current: {current}]" if current else ""
        entered = input(f"{description}{shown}: ").strip()
        if entered:
            values[key] = entered
    write_env(values)
    print(f"saved {ENV_PATH}")
    return values


def register_mcps(env: dict[str, str]) -> None:
    print("\n== external MCP servers ==")
    openalex = [CLAUDE, "mcp", "add", "openalex", "-s", "user"]
    if env.get("OPENALEX_API_KEY"):
        openalex += ["-e", f"OPENALEX_API_KEY={env['OPENALEX_API_KEY']}"]
    openalex += ["--", "npx", "-y", "@cyanheads/openalex-mcp-server"]
    run([CLAUDE, "mcp", "remove", "openalex", "-s", "user"])
    print(f"openalex: {'registered' if run(openalex) else 'FAILED (need claude + npx)'}")
    print("semantic-scholar: pick an MCP from the registry/npm and register it with "
          "-e SEMANTIC_SCHOLAR_API_KEY (from .env) if you set a key")


def main() -> int:
    print("Study ecosystem setup")
    print(f"platform={PLATFORM} interactive={INTERACTIVE} env={ENV_PATH}")
    install_cli()
    install_npm()
    env = collect_keys()
    register_mcps(env)
    print("\nDone. Register the workspace MCP servers with: uv run python scripts/register.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
