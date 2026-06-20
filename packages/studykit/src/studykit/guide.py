"""Embedded study guides and the ecosystem toolkit catalog."""
from __future__ import annotations

from .assets import CITATION_APA, STRUCTURE_GUIDE, VISUAL_GUIDE, WRITING_RULES

_GUIDES = {
    "writing": WRITING_RULES,
    "citations": CITATION_APA,
    "structure": STRUCTURE_GUIDE,
    "visual": VISUAL_GUIDE,
}

_ALIASES = {
    "apa": "citations",
    "cite": "citations",
    "references": "citations",
    "style": "writing",
    "anti-ai": "writing",
    "humanize": "writing",
    "organizer": "visual",
    "maps": "visual",
    "design": "visual",
}


def guide_topics() -> list[str]:
    return list(_GUIDES)


def study_guide(topic: str = "") -> str:
    key = topic.strip().lower()
    if not key:
        body = "\n\n".join(_GUIDES[name] for name in _GUIDES)
        return f"Study guide topics: {', '.join(_GUIDES)}\n\n{body}"
    if key in _GUIDES:
        return _GUIDES[key]
    if key in _ALIASES:
        return _GUIDES[_ALIASES[key]]
    return f"Unknown topic '{topic}'. Available: {', '.join(_GUIDES)}"


_TOOLKIT: dict[str, list[dict[str, str]]] = {
    "documents": [
        {
            "name": "Anthropic document skills (docx, pptx, xlsx, pdf)",
            "what": "create and read Office documents and PDFs",
            "install": "enable the document skills in Claude Code (see docs.claude.com skills)",
        },
        {
            "name": "Marp / Slidev",
            "what": "slides from Markdown",
            "install": "npm i -g @marp-team/marp-cli  (or)  npm i -g @slidev/cli",
        },
    ],
    "research": [
        {
            "name": "deep-research skill",
            "what": "fan-out web search, verify, cite a report",
            "install": "available as a Claude Code skill",
        },
        {
            "name": "OpenAlex MCP",
            "what": "open catalog of papers, citation graph, literature review",
            "install": "claude mcp add openalex -s user -- npx -y @cyanheads/openalex-mcp-server",
            "get_key": "free, no key required; set a contact email for the polite pool",
            "configure": "add -e OPENALEX_API_KEY=you@example.com before the -- in the install command",
        },
        {
            "name": "Semantic Scholar MCP",
            "what": "225M+ papers, citations, authors",
            "install": "pick a Semantic Scholar MCP from the MCP registry / npm and follow its README",
            "get_key": "optional; request a key at https://www.semanticscholar.org/product/api to raise rate limits",
            "configure": "register it with -e SEMANTIC_SCHOLAR_API_KEY=... (the key, if any, lives in .env)",
        },
    ],
    "citations": [
        {
            "name": "pandoc + citeproc",
            "what": "format citations and convert Markdown to docx/pdf",
            "install": "winget install JohnMacFarlane.Pandoc  |  brew install pandoc  |  apt install pandoc",
            "configure": "pandoc essay.md --citeproc --bibliography=references.bib --csl=styles/apa.csl -o essay.docx",
        },
        {
            "name": "apa.csl",
            "what": "APA 7 citation style for pandoc",
            "install": "download from https://raw.githubusercontent.com/citation-style-language/styles/master/apa.csl",
        },
    ],
    "diagrams": [
        {"name": "mermaid-cli (mmdc)", "what": "flowcharts from text", "install": "npm i -g @mermaid-js/mermaid-cli"},
        {"name": "markmap-cli", "what": "mind maps from Markdown", "install": "npm i -g markmap-cli"},
        {
            "name": "graphviz (dot)",
            "what": "graphs",
            "install": "winget install Graphviz.Graphviz  |  brew install graphviz  |  apt install graphviz",
        },
        {"name": "d2", "what": "styled diagrams", "install": "see https://d2lang.com (installer or package manager)"},
    ],
    "latex": [
        {
            "name": "TinyTeX",
            "what": "LaTeX (pdflatex/xelatex/latexmk, class apa7) for strict APA PDFs",
            "install": "see https://yihui.org/tinytex/ ; then tlmgr install apa7 biblatex-apa",
        },
    ],
    "images": [
        {
            "name": "Pollinations",
            "what": "free text-to-image, no key, no GPU",
            "install": "GET https://image.pollinations.ai/prompt/<text>",
        },
    ],
    "video": [
        {
            "name": "ffmpeg + whisper",
            "what": "cut/convert video and auto subtitles",
            "install": "winget install Gyan.FFmpeg  |  brew install ffmpeg  |  apt install ffmpeg",
        },
    ],
    "humanize": [
        {
            "name": "humanizer skill + writing_check",
            "what": "rewrite to a human voice, then verify",
            "install": "humanizer is a Claude Code skill; verify with the study writing_check tool",
        },
    ],
}


def toolkit_groups() -> list[str]:
    return list(_TOOLKIT)


def toolkit(topic: str = "") -> str:
    key = topic.strip().lower()
    if key and key not in _TOOLKIT:
        return f"Unknown toolkit group '{topic}'. Available: {', '.join(_TOOLKIT)}"
    groups = {key: _TOOLKIT[key]} if key else _TOOLKIT
    out = [
        "# Study toolkit (ecosystem)",
        "",
        "Run scripts/setup.py to install and configure these automatically. Keys are optional and "
        "live in a gitignored .env; the MCP never stores secrets.",
        "",
    ]
    for name, items in groups.items():
        out.append(f"## {name}")
        for item in items:
            out.append(f"- {item['name']}: {item['what']}")
            if item.get("install"):
                out.append(f"  install: {item['install']}")
            if item.get("get_key"):
                out.append(f"  key: {item['get_key']}")
            if item.get("configure"):
                out.append(f"  configure: {item['configure']}")
        out.append("")
    return "\n".join(out).strip()
