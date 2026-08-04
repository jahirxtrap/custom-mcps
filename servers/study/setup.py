"""Install the study ecosystem and store optional API keys in a gitignored .env.

Tiers: a default run installs the light basics; `--all` installs everything that can be
automated (heavier CLIs, slide tools, mermaid, and skills via `claude plugin install`).
Things a script cannot install (proprietary skills without a known marketplace, web-only
services) are always reported, never faked.

  uv run python servers/study/setup.py [--all]
      Global: register the external MCP at user scope; with --all also install the CLIs,
      npm tools, and skill plugins.

  uv run python servers/study/setup.py --workspace <dir> [--all] [--mermaid] [--latex] [--skills-from <dir>]
      Workspace-scoped: keep config inside <dir> (.env, .mcp.json, TOOLKIT.md, .gitignore,
      styles/apa.csl, .claude/skills) and install npm tools under <dir>/node_modules.
      Basics install markmap + Marp and repair pandoc when it is older than 2.11; --mermaid adds
      mermaid, --latex adds TinyTeX, and --all adds every one of those plus the system CLIs,
      video-audio and the skill plugins.
"""
from __future__ import annotations

import json
import os
import platform as platform_module
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from studykit import toolkit

ROOT = Path(__file__).resolve().parents[2]
CLAUDE = shutil.which("claude") or "claude"
NPM = shutil.which("npm")
GIT = shutil.which("git")
UV = shutil.which("uv")
VIDEO_AUDIO_REPO = "https://github.com/misbahsy/video-audio-mcp.git"
PLATFORM = "win" if sys.platform.startswith("win") else "mac" if sys.platform == "darwin" else "linux"
INTERACTIVE = sys.stdin.isatty()
APA_CSL_URL = "https://raw.githubusercontent.com/citation-style-language/styles/master/apa.csl"

USER_AGENT = "study-setup"
SEMANTIC_PIN = ["--with", "mcp[cli]<2"]
PANDOC_MIN = (2, 11)
PANDOC_LATEST_API = "https://api.github.com/repos/jgm/pandoc/releases/latest"
TINYTEX_URL = "https://yihui.org/tinytex/install-bin-unix.sh"
LATEX_PACKAGES = [
    "apa7",
    "biber",
    "biblatex",
    "biblatex-apa",
    "booktabs",
    "caption",
    "csquotes",
    "endfloat",
    "fancyhdr",
    "pgf",
    "scalerel",
    "threeparttable",
    "babel-english",
    "babel-spanish",
    "hyphen-spanish",
]
LOCAL_BIN = Path.home() / ".local" / "bin"

CLI_TOOLS = [
    {"bin": "pandoc", "win": "JohnMacFarlane.Pandoc", "mac": "pandoc", "linux": "pandoc"},
    {"bin": "ffmpeg", "win": "Gyan.FFmpeg", "mac": "ffmpeg", "linux": "ffmpeg"},
    {"bin": "dot", "label": "graphviz", "win": "Graphviz.Graphviz", "mac": "graphviz", "linux": "graphviz"},
    {
        "bin": "soffice",
        "label": "libreoffice",
        "win": "TheDocumentFoundation.LibreOffice",
        "mac": "libreoffice",
        "linux": "libreoffice",
    },
]

OPTIONAL_KEYS = [
    ("OPENALEX_API_KEY", "OpenAlex contact email for the polite pool (free; blank to skip)"),
    ("SEMANTIC_SCHOLAR_API_KEY", "Semantic Scholar API key to raise limits (blank to skip)"),
]

ENV_HEADER = (
    "# Optional API keys for the research MCPs (openalex, semantic-scholar). Both work without a\n"
    "# key; set one only to raise rate limits. This file is gitignored, never commit it."
)

SKILL_PLUGINS = [
    {
        "plugin": "superpowers",
        "marketplace": "claude-plugins-official",
        "provides": "brainstorming, writing-plans, systematic-debugging",
    },
]

SKILL_MANUAL = [
    {
        "name": "humanizer",
        "how": "claude plugin marketplace add <repo> ; claude plugin install humanizer@<marketplace>",
    },
    {
        "name": "docx/pptx/xlsx/pdf",
        "how": "Anthropic doc skills (proprietary): add their marketplace, then claude plugin install",
    },
]

SKILLS_README = """# Skills (project-scoped)

Skills placed here load automatically when this folder is open in Claude Code (project scope).
Plugin skills installed once at user scope are also available here, so most skills do not need
to be copied per project.

Install via Claude Code plugins:
- superpowers (brainstorming, writing-plans, systematic-debugging):
  claude plugin install superpowers@claude-plugins-official
- humanizer: add its marketplace, then claude plugin install humanizer@<marketplace>
- docx / pptx / xlsx / pdf: Anthropic document skills (proprietary), from their marketplace.

Use this folder for skills specific to this workspace (a `<name>/SKILL.md` per skill). To bundle
your own copies of existing skills into a portable workspace, run setup with
`--skills-from <your skills dir>`.
"""


def run(command: list[str], env: dict[str, str] | None = None, cwd: str | None = None) -> bool:
    done = subprocess.run(command, capture_output=True, text=True, env=env, cwd=cwd)
    if done.returncode != 0:
        tail = (done.stderr or done.stdout).strip().splitlines()[-1:] or [""]
        print(f"  ! {tail[0]}")
    return done.returncode == 0


def download(url: str, dest: Path) -> bool:
    """Some CDNs (yihui.org among them) answer 403 to urllib's default User-Agent."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            dest.write_bytes(response.read())
        return True
    except Exception as error:
        print(f"  ! {error}")
        return False


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def write_env(path: Path, values: dict[str, str]) -> None:
    known = {key for key, _ in OPTIONAL_KEYS}
    lines = [ENV_HEADER, ""]
    for key, description in OPTIONAL_KEYS:
        lines += [f"# {description}", f"{key}={values.get(key, '')}", ""]
    extra = [f"{key}={value}" for key, value in values.items() if key not in known and value]
    if extra:
        lines += [*extra, ""]
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8", newline="\n")


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
    if INTERACTIVE:
        for key, description in OPTIONAL_KEYS:
            current = values.get(key, "")
            shown = f" [current: {current}]" if current else ""
            entered = _ask(f"{description}{shown}: ")
            if entered is None:
                break
            if entered:
                values[key] = entered
    else:
        print("non-interactive; writing the .env template (fill the keys later)")
    write_env(env_path, values)
    print(f"saved {env_path}")
    return values


def install_cli(auto: bool) -> None:
    print("\n== system CLIs ==")
    for tool in CLI_TOOLS:
        label = tool.get("label", tool["bin"])
        if shutil.which(tool["bin"]):
            print(f"  {label}: already installed")
            continue
        do = auto or confirm(f"install {label}?")
        if not do:
            print(f"  {label}: skipped (see TOOLKIT.md)")
            continue
        if PLATFORM == "win" and shutil.which("winget"):
            ok = run([
                "winget", "install", "--id", tool["win"], "-e", "--source", "winget",
                "--accept-package-agreements", "--accept-source-agreements",
            ])
        elif PLATFORM == "mac" and shutil.which("brew"):
            ok = run(["brew", "install", tool["mac"]])
        elif PLATFORM == "linux" and shutil.which("apt"):
            ok = run(["sudo", "apt", "install", "-y", tool["linux"]])
        else:
            ok = False
        print(f"  {label}: {'installed' if ok else 'install manually (see TOOLKIT.md)'}")
    print("  d2: manual (no verified per-OS installer); see https://d2lang.com")


def pandoc_version() -> tuple[int, ...] | None:
    binary = shutil.which("pandoc")
    if not binary:
        return None
    done = subprocess.run([binary, "--version"], capture_output=True, text=True)
    if done.returncode != 0 or not done.stdout.strip():
        return None
    parts = done.stdout.splitlines()[0].split()[-1].split(".")
    numbers = tuple(int(part) for part in parts if part.isdigit())
    return numbers or None


def install_pandoc_local() -> bool:
    """Distro pandoc is often older than 2.11, where `--citeproc` replaced the separate
    pandoc-citeproc filter; fetch the official static build into ~/.local/bin, no root needed."""
    if PLATFORM != "linux":
        return False
    machine = platform_module.machine().lower()
    arch = "arm64" if machine in ("aarch64", "arm64") else "amd64"
    try:
        with urllib.request.urlopen(PANDOC_LATEST_API, timeout=30) as response:
            release = json.load(response)
    except Exception as error:
        print(f"  ! {error}")
        return False
    asset = next(
        (item for item in release.get("assets", []) if item["name"].endswith(f"linux-{arch}.tar.gz")), None
    )
    if not asset:
        print(f"  ! no linux-{arch} build in the latest release")
        return False
    with tempfile.TemporaryDirectory() as scratch:
        archive = Path(scratch) / asset["name"]
        if not download(asset["browser_download_url"], archive):
            return False
        with tarfile.open(archive) as bundle:
            try:
                bundle.extractall(scratch, filter="data")
            except TypeError:
                bundle.extractall(scratch)
        found = next(Path(scratch).glob("pandoc-*/bin/pandoc"), None)
        if not found:
            print("  ! unexpected archive layout")
            return False
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)
        shutil.copy2(found, LOCAL_BIN / "pandoc")
        (LOCAL_BIN / "pandoc").chmod(0o755)
    return True


def ensure_pandoc(auto: bool) -> None:
    print("\n== pandoc (automatic APA bibliography) ==")
    version = pandoc_version()
    minimum = ".".join(str(part) for part in PANDOC_MIN)
    if version and version >= PANDOC_MIN:
        print(f"  pandoc {'.'.join(str(part) for part in version)}: --citeproc available")
        return
    state = "not installed" if version is None else f"{'.'.join(str(part) for part in version)} is too old"
    print(f"  {state}; --citeproc needs pandoc {minimum}+")
    if not (auto or confirm(f"install the official pandoc build into {LOCAL_BIN}?")):
        print("  skipped (see TOOLKIT.md)")
        return
    if install_pandoc_local():
        print(f"  installed -> {LOCAL_BIN / 'pandoc'}  (ensure {LOCAL_BIN} is on PATH)")
    else:
        print("  install manually: https://github.com/jgm/pandoc/releases")


def _tlmgr() -> str | None:
    found = shutil.which("tlmgr")
    if found:
        return found
    return next((str(path) for path in sorted((Path.home() / ".TinyTeX" / "bin").glob("*/tlmgr"))), None)


def install_latex(auto: bool) -> None:
    print("\n== LaTeX (TinyTeX, for strict APA 7 papers) ==")
    if shutil.which("pdflatex") or shutil.which("xelatex"):
        print("  already installed")
        return
    if PLATFORM == "win":
        print("  manual: see https://yihui.org/tinytex/ (PowerShell installer)")
        return
    if not (auto or confirm("install TinyTeX (~200 MB, no root)?")):
        print("  skipped (see TOOLKIT.md)")
        return
    with tempfile.TemporaryDirectory() as scratch:
        script = Path(scratch) / "install-tinytex.sh"
        if not download(TINYTEX_URL, script):
            return
        if not run(["sh", str(script)]):
            print("  install failed; see https://yihui.org/tinytex/")
            return
    tlmgr = _tlmgr()
    if not tlmgr:
        print("  installed, but tlmgr is not on PATH yet; in a new shell run:"
              f" tlmgr install {' '.join(LATEX_PACKAGES)}")
        return
    ok = run([tlmgr, "install", *LATEX_PACKAGES])
    print(f"  TinyTeX installed; apa7 packages: {'ok' if ok else 'run tlmgr install manually'}")
    run([tlmgr, "path", "add"])


def install_npm(packages: list[str], prefix: Path | None = None) -> None:
    location = f"local -> {prefix.name}/node_modules" if prefix else "global"
    print(f"\n== npm tools ({location}) ==")
    if not NPM:
        print("  npm not found; install Node.js")
        return
    command = [NPM, "install", *(["--prefix", str(prefix)] if prefix else ["-g"]), *packages]
    env = {**os.environ, "PUPPETEER_CACHE_DIR": str((prefix or ROOT) / ".cache" / "puppeteer")}
    ok = run(command, env=env)
    print(f"  {' '.join(packages)}: {'installed' if ok else 'FAILED (check network)'}")


def record_chrome_path(workspace: Path) -> None:
    """marp-cli ships no browser: it needs CHROME_PATH pointing at one. The puppeteer cache that
    mermaid-cli fills is the only Chrome a workspace install is guaranteed to have."""
    print("\n== Chrome for Marp (CHROME_PATH) ==")
    cache = workspace / ".cache" / "puppeteer"
    found = next((path for path in sorted(cache.rglob("chrome")) if path.is_file()), None)
    if not found:
        print("  no browser found; Marp can render HTML but not PDF/PPTX")
        print("  fix: rerun with --mermaid (downloads Chrome), or set CHROME_PATH to your own")
        return
    env_path = workspace / ".env"
    values = read_env(env_path)
    values["CHROME_PATH"] = str(found)
    write_env(env_path, values)
    print(f"  CHROME_PATH={found}")
    print(f"  recorded in {env_path.name}; export it before calling marp")


def install_skills(auto: bool) -> None:
    print("\n== skills (Claude Code plugins) ==")
    if not auto:
        print("  skipped (run with --all). To add them yourself:")
        for plugin in SKILL_PLUGINS:
            print(f"    claude plugin install {plugin['plugin']}@{plugin['marketplace']}  ({plugin['provides']})")
        for manual in SKILL_MANUAL:
            print(f"    {manual['name']}: {manual['how']}")
        return
    for plugin in SKILL_PLUGINS:
        ok = run([CLAUDE, "plugin", "install", f"{plugin['plugin']}@{plugin['marketplace']}"])
        print(f"  {plugin['plugin']}: {'installed' if ok else 'FAILED'} ({plugin['provides']})")
    for manual in SKILL_MANUAL:
        print(f"  {manual['name']}: manual -> {manual['how']}")


def register_mcps(env: dict[str, str]) -> None:
    print("\n== external MCP servers (user scope) ==")
    command = [CLAUDE, "mcp", "add", "openalex", "-s", "user"]
    if env.get("OPENALEX_API_KEY"):
        command += ["-e", f"OPENALEX_API_KEY={env['OPENALEX_API_KEY']}"]
    command += ["--", "npx", "-y", "@cyanheads/openalex-mcp-server"]
    run([CLAUDE, "mcp", "remove", "openalex", "-s", "user"])
    print(f"  openalex: {'registered' if run(command) else 'FAILED (need claude + npx)'}")


def study_command() -> dict[str, object]:
    """Prefer the venv entry point: `uv run` re-syncs on launch and clashes with the user-scope
    registration, which points at the same binary."""
    scripts = ROOT / ".venv" / ("Scripts" if PLATFORM == "win" else "bin")
    entry = scripts / ("study-mcp.exe" if PLATFORM == "win" else "study-mcp")
    if entry.exists():
        return {"command": str(entry), "args": []}
    return {"command": "uv", "args": ["run", "--no-sync", "--project", str(ROOT), "study-mcp"]}


def write_mcp_json(workspace: Path, env: dict[str, str]) -> None:
    openalex: dict[str, object] = {"command": "npx", "args": ["-y", "@cyanheads/openalex-mcp-server"]}
    if env.get("OPENALEX_API_KEY"):
        openalex["env"] = {"OPENALEX_API_KEY": env["OPENALEX_API_KEY"]}
    semantic: dict[str, object] = {"command": "uvx", "args": [*SEMANTIC_PIN, "semantic-scholar-mcp"]}
    if env.get("SEMANTIC_SCHOLAR_API_KEY"):
        semantic["env"] = {"SEMANTIC_SCHOLAR_API_KEY": env["SEMANTIC_SCHOLAR_API_KEY"]}
    servers: dict[str, object] = {
        "study": study_command(),
        "openalex": openalex,
        "semantic-scholar": semantic,
    }
    video = workspace / "tools" / "video-audio-mcp"
    if (video / "server.py").exists():
        servers["video-audio"] = {"command": "uv", "args": ["run", "--directory", str(video), "server.py"]}
    (workspace / ".mcp.json").write_text(
        json.dumps({"mcpServers": servers}, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def install_video_audio(workspace: Path) -> None:
    print("\n== video-audio MCP (misbahsy/video-audio-mcp) ==")
    dest = workspace / "tools" / "video-audio-mcp"
    if (dest / ".venv").exists():
        print("  already installed")
        return
    if not (dest / "server.py").exists():
        if not GIT:
            print("  git not found; skipping")
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not run([GIT, "clone", "--depth", "1", VIDEO_AUDIO_REPO, str(dest)]):
            print("  clone failed")
            return
    (dest / ".python-version").write_text("3.13\n", encoding="utf-8", newline="\n")
    if UV and run([UV, "sync"], cwd=str(dest)):
        print(f"  installed at {dest}")
    else:
        print(f"  cloned at {dest} (uv sync failed; run it there to finish)")


def write_skills_dir(workspace: Path, skills_from: str) -> None:
    print("\n== skills folder (.claude/skills) ==")
    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "README.md").write_text(SKILLS_README, encoding="utf-8", newline="\n")
    print(f"  {skills_dir}")
    if not skills_from:
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


def workspace_setup(workspace: Path, all_: bool, mermaid: bool, latex: bool, skills_from: str) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    print(f"Workspace setup -> {workspace}  (mode: {'all' if all_ else 'basics'})")
    env = collect_keys(workspace / ".env")
    if all_:
        install_video_audio(workspace)
    write_mcp_json(workspace, env)
    print(f"wrote {workspace / '.mcp.json'}")
    (workspace / "TOOLKIT.md").write_text(toolkit() + "\n", encoding="utf-8", newline="\n")
    (workspace / ".gitignore").write_text(
        ".env\nnode_modules/\n.venv/\n.cache/\n*.png\n", encoding="utf-8", newline="\n"
    )
    puppeteer = {"args": ["--no-sandbox"]}
    (workspace / "puppeteer-config.json").write_text(
        json.dumps(puppeteer, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {workspace / 'puppeteer-config.json'}")

    styles = workspace / "styles"
    styles.mkdir(parents=True, exist_ok=True)
    print("\n== apa.csl ==")
    if (styles / "apa.csl").exists():
        print("  styles/apa.csl: already present")
    else:
        print(f"  styles/apa.csl: {'downloaded' if download(APA_CSL_URL, styles / 'apa.csl') else 'download failed'}")

    write_skills_dir(workspace, skills_from)

    packages = ["markmap-cli", "@marp-team/marp-cli"]
    if all_ or mermaid:
        packages.append("@mermaid-js/mermaid-cli")
    install_npm(packages, prefix=workspace)
    record_chrome_path(workspace)

    ensure_pandoc(auto=all_)
    if all_ or latex:
        install_latex(auto=True)

    if all_:
        install_cli(auto=True)
        install_skills(auto=True)
    else:
        install_skills(auto=False)
        print("\nbasics done. Run with --all to also clone video-audio, install mermaid, the system"
              " CLIs, LaTeX and skills.")
    print("\nOpen this folder in Claude Code; .mcp.json loads study, openalex, semantic-scholar"
          " (and video-audio if cloned).")


def global_setup(all_: bool) -> None:
    print(f"Global ecosystem setup  (mode: {'all' if all_ else 'basics'})")
    print(f"platform={PLATFORM} interactive={INTERACTIVE} env={ROOT / '.env'}")
    env = collect_keys(ROOT / ".env")
    register_mcps(env)
    if all_:
        install_cli(auto=True)
        ensure_pandoc(auto=True)
        install_latex(auto=True)
        install_npm(["@mermaid-js/mermaid-cli", "markmap-cli", "@marp-team/marp-cli"])
        install_skills(auto=True)
    else:
        install_cli(auto=False)
        ensure_pandoc(auto=False)
        install_latex(auto=False)
        install_skills(auto=False)
        print("\nbasics done. Run with --all to install CLIs, LaTeX, npm tools and skills without prompts.")


def _flag_value(args: list[str], name: str) -> str:
    if name in args:
        index = args.index(name)
        if index + 1 < len(args):
            return args[index + 1]
    return ""


def main() -> int:
    args = sys.argv[1:]
    all_ = "--all" in args
    if "--workspace" in args:
        target = _flag_value(args, "--workspace")
        if not target:
            print("usage: setup.py --workspace <dir> [--all] [--mermaid] [--latex] [--skills-from <dir>]")
            return 1
        workspace_setup(
            Path(target).expanduser(),
            all_,
            "--mermaid" in args,
            "--latex" in args,
            _flag_value(args, "--skills-from"),
        )
    else:
        global_setup(all_)
    return 0


if __name__ == "__main__":
    sys.exit(main())
