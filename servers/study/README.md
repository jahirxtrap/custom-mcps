# study

An **area-agnostic, language-agnostic** MCP server for academic and study work. It distills the
reusable half of an academic-work assistant into tools: catch "AI tells" in writing, format
citations, render concept maps by data, and scaffold a multi-area study **workspace**. It carries
no subject knowledge; you choose the field. For documents, deep research, and diagrams it doesn't
reimplement, the `toolkit` tool tells you exactly what to install.

## Tools

| Tool | Args | What it does |
|---|---|---|
| `writing_check` | `text` | Detect AI tells (EN+ES): em dashes, filler, negative parallelism, rule of three, tell-tale vocabulary, vague attributions, meta-commentary, chained transitions, stacked hedging. Score + hits by category. |
| `burstiness` | `text` | Sentence-length variation (detectors penalize uniformity): mean, stdev, coefficient of variation, score. Language-agnostic. |
| `study_guide` | `topic=""` | Embedded guidance: `writing` / `citations` / `structure` / `visual`. |
| `concept_map` | `spec`, `out_dir=""` | Concept map / organizer from a JSON spec to a PNG (returns the image + `path=`), following the anti-AI visual rules. |
| `cite` | `fields=""`, `doi=""` | APA 7 reference + in-text + BibTeX from fields, or resolve a DOI to BibTeX (network). |
| `toolkit` | `topic=""` | The ecosystem to install (documents, research, citations, diagrams, latex, images, video): commands, API keys, how to configure them. |
| `workspace_init` | `path`, `areas=""` | Scaffold a multi-area study workspace (conventions, styles, memory, areas) with a generated CLAUDE.md. |
| `area_add` | `path`, `name` | Add a study area with its knowledge base and reference library. |
| `reference_add` | `path`, `area`, `fields`, `file=""` | Register a reference (BibTeX + index row, copy source, convert it to Markdown via pdftotext/pandoc). |
| `workspace_status` | `path` | Overview: areas, reference counts, stored sources. |

## The workspace

`workspace_init` builds a reusable, **multi-area** study space (a student can carry several
subjects at once):

```
<workspace>/
├── CLAUDE.md              # how to work here: anti-AI, APA, consult the area, keep memory
├── conventions/          # writing-rules.md (anti-AI) + citation-apa.md
├── styles/apa.csl        # APA style for pandoc (downloaded by setup)
├── templates/            # paper-apa7.tex, concept-map-example.json
├── memory/               # profile.md, log.md
├── areas/<area>/         # knowledge.md, references.bib, library/{INDEX.md,sources/,md/}
├── tools/video-audio-mcp # ffmpeg-based editing MCP, cloned by setup --all
├── .mcp.json             # study + openalex + semantic-scholar (+ video-audio)
├── puppeteer-config.json # --no-sandbox for headless mermaid (mmdc)
└── .claude/skills/        # project-scoped skills
```

The structure, folder names and conventions are **English**; the *output* (essays, diagram labels,
bibliography) is produced in the **language the user asks for**. Shared conventions, styles and
memory live at the root; each area keeps its own knowledge base and bibliography. The generated
`CLAUDE.md` tells Claude to apply the anti-AI rules, cite in APA from the area's `references.bib`,
consult its `knowledge.md`, and keep `memory/` up to date.

## Setup and API keys

The `toolkit` tool is the catalog; `servers/study/setup.py` is its executable form: it installs
what it can, registers the external MCPs (OpenAlex, Semantic Scholar), and writes any keys to a
**gitignored `.env`**. Most tools need no key (OpenAlex is free; Semantic Scholar works without
one), so it only asks when a key would raise your limits. The server never stores secrets.

`servers/study/setup.py --workspace <dir> [--all] [--mermaid] [--skills-from <dir>]` keeps
everything inside one workspace. **Basics** write `.env`, `.mcp.json` (study + openalex + semantic-scholar),
`TOOLKIT.md`, `puppeteer-config.json`, download `styles/apa.csl`, create `.claude/skills/`, and
install `markmap` locally. **`--all`** also clones the `video-audio` MCP into `tools/`, installs
`mermaid` + `Marp` locally, installs the system CLIs (pandoc, ffmpeg, graphviz), and installs skill
plugins via `claude plugin install` (deep-research via superpowers). Plugin skills install at user
scope and apply everywhere; `--skills-from` copies your own skill folders in for a portable bundle.

## Output contract

`concept_map` returns a standard image block plus a `path=<abs> mime=image/png size=NxN` line.
The server stays UI-agnostic; rendering the image to a user is the host agent's job.

See [`packages/studykit`](../../packages/studykit) for the underlying library.
