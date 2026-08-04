"""Embedded study guides and the ecosystem toolkit catalog."""
from __future__ import annotations

from .assets import (
    CITATION_APA,
    DOCUMENTS_GUIDE,
    IMAGES_GUIDE,
    SLIDES_GUIDE,
    STRUCTURE_GUIDE,
    VISUAL_GUIDE,
    WRITING_RULES,
)

_GUIDES = {
    "writing": WRITING_RULES,
    "citations": CITATION_APA,
    "structure": STRUCTURE_GUIDE,
    "visual": VISUAL_GUIDE,
    "images": IMAGES_GUIDE,
    "slides": SLIDES_GUIDE,
    "documents": DOCUMENTS_GUIDE,
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
    "image": "images",
    "photo": "images",
    "photos": "images",
    "picture": "images",
    "figures": "images",
    "slide": "slides",
    "presentation": "slides",
    "presentations": "slides",
    "marp": "slides",
    "deck": "slides",
    "powerpoint": "slides",
    "pptx": "slides",
    "document": "documents",
    "docx": "documents",
    "word": "documents",
    "report": "documents",
    "pdf": "documents",
    "reportlab": "documents",
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
            "name": "ReportLab (render_document tool)",
            "what": "the professional, technical engine: designed PDFs with fine tables, vector charts, "
            "navigable outline, page numbering; already installed with this server",
            "install": "bundled (studykit dependency); nothing to install",
            "configure": "ask the user which engine fits before building: pandoc (.docx + automatic "
            "citations), LaTeX (strict APA), or ReportLab (designed PDF). It does not read BibTeX/CSL",
        },
        {
            "name": "Anthropic document skills (docx, pptx, xlsx, pdf)",
            "what": "create and read Office documents and PDFs",
            "install": "enable the document skills in Claude Code (see docs.claude.com skills)",
        },
    ],
    "slides": [
        {
            "name": "ReportLab (render_document tool, format='slides')",
            "what": "the technical deck: 16:9, vector charts, reveal builds, progress bar, matching the "
            "report palette; already installed with this server",
            "install": "bundled (studykit dependency); nothing to install",
            "configure": "ask the user first: a visual deck (Marp) or a precisely typeset one (ReportLab)",
        },
        {
            "name": "Marp (marp-cli)",
            "what": "styled slide decks from Markdown (headless Chromium); export PDF (recommended) or PPTX",
            "install": "npm i -g @marp-team/marp-cli  (workspace: setup.py installs it locally by default)",
            "configure": "marp-cli bundles no browser: export CHROME_PATH first (setup.py records it "
            "in the workspace .env) or PDF export hangs. Then recommend PDF; marp deck.md --pdf -o "
            "deck.pdf | --pptx gives image slides | add --pptx-editable for editable text "
            "(needs LibreOffice, experimental)",
        },
        {
            "name": "LibreOffice (soffice)",
            "what": "only for Marp editable PPTX (--pptx-editable); converts the rendered deck to editable shapes",
            "install": "winget install TheDocumentFoundation.LibreOffice  |  brew install libreoffice  |  "
            "apt install libreoffice  (setup.py --all installs it)",
            "configure": "if soffice is not on PATH after install, set SOFFICE_PATH to the soffice binary",
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
            "install": "claude mcp add semantic-scholar -s user -- uvx semantic-scholar-mcp",
            "get_key": "optional; request a key at https://www.semanticscholar.org/product/api to raise rate limits",
            "configure": "add -e SEMANTIC_SCHOLAR_API_KEY=... before the -- (the key lives in .env)",
        },
    ],
    "citations": [
        {
            "name": "pandoc + citeproc",
            "what": "format citations and convert Markdown to docx/pdf; --citeproc needs pandoc 2.11+ "
            "(older distro builds expect the removed pandoc-citeproc filter and fail)",
            "install": "winget install JohnMacFarlane.Pandoc  |  brew install pandoc  |  "
            "apt install pandoc (often too old; setup.py drops the official build in ~/.local/bin)",
            "configure": "check `pandoc --version` first, then: pandoc essay.md --citeproc "
            "--bibliography=references.bib --csl=styles/apa.csl -o essay.docx",
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
            "install": "setup.py --latex (no root) ; or https://yihui.org/tinytex/ then "
            "tlmgr install apa7 biblatex-apa",
        },
    ],
    "images": [
        {
            "name": "Wikimedia Commons",
            "what": "search free public-domain and Creative Commons images (no key, no install)",
            "install": "search https://commons.wikimedia.org/w/index.php?search=<q>&title=Special:MediaSearch&type=image",
            "configure": "check the license (PD/CC0 free; CC BY/BY-SA need credit) and take the full-resolution file",
        },
        {
            "name": "Openverse",
            "what": "aggregated CC and public-domain image search (no key)",
            "install": "search https://openverse.org/search?q=<q>  (API https://api.openverse.org/v1/images/?q=<q>)",
        },
        {
            "name": "Google Images (reusable)",
            "what": "web image search filtered to reusable licenses",
            "install": "search https://www.google.com/search?tbm=isch&tbs=il:cl&q=<q>",
        },
        {
            "name": "Pollinations",
            "what": "free text-to-image AI, no key, no GPU; use only when the user explicitly asks to generate/use AI",
            "install": "GET https://image.pollinations.ai/prompt/<text>",
        },
    ],
    "video": [
        {
            "name": "ffmpeg + whisper",
            "what": "cut/convert video and auto subtitles",
            "install": "winget install Gyan.FFmpeg  |  brew install ffmpeg  |  apt install ffmpeg",
        },
        {
            "name": "video-audio MCP",
            "what": "30+ video/audio editing tools over ffmpeg, by natural language",
            "install": "git clone https://github.com/misbahsy/video-audio-mcp ; cd video-audio-mcp ; uv sync",
            "configure": "claude mcp add video-audio -- uv run --directory <clone> server.py",
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
        "servers/study/setup.py installs the automatable items (basics by default, everything with --all; "
        "skills via 'claude plugin install'). Web services (Pollinations) and proprietary skills are "
        "documented here, not auto-installed. Keys are optional and live in a gitignored .env.",
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
