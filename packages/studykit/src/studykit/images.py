"""Build a free-image sourcing brief for a subject: where to search, license rules, AI only on request."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

_KIND_QUERIES = {
    "photo": ["{s} photo", "{s} high resolution photograph"],
    "diagram": ["{s} diagram", "{s} labeled diagram", "{s} schematic"],
    "illustration": ["{s} illustration", "{s} drawing"],
    "map": ["{s} map", "{s} location map"],
    "portrait": ["{s} portrait", "{s} headshot"],
    "logo": ["{s} logo", "{s} logo transparent"],
}
_BASE_QUERIES = ["{s}", "{s} public domain", "{s} creative commons"]


def _providers(query: str) -> list[dict[str, str]]:
    q = quote_plus(query)
    return [
        {
            "name": "Wikimedia Commons",
            "search": f"https://commons.wikimedia.org/w/index.php?search={q}&title=Special:MediaSearch&type=image",
            "api": f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6"
            f"&gsrsearch={q}&prop=imageinfo&iiprop=url|extmetadata&format=json",
            "license": "public domain and Creative Commons; credit CC BY and CC BY-SA",
        },
        {
            "name": "Openverse",
            "search": f"https://openverse.org/search?q={q}",
            "api": f"https://api.openverse.org/v1/images/?q={q}",
            "license": "CC and public domain; filter with license_type",
        },
        {
            "name": "Google Images (reusable)",
            "search": f"https://www.google.com/search?tbm=isch&tbs=il:cl&q={q}",
            "license": "filtered to Creative Commons; verify on the source page",
        },
        {
            "name": "Flickr Commons",
            "search": f"https://www.flickr.com/search/?text={q}&license=9%2C10",
            "license": "public domain and no known copyright restrictions",
        },
    ]


def image_search(subject: str, kind: str = "") -> dict[str, Any]:
    name = subject.strip() or "subject"
    raw = [q.format(s=name) for q in _BASE_QUERIES]
    raw += [q.format(s=name) for q in _KIND_QUERIES.get(kind.strip().lower(), [])]
    seen: set[str] = set()
    queries: list[str] = []
    for query in raw:
        if query not in seen:
            seen.add(query)
            queries.append(query)
    return {
        "subject": name,
        "kind": kind.strip().lower() or None,
        "decision": "The user asked to search, so pull from the free sources below. Generate with AI "
        "only if the user explicitly asked to generate an image or to use AI.",
        "queries": queries,
        "providers": _providers(name),
        "look_for": [
            "A license that allows your use: public domain and CC0 are free; CC BY and CC BY-SA need credit.",
            "The full-resolution original from the file page, not a thumbnail or a watermarked preview.",
            "An image that clearly matches the subject and the figure's purpose.",
            "The author, title, source URL and license, to store with the figure.",
        ],
        "license": [
            "Public domain and CC0: use freely, no attribution required.",
            "CC BY and CC BY-SA: allowed with credit (author, title, source, license); SA keeps the same license.",
            "Check NonCommercial (NC) and NoDerivs (ND) terms before reusing.",
            "Unsplash, Pexels and Pixabay: free under their own license; crediting is polite.",
        ],
        "ai_generation": {
            "when": "only when the user explicitly asks to generate an image or to use AI",
            "tool": "Pollinations (free, no key): https://image.pollinations.ai/prompt/<text>",
            "note": "disclose that a figure is AI-generated when honesty about the source matters.",
        },
        "workflow": [
            "Run a query on a free provider with your host web search, or fetch the API URL.",
            "Open the file page, confirm the license, and take the full-resolution original.",
            "Record the credit (author, title, source, license) in the caption or reference library.",
            "Generate with AI only if the user explicitly asked for it.",
        ],
        "note": "This brief does not fetch images; it says where to search and what to check. Use your "
        "host web tools (search/fetch) to pull the actual files.",
    }
