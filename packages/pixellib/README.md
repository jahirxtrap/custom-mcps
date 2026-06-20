# pixellib

Engine-agnostic pixel-art primitives, built on Pillow. No project, engine or game
assumptions — just the canonical "draw by data" pipeline used by the `pixelart`
MCP server, exposed as a small, typed library.

## What it gives you

| Module | Provides |
|---|---|
| `grid` | `Grid` (square canvas of optional RGB cells), `rect`, `disc`, `from_rows` |
| `color` | `ramp` / `skin_ramp` / `hair_ramp` / `grayscale_ramp`, `pick`, `hex_to_rgb`, `rgb_to_hex` |
| `shade` | `shade` (top-left directional), `sphere`, `inner_rim` |
| `outline` | `outline` (1px, 8-connected), `edge_contact` (canvas-edge guard) |
| `preview` | `montage` (NEAREST upscale on a checkerboard, for verification) |
| `rules` | `color_limit`, `COLOR_LIMITS`, `guide` (embedded pixel-art principles) |

## The pipeline

```python
from pixellib import Grid, from_rows, ramp, shade, outline, hex_to_rgb

grid = Grid(16)
body = from_rows([
    "................",
    ".....######.....",
    "....########....",
    "....########....",
    "....########....",
    "....########....",
    ".....######.....",
    "................",
])
shade(grid, body, ramp(hex_to_rgb("#8a5a33")))
outline(grid, hex_to_rgb("#221710"))
grid.save("sprite.png")
```

Draw by building data on the grid (silhouette -> shade -> outline), then save.
Never judge from a raw tiny thumbnail — use `montage` to inspect upscaled.

## Design rules

- Hard edges, no anti-aliasing (cells are opaque RGB or `None`).
- Hue-shifted ramps, consistent top-left light.
- 1px 8-connected outline drawn last; keep content >=1px from every canvas edge
  (the outline cannot draw past the border).

See `rules.guide()` for the full embedded guidance.
