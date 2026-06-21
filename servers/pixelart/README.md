# pixelart MCP server

A standalone MCP server for **drawing, inspecting and verifying pixel art by data**.
Engine-agnostic (works for 8×8, 16×16, 32×32, 64×64) — it knows nothing about any
project, engine or game. The pixel-art principles are embedded, so it is self-contained;
for reference-driven design and sprite animation it points to the complementary
[pixel-art-sprites](https://github.com/omer-metin/skills-for-antigravity) skill.

Built on [`fastmcp`](https://gofastmcp.com) + [`pillow`](https://python-pillow.org),
on top of the shared [`pixellib`](../../packages/pixellib) library.

## Tools

| Tool | Purpose |
|---|---|
| `pixel_guide` | Embedded pixel-art principles, tuned to a sprite size (color budget, outline gotchas, ramps). |
| `search_reference` | Build a reference brief before drawing: web-search queries (photos + similar pixel arts), what to extract, how to translate to pixels. Optional. |
| `render_sprite` | Render a sprite from a declarative JSON spec (silhouette → shade → outline → symmetry). Returns the upscaled preview + a `path=` line. |
| `from_grid` | Build a PNG from an explicit 2D matrix (hex cells, or symbols + a palette map). |
| `to_grid` | Dump a PNG as a 2D matrix (`hex` or `index` format) to read a reference or edit pixels. |
| `preview` | Upscale PNG(s) with NEAREST on a checkerboard (never blurs) for inspection. |
| `palette` | Extract + count + budget-check a PNG's colors, or generate a ramp from a base color. |
| `check` | Validate a PNG: anti-aliasing, canvas-edge contact, floating pixels, color budget. |

## The `render_sprite` spec

```json
{
  "size": 16,
  "layers": [
    {
      "shape": { "rows": ["....####....", "..."] },
      "fill": { "ramp": { "base": "#8a5a33", "kind": "art" },
                "shade": { "ambient": 0.42, "top": 0.40, "left": 0.24 } }
    }
  ],
  "outline": "#221710",
  "symmetry": false,
  "out": "sprite.png"
}
```

- `shape`: `{rows:[...]}` (ASCII, `.`=empty) · `{rect:[x0,y0,x1,y1]}` · `{disc:[cx,cy,r]}` ·
  `{pixels:[[x,y]...]}` · or a **list** of those (union).
- `fill`: `{color:"#rrggbb"}` (flat) · or `{ramp:{base,kind,steps}, shade:{...}}` where shade is
  `{ambient,top,left}` (directional) or `{sphere:{cx,cy,r}}` (lit sphere).
- `outline`: hex color drawn last, or omit for none.
- `symmetry`: mirror the left half onto the right before outlining.

## Output contract (UI-agnostic)

`render_sprite` and `preview` return a standard image block **and** a text line
`path=<abs> mime=image/png size=NxN ...`. The server never targets a specific UI —
showing the image is the host agent's job (e.g. a client that renders markdown images).

## Integrations

- **Pillow** — all raster I/O and NEAREST upscaling.
- **pixellib** — the shared grid/ramp/shade/outline/preview engine.
- **pixel-art-sprites skill** (complementary, not required): reference-driven design, sprite-sheet
  animation, Aseprite workflows. Install with this server's own setup
  `uv run python servers/pixelart/setup.py`, or directly:
  `npx skills add https://github.com/omer-metin/skills-for-antigravity --skill pixel-art-sprites`.
- **Optional, future**: an Aseprite-CLI importer, enabled only if `aseprite` is on PATH.

## Run / register

```bash
# from the repo root
uv run pixelart-mcp                 # run the server over stdio

# register for every Claude Code session (user scope)
claude mcp add pixelart -s user -- uv run --project /path/to/custom-mcps pixelart-mcp
```
