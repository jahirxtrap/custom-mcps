# CLAUDE.md — custom-mcps

A personal collection of **standalone MCP servers** (most engine-agnostic, some
domain-specific), managed as a [uv](https://docs.astral.sh/uv/) workspace. Each server runs on its own over **stdio**
and is registered at user scope so every Claude Code client can use it — there is no
host app dependency. Each server lives in `servers/<name>/` with its own library, and that
folder is also its plugin.

## Architecture

```
custom-mcps/                      # uv workspace root (virtual project, package = false)
├── .claude-plugin/marketplace.json   # the plugin marketplace: one entry per server
└── servers/<name>/               # one server = one plugin (own pyproject + [project.scripts] + README)
    ├── .claude-plugin/plugin.json    # the server as a Claude Code plugin
    ├── .mcp.json                 # what the plugin launches: its own installed copy
    ├── constraints.txt           # third-party versions pinned from uv.lock (scripts/pin.py)
    └── src/
        ├── <pkg>_mcp/
        │   ├── server.py         # FastMCP instance + @mcp.tool tools + main()
        │   └── __main__.py       # python -m entry
        └── <lib>/                # its library (py.typed); the plugin runs both from src/
```

- **Plugin marketplace.** Every server is also a Claude Code plugin (author `jahirtrap`; `jahirxtrap`
  is only the GitHub user). The plugin carries the server: its `.mcp.json` runs
  `uv run --no-project --python <requires-python> --with-requirements ${CLAUDE_PLUGIN_ROOT}/constraints.txt python -m <pkg>_mcp`
  with `PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/src`: the source of the copy Claude Code installed, so it
  stays on that version until the plugin is updated, and nothing is fetched from GitHub when it starts.
  Nothing is built either: the environment depends only on the pinned packages, so a new version of
  the plugin reuses it and starts in about 2 s (4 on the VPS); only the first start of a new set of
  pins installs them (6-13 s). A plugin that built itself on every new version (`uvx --from`) went past
  the CLI's 30 s connect limit on the VPS when several updated at once. A server needs nothing outside
  its folder: no workspace sources, its library inside `src/`. A plugin may also bundle third-party
  servers its work needs, pinned to a version and configured through `userConfig`
  (`${user_config.*}`): study brings `openalex` (npx) and `semantic-scholar` (uvx).
  `tests/test_marketplace.py` keeps `plugin.json`, `.mcp.json`, `marketplace.json`, `pyproject.toml`
  and `constraints.txt` in agreement, including the pins and that every option is declared and used.

- **Transport.** Every server is **stdio** (`mcp.run()`); the client launches the process
  on demand and tears it down on close. No port, no FastAPI/uvicorn, nothing long-running.
- **SDK.** [`fastmcp`](https://gofastmcp.com) (v3+). Define tools with `@mcp.tool`; return an
  image with `from fastmcp.utilities.types import Image` (`Image(path=...)` or `Image(data=, format=)`).
- **Packaging.** `hatchling` build backend, `src/` layout, `py.typed` on typed libs. Internal
  deps are wired with `[tool.uv.sources] <pkg> = { workspace = true }`.

## Current members

| Kind | Name | Summary |
|---|---|---|
| library | `pixellib` | Pixel-art primitives: grid, color ramps, shading, outline, preview. |
| server | `pixelart` | Draw/inspect/verify pixel art by data (8/16/32/64); principles embedded. Tools: `pixel_guide`, `search_reference`, `render_sprite`, `from_grid`, `to_grid`, `preview`, `palette`, `check`. |
| library | `audiolib` | SFX synthesis primitives: oscillators, noise, sweeps, FM, envelopes, shaping, audio I/O (ffmpeg > soundfile). |
| server | `sfx` | Synthesize sound effects by data; principles embedded. Tools: `sfx_guide`, `synth_sfx`, `waveform`, `encode`, `inspect`. |
| library | `loaderkit` | Read-only multiloader-workspace toolkit: scan mods/versions, parse gradle.properties, compare loaders, conventions. |
| server | `modkit` | Domain-specific (multiloader mod dev); read-only. Tools: `list_mods`, `mod_info`, `loader_sync`, `check_structure`, `check_json`, `check_access`, `find_symbol`, `decompile_guide`. |
| library | `i18nkit` | Read-only translation checks: flat and namespaced layouts, plural-aware diff, completeness, placeholders, unused keys. |
| server | `i18n` | Keep translation locales in sync (agnostic); read-only. Tools: `locale_diff`, `completeness`, `check_format`, `find_unused`, `i18n_guide`. |
| library | `convkit` | Developer-convention guides + git/static checks (multi-stack); no deps. |
| server | `devkit` | Development conventions + the checks that verify them; read-only. Tools: `conventions`, `commit_style`, `commit_context`, `find_hardcoded`, `find_inconsistent`, `find_format`, `find_duplication`. |
| library | `studykit` | Area- and language-agnostic study toolkit: AI-tell + burstiness checks, LanguageTool grammar check (optional, by URL or jar, Markdown stripped first), extracted-text cleanup, APA citations, concept-map render, ReportLab report/deck typesetting, Word and PowerPoint on a template (python-docx, python-pptx) with template inspection, free-image sourcing, multi-area workspace with a derived inventory. |
| server | `study` | Academic study work by data (agnostic). Tools: `writing_check`, `burstiness`, `grammar_check`, `final_check`, `study_guide`, `concept_map`, `render_document`, `template_inspect`, `cite`, `image_search`, `toolkit`, `workspace_init`, `area_add`, `reference_add`, `workspace_status`. |
| library | `formkit` | Low-poly 3D toolkit: spec->primitives compile, software iso/silhouette renderer (Pillow+NumPy), design principles, Godot def. |
| server | `buildkit` | Design low-poly 3D structures by data (agnostic). Tools: `design_guide`, `search_reference`, `render_preview`, `check`, `godot_def`. |
| library | `tokenkit` | Design tokens read from any theme shape, paired from real code (naming, variant maps, classes used together) and measured against WCAG; no deps. |
| server | `uikit` | Interface design measured against WCAG (agnostic); read-only. Tools: `design_guide`, `read_tokens`, `find_pairs`, `check_contrast`, `review_context`, `contrast`. |

## Commands

```bash
uv sync                     # venv + install all members (editable)
uv run pytest               # tests (tests/)
uv run ruff check .         # lint
uv run <name>-mcp           # run a server over stdio
uv run python scripts/register.py   # register every server with Claude Code (user scope)
uv run python scripts/pin.py        # rewrite each plugin's constraints.txt after uv.lock changes
claude plugin validate .            # the plugin marketplace (and claude plugin validate servers/<name> per plugin)
```

Register a server for every Claude Code session (`uv sync` once first; `--no-sync` keeps each
launch from re-syncing, so startup is fast and never stalls rebuilding on a locked entry point):
```bash
claude mcp add <name> -s user -- uv run --no-sync --project <abs-repo-path> <name>-mcp
```

## Adding a server

1. Create `servers/<name>/pyproject.toml` with `requires-python = ">=3.11"`,
   `dependencies = ["fastmcp>=3.4", ...]`, and `[project.scripts] <name>-mcp = "<pkg>_mcp.server:main"`.
2. `src/<pkg>_mcp/server.py`: build `mcp = FastMCP(name="<name>", instructions=...)`, add
   `@mcp.tool` functions, and `def main(): mcp.run()`. Add `__main__.py` and `__init__.py`.
   **`instructions` is mandatory** — it is the only description that travels over MCP, so a
   client that has none of this repo's docs still knows what the server is for. Three lines:
   what it does, a `Tools:` line naming every tool, and when to reach for it.
   `tests/test_server_instructions.py` fails if a server has none or forgets a tool there.
3. Its library goes in `src/<lib>/` beside `src/<pkg>_mcp/` and in the wheel's `packages`; its
   dependencies go in the server's own `dependencies`. Nothing outside the folder: the plugin is a copy of it.
4. Make it a plugin: `servers/<name>/.claude-plugin/plugin.json` (name, version as in its
   `pyproject.toml`, description, author `jahirtrap`, homepage, repository, license, `icon` pointing at
   `./assets/icon.svg`, keywords),
   `servers/<name>/.mcp.json` (the uvx line above) and its entry in `.claude-plugin/marketplace.json`
   (same description and version, `source: "./servers/<name>"`, keywords as `tags`). Add the
   one-step install line to its README.
5. `uv sync`, `scripts/pin.py`, add tests under `tests/`, update both READMEs and the table above, run
   `claude plugin validate .`, then register it. Every change to a server bumps its version (pyproject,
   `plugin.json`, marketplace entry): that is what an installed plugin updates to.

## The pixelart model (reference for new graphics servers)

Pixel art is drawn **by data, not by perception**: build a `pixellib.Grid` (silhouette →
shade with a top-left light → 1px 8-connected outline → optional symmetry), then save the
PNG. Upscaled previews (`preview` / `pixellib.montage`) are for **verification only**, never
the drawing method. `check` validates against the embedded rules.

### Output contract

Tools that produce an image return a standard image block **and** a text line
`path=<abs> mime=image/png size=NxN ...`. Servers stay UI-agnostic: rendering the image to
a user is the **host agent's** job (e.g. a client that turns the path into a markdown image).
Never hardcode a client, URL, or shared folder into a server.

## Conventions (hard rules)

1. **Agnostic by default; domain-specific only when justified.** Agnostic servers
   (pixelart, sfx) assume no engine/game. A domain server (modkit) may target a domain
   but must still **never hardcode a specific project/instance** (e.g. modkit knows
   "Minecraft multiloader" but never a specific mod name) — it scans generically.
2. **English only.** Code, docstrings, READMEs, identifiers.
3. **No comments.** Self-explanatory names; a short docstring only when it genuinely helps.
   Never inline `#` comments.
4. **Free dependencies that install as wheels on every platform, no native builds.** Pillow is the
   raster stack; in `studykit`, ReportLab (BSD, `py3-none-any`) is the PDF stack and python-docx /
   python-pptx (MIT, on lxml's wheels) the Office stack. No paid services, nothing that needs a
   system install to work. Optional integrations (an Aseprite-CLI importer, LanguageTool) load only
   if the tool is on PATH or configured.
5. **Relative/temp paths.** Never hardcode machine paths; scratch output goes to the system
   temp dir unless an explicit `out_dir` is given. The repo is public on GitHub.
6. **stdio only.** No long-running servers, no auth, no network transport.
7. **Subprocess from a tool: always `stdin=subprocess.DEVNULL`.** A stdio server's stdin is the
   JSON-RPC pipe (never EOF); a child that inherits it (git, ffmpeg, pandoc) blocks reading it and
   hangs the tool call forever — fast as a direct call, dead through the MCP. Also neutralize stdin
   readers explicitly: `git --no-pager`, `ffmpeg -nostdin`.
8. **Register via the venv entry point, not `uv run`.** `scripts/register.py` points each server at
   `.venv/Scripts/<name>-mcp`, so launch never re-syncs/rebuilds (which stalls and contends on
   locked entry points). Run `uv sync` once after dependency changes. This is the local route;
   the plugin route (the installed copy) is for installs without a checkout. Use one per server.
