"""Embedded low-poly 3D design principles and a reference-gathering brief."""
from __future__ import annotations

from typing import Any

_METHOD = """# Method: blockout first
- Solve the BIG shapes, proportion and scale before any detail. If it looks bad in low-poly, it
  looks worse detailed. Moving a few big masses now is cheap; fixing them after detailing is not.
- Work primary -> secondary -> tertiary forms. Each object has a dominant shape (its shape language).
- Tools are secondary to fundamentals: form, proportion, light, composition."""

_SILHOUETTE = """# Silhouette (the readability gate)
- The model must read as a flat black shape, recognizable from every angle. This is the first
  acceptance test; failing it is the most expensive thing to retrofit.
- Render it as a pure black silhouette and check the read before committing to detail
  (the render tool has view='silhouette')."""

_PROPORTION = """# Proportion & scale
- Ground sizes in real references and keep ONE scale grid for the whole project.
- Reference metrics: person ~1.8 m; door ~0.9 x 2.1 m; storey ~2.7-3.0 m; window sill ~0.9 m;
  step rise/run ~0.17 / 0.28 m; corridor ~1.2 m.
- Define relationships (width:height:depth ratios), not just absolutes; avoid extreme footprints."""

_COMPOSITION = """# Composition & placement
- Rhythm and placement of openings (doors/windows) on the grid; use negative space and intentional
  asymmetry. Don't force perfect symmetry or even spacing if the form wants otherwise.
- Place geometry only where it defines form (silhouette edges, major transitions); none on flat planes."""

_COLOR = """# Color & material
- Limited palette: 2-3 materials per object, flat colors or simple gradients; vertex paint is ideal.
- Color reinforces readability: a consistent palette makes important objects stand out.
- Hue-shift the ramp: shadows toward cool, highlights toward warm (not just darker/lighter)."""

_LIGHT = """# Light
- One directional light (top-left standard). Faceted flat shading responds strongly to direction,
  so let light reinforce the geometry; strong, simple shadows define shapes.
- Review under flat/neutral light from all angles to confirm clarity."""

_CONSISTENCY = """# Consistency
- Low-poly is unforgiving: small drifts in proportion, color or shape language are obvious.
- Audit periodically: put all assets in one scene under neutral light and check for style drift.
- Same scale grid, same palette, same outline/edge treatment across the project."""

_SUBJECTS = """# By subject (how to block out)
- building/house: footprint -> storeys (count x storey_height) -> roof (gable/hip/flat) -> openings
  on a grid (door + window rhythm) -> trim. Keep storey ~3 m, door ~2.1 m.
- wall/tower: a primary prism; break the silhouette with a cap/battlement, not surface noise.
- tree: trunk (taper) + 1-3 foliage masses (cone/sphere) with rhythm; silhouette over leaf detail.
- prop: one primary shape + at most one accent; readable when small or partly hidden."""

_GUIDES = {
    "method": _METHOD,
    "silhouette": _SILHOUETTE,
    "proportion": _PROPORTION,
    "composition": _COMPOSITION,
    "color": _COLOR,
    "light": _LIGHT,
    "consistency": _CONSISTENCY,
    "subjects": _SUBJECTS,
}

_KIND_QUERIES = {
    "building": ["{s} elevation orthographic", "{s} floor plan", "{s} architecture facade"],
    "house": ["{s} elevation orthographic", "{s} floor plan", "{s} cottage exterior"],
    "tree": ["{s} silhouette", "{s} branch structure", "{s} low poly tree"],
    "prop": ["{s} 3d game asset", "{s} orthographic views"],
}
_BASE_QUERIES = ["{s} reference photo", "{s} low poly 3D model", "{s} blockout greybox"]


def design_topics() -> list[str]:
    return list(_GUIDES)


def design_guide(topic: str = "") -> str:
    key = topic.strip().lower()
    if not key:
        return "\n\n".join(_GUIDES[name] for name in _GUIDES)
    if key in _GUIDES:
        return _GUIDES[key]
    return f"Unknown topic '{topic}'. Available: {', '.join(_GUIDES)}"


def reference_brief(subject: str, kind: str = "") -> dict[str, Any]:
    name = subject.strip() or "subject"
    queries = [q.format(s=name) for q in _BASE_QUERIES]
    queries += [q.format(s=name) for q in _KIND_QUERIES.get(kind.strip().lower(), [])]
    queries.append(f"{name} silhouette")
    seen: set[str] = set()
    unique = [q for q in queries if not (q in seen or seen.add(q))]
    return {
        "subject": name,
        "kind": kind.strip().lower() or None,
        "queries": unique,
        "look_for": [
            "Primary masses and shape language (the dominant forms).",
            "Real proportions and scale: heights, ratios, metrics you can put on the grid.",
            "Rhythm and placement of openings/features (door, windows, branches).",
            "Roof / canopy type, and the material + color cues (2-3 flats).",
            "The one or two signature features that make it recognizable.",
        ],
        "translate": [
            "Block the big masses first; lock the silhouette from key angles.",
            "Snap sizes to the scale grid (door 2.1 m, storey 3 m, person 1.8 m).",
            "Place openings on the grid with rhythm, not perfectly even.",
            "Keep the palette to 2-3 flat colors; light from a single top-left source.",
            "Add detail only where it reads at gameplay distance.",
        ],
        "workflow": [
            "Run the queries with your own web search; open 2-3 (one real photo, one low-poly "
            "reference, and for buildings a plan/elevation).",
            "Extract masses, proportions and opening positions; then fill the spec (def).",
            "Render it (iso + silhouette) and check before detailing.",
        ],
        "note": "This brief does not fetch images; it says what to search and extract. Use your host "
        "web tools to pull the actual references.",
    }
