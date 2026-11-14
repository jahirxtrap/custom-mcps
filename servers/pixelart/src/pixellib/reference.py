"""Build a reference-gathering brief for a subject before drawing it."""
from __future__ import annotations

from typing import Any

from .rules import color_limit

_KIND_QUERIES = {
    "character": ["{s} character reference", "{s} character turnaround", "{s} walk cycle sprite sheet"],
    "creature": ["{s} animal reference photo", "{s} side profile", "{s} creature concept art"],
    "item": ["{s} reference photo", "{s} game icon", "{s} item pixel art"],
    "tile": ["{s} seamless texture", "{s} tileset pixel art", "{s} top-down tile"],
    "environment": ["{s} concept art", "{s} landscape reference", "{s} parallax background pixel art"],
}
_BASE_QUERIES = ["{s} reference photo", "{s} side view", "{s} silhouette"]


def reference_brief(subject: str, size: int = 0, kind: str = "") -> dict[str, Any]:
    name = subject.strip() or "subject"
    pixel_query = f"{name} pixel art {size}x{size}" if size else f"{name} pixel art sprite"
    raw = [q.format(s=name) for q in _BASE_QUERIES]
    raw += [q.format(s=name) for q in _KIND_QUERIES.get(kind.strip().lower(), [])]
    raw += [pixel_query, f"{name} sprite sheet"]
    seen: set[str] = set()
    queries: list[str] = []
    for query in raw:
        if query not in seen:
            seen.add(query)
            queries.append(query)
    budget = list(color_limit(size)) if size else None
    return {
        "subject": name,
        "size": size or None,
        "kind": kind.strip().lower() or None,
        "queries": queries,
        "look_for": [
            "Overall silhouette and the proportions that read at a glance.",
            "The one or two signature features that make it recognizable.",
            "Dominant colors plus one accent hue (hue-shift them, never copy raw photo colors).",
            "Material and form cues (matte / metal / soft) that shading must convey.",
        ],
        "translate": [
            "Block the silhouette first at the target size; readability beats detail.",
            "Pick a small palette within the size budget; build a hue-shifted ramp from base colors.",
            "At small sizes exaggerate the signature features and drop the rest.",
            "Light from a consistent top-left source, not the photo's lighting.",
        ],
        "workflow": [
            "Run the queries with your own web search; open 2-3 of the best results (one realistic "
            "photo plus one or two pixel arts at a similar size).",
            "For a downloaded pixel-art reference, read it with to_grid and its colors with palette.",
            "Then build the render_sprite spec from the silhouette, palette and light you extracted.",
        ],
        "color_budget": budget,
        "note": "This brief does not fetch images; it says what to search and extract. Use your host "
        "web tools (search/fetch) to pull the actual references.",
    }
