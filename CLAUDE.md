# CLAUDE.md — custom-mcps

A personal collection of **standalone MCP servers** (most engine-agnostic, some
domain-specific), managed as a [uv](https://docs.astral.sh/uv/) workspace. Each server runs on its own over **stdio**
and is registered at user scope so every Claude Code client can use it — there is no
host app dependency. Shared code lives in `packages/`, servers in `servers/`.

## Architecture

```
custom-mcps/                      # uv workspace root (virtual project, package = false)
├── packages/<lib>/               # shared libraries (src layout, py.typed, hatchling)
│   └── src/<lib>/
└── servers/<name>/               # MCP servers (own pyproject + [project.scripts] + README)
    └── src/<pkg>_mcp/
        ├── server.py             # FastMCP instance + @mcp.tool tools + main()
        └── __main__.py           # python -m entry
```

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
| library | `i18nkit` | Read-only translation checks: parse flat/nested locales, diff, completeness, placeholders, unused keys. |
| server | `i18n` | Keep translation locales in sync (agnostic); read-only. Tools: `locale_diff`, `completeness`, `check_format`, `find_unused`, `i18n_guide`. |
| library | `convkit` | Developer-convention guides + git/static checks (multi-stack); no deps. |
| server | `devkit` | The user's dev conventions + checks (personal); read-only. Tools: `conventions`, `commit_style`, `commit_context`, `find_hardcoded`, `find_inconsistent`, `find_format`, `find_duplication`. |
| library | `studykit` | Area- and language-agnostic study toolkit: AI-tell + burstiness checks, APA citations, concept-map render, multi-area workspace. |
| server | `study` | Academic study work by data (agnostic). Tools: `writing_check`, `burstiness`, `study_guide`, `concept_map`, `cite`, `toolkit`, `workspace_init`, `area_add`, `reference_add`, `workspace_status`. |

## Commands

```bash
uv sync                     # venv + install all members (editable)
uv run pytest               # tests (tests/)
uv run ruff check .         # lint
uv run <name>-mcp           # run a server over stdio
uv run python scripts/register.py   # register every server with Claude Code (user scope)
```

Register a server for every Claude Code session (`uv sync` once first; `--no-sync` keeps each
launch from re-syncing, so startup is fast and never stalls rebuilding on a locked entry point):
```bash
claude mcp add <name> -s user -- uv run --no-sync --project <abs-repo-path> <name>-mcp
```

## Adding a server

1. Create `servers/<name>/pyproject.toml` with `requires-python = ">=3.11"`,
   `dependencies = ["fastmcp>=3.4", ...]`, and `[project.scripts] <name>-mcp = "<pkg>_mcp.server:main"`.
2. `src/<pkg>_mcp/server.py`: build `mcp = FastMCP(name="<name>")`, add `@mcp.tool` functions,
   and `def main(): mcp.run()`. Add `__main__.py` and `__init__.py`.
3. Reuse `pixellib` or add a package under `packages/`; wire it with `[tool.uv.sources]`.
4. `uv sync`, add tests under `tests/`, update both READMEs and the table above, then register it.

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
4. **Pillow-only** raster stack. No heavyweight, native, or paid dependencies in a core server.
   Optional integrations (e.g. an Aseprite-CLI importer) load only if the tool is on PATH.
5. **Relative/temp paths.** Never hardcode machine paths; scratch output goes to the system
   temp dir unless an explicit `out_dir` is given. The repo is public on GitHub.
6. **stdio only.** No long-running servers, no auth, no network transport.
