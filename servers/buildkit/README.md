# buildkit

An MCP server for **designing low-poly 3D structures by data** — buildings, houses, walls, trees,
props. It is the 3D counterpart of `pixelart`: it carries the **design principles**, gathers
**references**, lets you **define** a structure by spec, **previews** it (isometric + silhouette), and
**checks** it — then emits a **Godot-ready def**. Free and self-contained (Pillow + NumPy, no GPU, no
paid services). It does **not** sculpt detailed/organic art and does not do a final render — that is
the engine's job.

It fits Vorenth's actual pipeline: `house_builder.gd` already builds houses from a `def` dictionary
(`size`, `height`, `roof_height`, `wall_color`, `door`) using boxes + a `SurfaceTool` roof. buildkit
designs and previews that spec, and `godot_def` emits it in the same shape.

## Tools

| Tool | Args | What it does |
|---|---|---|
| `design_guide` | `topic=""` | Low-poly 3D principles: method (blockout first) / silhouette / proportion / composition / color / light / consistency / subjects. |
| `search_reference` | `subject`, `kind=""` | Reference brief: queries (photos, low-poly, plans/elevations), what to extract, how to translate. Doesn't fetch. |
| `render_preview` | `spec`, `view="iso"`, `out_dir=""` | Blockout preview of the spec to a PNG (returns the image + `path=`). `view=iso` or `silhouette`. |
| `check` | `spec` | Proportion/scale, door fit, footprint ratio, palette size, silhouette reminder. |
| `godot_def` | `spec` | A `house_builder`-style def for buildings, or a generic primitives def + a GDScript `FormBuilder`. |

## The spec

```jsonc
// building
{ "type": "building", "footprint": [6, 5], "storeys": 2, "storey_height": 3.0,
  "roof": { "type": "gable|hip|flat|pyramid", "height": 1.6, "overhang": 0.5 },
  "openings": { "door": { "side": "south", "width": 1.8, "height": 2.2 },
                "windows": { "grid": [3, 1], "size": [1.0, 1.2], "sill": 0.9 } },
  "palette": { "wall": "#b8a884", "roof": "#7a3b2a", "door": "#5a3b2a" } }
// tree
{ "type": "tree", "trunk": { "height": 2.5, "radius": 0.25 },
  "foliage": [ { "shape": "cone", "radius": 1.4, "height": 2.0, "y": 2.5 } ],
  "palette": { "trunk": "#5a3b2a", "leaves": "#3a6b3a" } }
// group (explicit primitives)
{ "type": "group", "parts": [ { "box": [1, 2, 1], "at": [0, 1, 0], "color": "#888" } ] }
```

## The loop (same as pixelart)

`search_reference` (gather) -> `design_guide` (principles) -> spec defines forms/sizes/positions ->
`render_preview` (iso + silhouette to verify) -> `check` -> `godot_def` (into Godot).

## Output contract

`render_preview` returns a standard image block plus a `path=<abs> mime=image/png size=NxN view=...`
line. The server stays UI-agnostic; showing the image is the host agent's job.

See [`packages/formkit`](../../packages/formkit) for the underlying library.
