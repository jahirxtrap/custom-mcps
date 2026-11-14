# formkit

The library behind the `buildkit` MCP server: **design low-poly 3D structures by data**. It compiles
a high-level spec (a building, a tree, or explicit primitives) into flat primitives, renders a
**software isometric/silhouette preview** (Pillow + NumPy, no GPU), carries the **design principles**,
and emits a **Godot-ready def**. It produces no sculpted/organic art and no final render — that is the
engine's job. Free and self-contained.

## What it gives you

| Module | Provides |
|---|---|
| `compile` | `compile_spec(def)` -> flat primitives (boxes + triangles); `hex_to_rgb`, `rgb_to_hex` |
| `render` | `render(primitives, view)` -> a Pillow image (`iso` flat-shaded, or `silhouette`) |
| `guide` | `design_guide(topic)` (blockout/silhouette/proportion/composition/color/light/consistency/subjects), `reference_brief(subject)` |
| `check` | `check(def)` -> proportion/scale, door fit, palette size, plus the silhouette reminder |
| `godot` | `godot_def(def)` -> a `house_builder`-style def or a generic primitives def + a GDScript builder |

## Example

```python
from formkit import compile_spec, render, check, godot_def

house = {"type": "building", "footprint": [6, 5], "storeys": 2, "storey_height": 3.0,
         "roof": {"type": "gable", "height": 1.6},
         "openings": {"door": {"side": "south", "width": 1.8}, "windows": {"grid": [3, 1]}},
         "palette": {"wall": "#b8a884", "roof": "#7a3b2a"}}

render(compile_spec(house), view="iso").save("house.png")     # flat-shaded preview
render(compile_spec(house), view="silhouette").save("sil.png")  # the silhouette test
check(house)                                                   # proportions / door fit / palette
godot_def(house)                                               # -> Vorenth house_builder def
```

## Notes

- The renderer is a **blockout preview** (massing, proportion, silhouette) via a painter's-algorithm
  ortho/iso projection with flat per-face shading from a top-left light. Some depth-sort artifacts are
  possible on heavily intersecting boxes; that is fine for design verification.
- `design_guide` is grounded in established low-poly/game-art practice (blockout first, silhouette as
  the readability gate, real-world scale, limited palette).
- `godot_def` matches the keys of Vorenth's `house_builder.gd` so a building def drops straight in.
