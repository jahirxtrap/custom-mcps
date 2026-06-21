"""Install the study ecosystem and store optional API keys in a gitignored .env.

Two modes, both idempotent and best-effort:

  uv run python scripts/setup.py
      Global: install CLIs (winget/brew/apt) and npm tools, write a repo .env, and
      register the external MCP servers at user scope.

  uv run python scripts/setup.py --workspace <dir> [--mermaid]
      Workspace-scoped: keep everything inside <dir> -- a local .env, a project
      .mcp.json, a TOOLKIT.md, a .gitignore, and npm tools installed under
      <dir>/node_modules. Nothing is installed globally and no user scope is touched.
      --mermaid also installs mermaid-cli locally (heavy: it pulls Chromium).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from studykit import toolkit

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = shutil.which("claude") or "claude"
NPM = shutil.which("npm")
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

SKILLS_README = """# Skills (project-scoped)

Skills placed here load automatically when this folder is open in Claude Code (project scope).
Plugin skills installed once at user scope are also available here, so most skills do not need
to be copied per project.

Recommended:
- Document skills: docx, pptx, xlsx, pdf (install the Anthropic document skills, user scope).
- humanizer: rewrite text to a human voice (install its plugin); verify with the study
  writing_check tool.
- deep-research: multi-source, cited research (Claude Code skill).

Use this folder for skills specific to this workspace (a `<name>/SKILL.md` per skill). To bundle
your own copies of existing skills into a portable workspace, run setup with
`--skills-from <your skills dir>`.
"""


def run(command: list[str], env: dict[str, str] | None = None) -> bool:
    done = subprocess.run(command, capture_output=True, text=True, env=env)
    if done.returncode != 0:
        tail = (done.stderr or done.stdout).strip().splitlines()[-1:] or [""]
        print(f"  ! {tail[0]}")
    return done.returncode == 0


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def write_env(path: Path, values: dict[str, str]) -> None:
    lines = [f"{key}={value}" for key, value in values.items() if value]
    path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8", newline="\n")


def _ask(prompt: str) -> str | None:
    try:
        return input(prompt).strip()
    except EOFError:
        return None


def confirm(prompt: str) -> bool:
    if not INTERACTIVE:
        return False
    answer = _ask(f"{prompt} [Y/n] ")
    return answer is not None and answer.lower() in ("", "y", "yes")


def collect_keys(env_path: Path) -> dict[str, str]:
    print(f"\n== API keys (optional) -> {env_path.name} ==")
    values = read_env(env_path)
    if not INTERACTIVE:
        print("non-interactive; keeping existing values")
        return values
    for key, description in OPTIONAL_KEYS:
        current = values.get(key, "")
        shown = f" [current: {current}]" if current else ""
        entered = _ask(f"{description}{shown}: ")
        if entered is None:
            print("no input stream; keeping existing values")
            break
        if entered:
            values[key] = entered
    write_env(env_path, values)
    print(f"saved {env_path}")
    return values


def report_clis() -> None:
    print("\n== system CLIs (installed globally; not confined to a directory) ==")
    for tool in [*[t["bin"] for t in CLI_TOOLS], "latexmk"]:
        print(f"  {tool}: {'found' if shutil.which(tool) else 'missing (see TOOLKIT.md)'}")


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


def install_npm_global() -> None:
    print("\n== npm tools (global) ==")
    if not NPM:
        print("npm not found; install Node.js to get mmdc and markmap")
        return
    for tool in NPM_TOOLS:
        if shutil.which(tool["bin"]):
            print(f"{tool['bin']}: already installed")
        elif confirm(f"install {tool['pkg']} globally?"):
            print(f"{tool['bin']}: {'installed' if run([NPM, 'install', '-g', tool['pkg']]) else 'FAILED'}")
        else:
            print(f"{tool['bin']}: skipped")


def register_mcps(env: dict[str, str]) -> None:
    print("\n== external MCP servers (user scope) ==")
    command = [CLAUDE, "mcp", "add", "openalex", "-s", "user"]
    if env.get("OPENALEX_API_KEY"):
        command += ["-e", f"OPENALEX_API_KEY={env['OPENALEX_API_KEY']}"]
    command += ["--", "npx", "-y", "@cyanheads/openalex-mcp-server"]
    run([CLAUDE, "mcp", "remove", "openalex", "-s", "user"])
    print(f"openalex: {'registered' if run(command) else 'FAILED (need claude + npx)'}")
    print("semantic-scholar: pick an MCP from the registry/npm and register it with "
          "-e SEMANTIC_SCHOLAR_API_KEY (from .env) if you set a key")


def write_mcp_json(workspace: Path, env: dict[str, str]) -> None:
    openalex = {"command": "npx", "args": ["-y", "@cyanheads/openalex-mcp-server"]}
    if env.get("OPENALEX_API_KEY"):
        openalex["env"] = {"OPENALEX_API_KEY": env["OPENALEX_API_KEY"]}
    config = {
        "mcpServers": {
            "study": {"command": "uv", "args": ["run", "--project", str(ROOT), "study-mcp"]},
            "openalex": openalex,
        }
    }
    (workspace / ".mcp.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_skills(workspace: Path, skills_from: str) -> None:
    print("\n== skills (.claude/skills) ==")
    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "README.md").write_text(SKILLS_README, encoding="utf-8", newline="\n")
    print(f"  {skills_dir}")
    if not skills_from:
        print("  (no --skills-from; install plugin skills at user scope, add custom skills here)")
        return
    source = Path(skills_from).expanduser()
    if not source.is_dir():
        print(f"  skills-from not found: {source}")
        return
    for entry in sorted(source.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").exists():
            dest = skills_dir / entry.name
            if dest.exists():
                print(f"  {entry.name}: already present")
            else:
                shutil.copytree(entry, dest)
                print(f"  {entry.name}: copied")


def npm_local(workspace: Path, packages: list[str]) -> None:
    print(f"\n== npm tools (local -> {workspace.name}/node_modules) ==")
    if not NPM:
        print("npm not found; install Node.js to get markmap/mmdc")
        return
    child_env = {**os.environ, "PUPPETEER_CACHE_DIR": str(workspace / ".cache" / "puppeteer")}
    ok = run([NPM, "install", "--prefix", str(workspace), *packages], env=child_env)
    bin_dir = workspace / "node_modules" / ".bin"
    for tool in ("markmap", "mmdc"):
        present = (bin_dir / tool).exists() or (bin_dir / f"{tool}.cmd").exists()
        if present:
            print(f"  {tool}: {bin_dir / tool}")
    if not ok:
        print("  (npm reported an error; check network or the package names)")


def workspace_setup(workspace: Path, mermaid: bool, skills_from: str) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    print(f"Workspace setup -> {workspace}")
    env = collect_keys(workspace / ".env")
    write_mcp_json(workspace, env)
    print(f"wrote {workspace / '.mcp.json'}")
    (workspace / "TOOLKIT.md").write_text(toolkit() + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {workspace / 'TOOLKIT.md'}")
    (workspace / ".gitignore").write_text(".env\nnode_modules/\n.cache/\n*.png\n", encoding="utf-8", newline="\n")
    write_skills(workspace, skills_from)
    packages = ["markmap-cli"] + (["@mermaid-js/mermaid-cli"] if mermaid else [])
    npm_local(workspace, packages)
    if not mermaid:
        print("\nmermaid-cli skipped (heavy, pulls Chromium). Add it with --mermaid.")
    report_clis()
    print("\nDone. Open this folder in Claude Code; .mcp.json loads the study and openalex servers.")


def global_setup() -> None:
    print("Global ecosystem setup")
    print(f"platform={PLATFORM} interactive={INTERACTIVE} env={ROOT / '.env'}")
    install_cli()
    install_npm_global()
    env = collect_keys(ROOT / ".env")
    register_mcps(env)
    print("\nDone. Register the workspace MCP servers with: uv run python scripts/register.py")


def _flag_value(args: list[str], name: str) -> str:
    if name in args:
        index = args.index(name)
        if index + 1 < len(args):
            return args[index + 1]
    return ""


def main() -> int:
    args = sys.argv[1:]
    if "--workspace" in args:
        target = _flag_value(args, "--workspace")
        if not target:
            print("usage: setup.py --workspace <dir> [--mermaid] [--skills-from <dir>]")
            return 1
        workspace_setup(Path(target).expanduser(), "--mermaid" in args, _flag_value(args, "--skills-from"))
    else:
        global_setup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
