# custom-mcps

A personal collection of **standalone MCP servers** for Claude Code. Each one runs
on its own over **stdio** and is registered once at user scope, so every Claude Code
client — the CLI, the desktop app, the web app, or any host that loads user MCP
servers — can reach it. Nothing stays running: there's no app and no service, the
client launches a server on demand and tears it down when the turn is done.

```
[Any Claude Code client] ──stdio──> [a custom-mcps server, on demand]
```

It's a [uv](https://docs.astral.sh/uv/) workspace — shared libraries in `packages/`,
servers in `servers/` — so adding a server is a single new folder.

## Servers

| Server | What it does |
|---|---|
| **pixelart** | Draw, inspect and verify pixel art by data — any size, no project assumptions. |

## pixelart

**pixelart** treats pixel art as something you build by **data, not by eye**. You
describe a sprite — a silhouette, a color ramp, a light direction — and it renders
the native PNG plus an upscaled, checkerboard **preview you can actually read**,
instead of squinting at a 16-pixel thumbnail.

- **render_sprite** is the heart of it: a declarative JSON spec — silhouette, then
  shading from a consistent top-left light, then a 1px outline, then optional
  symmetry — becomes a finished sprite in one call.
- **from_grid** and **to_grid** move between an explicit pixel matrix and a PNG, so
  you can read a reference, hand-place pixels, or edit an existing sprite as data.
- **preview** upscales any PNG with nearest-neighbor on a checkerboard — it never
  blurs — to judge how a sprite is coming along.
- **palette** extracts and budget-checks a sprite's colors, or generates a
  hue-shifted ramp (art, skin, hair, or neutral grayscale) from a single base color.
- **check** flags the usual mistakes: anti-aliasing, content touching the canvas
  edge, floating pixels, and going over the per-size color budget.
- **pixel_guide** carries the pixel-art principles with it, so the server is
  self-contained and needs no external skill or reference.

It's **agnostic by design** — 8×8, 16×16, 32×32, 64×64, with no idea what engine or
game the art is for. Tools that produce an image return both the picture and a
`path=` line, so whatever host you're in can show it.

See [`servers/pixelart`](servers/pixelart) for the full spec and tool reference, and
[`packages/pixellib`](packages/pixellib) for the underlying drawing library.

## Structure

```
custom-mcps/
├── packages/
│   └── pixellib/    # shared drawing library — grid, ramps, shading, outline, preview
├── servers/
│   └── pixelart/    # the MCP server — own pyproject, entry point and README
└── tests/           # workspace test suite (pytest)
```

## Setup

```bash
uv sync             # create the venv and install every workspace member
uv run pytest       # run the test suite
```

## Use it from Claude Code

Register a server once at user scope and it's available in every session — the tools
show up as `mcp__pixelart__*`:

```bash
claude mcp add pixelart -s user -- uv run --project /path/to/custom-mcps pixelart-mcp
```

Or run it straight from the repo, without a local checkout:

```bash
claude mcp add pixelart -s user -- uvx --from git+https://github.com/jahirxtrap/custom-mcps pixelart-mcp
```

## Add a server

Drop a folder under `servers/<name>/` with its own `pyproject.toml` and a
`FastMCP` instance exposing `main()`, reuse `pixellib` (or add a package under
`packages/`), run `uv sync`, and register it. The contributor guide lives in
[CLAUDE.md](CLAUDE.md).

## License

MIT — see [LICENSE](LICENSE).
