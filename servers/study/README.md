# study

An **area-agnostic, language-agnostic** MCP server for academic and study work. It distills the
reusable half of an academic-work assistant into tools: catch "AI tells" in writing, check spelling
and grammar through a local LanguageTool, format citations, render concept maps by data, typeset
professional PDFs and decks, source images from
free licensed providers, and scaffold a multi-area study **workspace**. It carries no subject
knowledge; you choose the field. For what it doesn't reimplement (Word, deep research, diagrams),
the `toolkit` tool tells you exactly what to install.

## Tools

| Tool | Args | What it does |
|---|---|---|
| `writing_check` | `text` | Detect AI tells (EN+ES): em dashes, filler, negative parallelism, rule of three, tell-tale vocabulary, vague attributions, meta-commentary, chained transitions, stacked hedging. Score + hits by category. |
| `burstiness` | `text` | Sentence-length variation (detectors penalize uniformity): mean, stdev, coefficient of variation, score. Language-agnostic. |
| `grammar_check` | `text`, `language` | Spelling and grammar through a local LanguageTool (30+ languages; `auto` detects). Markdown and pandoc markup is removed first; every finding points to the original line with the flagged text, message, replacements, rule and category, plus counts by category. Once over the finished text; names and technical terms flagged as spelling are the author's call. Needs LanguageTool (see `toolkit('grammar')`). |
| `study_guide` | `topic=""` | Embedded guidance: `writing` / `citations` / `structure` / `visual` / `images` / `slides` / `documents`. |
| `concept_map` | `spec`, `out_dir=""` | Concept map / organizer from a JSON spec to a PNG (returns the image + `path=`), following the anti-AI visual rules. |
| `render_document` | `spec`, `out_dir=""` | Typeset a professional PDF with ReportLab: `format='report'` (cover, outline, tables, vector charts, two columns, page numbers) or `format='slides'` (16:9, reveal builds, progress bar). |
| `cite` | `fields=""`, `doi=""` | APA 7 reference + in-text + BibTeX from fields, or resolve a DOI to BibTeX (network). |
| `image_search` | `subject`, `kind=""` | Brief for sourcing a real image from free, openly licensed providers (Wikimedia Commons, Openverse, Google reusable, Flickr): search/API URLs + licensing checklist; AI only when explicitly asked. |
| `toolkit` | `topic=""` | The ecosystem to install (documents, slides, research, citations, diagrams, latex, images, video, humanize, grammar): commands, API keys, how to configure them. |
| `workspace_init` | `path`, `areas=""` | Scaffold a multi-area study workspace (conventions, styles, memory, areas) with a generated CLAUDE.md. |
| `area_add` | `path`, `name` | Add a study area with its knowledge base and reference library. |
| `reference_add` | `path`, `area`, `fields`, `file=""` | Register a reference (BibTeX + index row, copy source, convert it to readable Markdown: pdftotext in reading order plus a cleanup of repeated headers, page numbers, broken lines and ligatures, or pandoc). |
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
├── .mcp.json             # only video-audio, when setup --all cloned it
├── puppeteer-config.json # --no-sandbox for headless mermaid (mmdc)
└── .claude/skills/        # project-scoped skills
```

The structure, folder names and conventions are **English**; the *output* (essays, diagram labels,
bibliography) is produced in the **language the user asks for**. Shared conventions, styles and
memory live at the root; each area keeps its own knowledge base and bibliography. The generated
`CLAUDE.md` tells Claude to apply the anti-AI rules, cite in APA from the area's `references.bib`,
consult its `knowledge.md`, and keep `memory/` up to date.

## Setup, keys and LanguageTool

The plugin brings three servers: `study` itself, `openalex` (open catalog of papers and citation
graph, through `@cyanheads/openalex-mcp-server`) and `semantic-scholar` (`semantic-scholar-mcp`),
both pinned to a version and started with `npx` and `uvx`. Everything they can take from you is a
plugin option, set with `claude plugin configure study@custom-mcps` or from `/plugin`:

| Option | What it is |
|---|---|
| `languagetool_url` | A LanguageTool server you keep running, for `grammar_check` (sub-second checks). |
| `languagetool_home` | The unzipped LanguageTool folder, used when no server is set (one JVM start per check; Java 17+ on PATH). |
| `openalex_mailto` | Email sent to OpenAlex as `mailto=` (its polite pool). |
| `openalex_key` | Free OpenAlex account key, raises the rate limits (stored in the secure store). |
| `semantic_scholar_key` | Optional Semantic Scholar key, raises the rate limits (secure store). |

All of them are optional: without a LanguageTool location `grammar_check` answers that it is not
available and points to `toolkit('grammar')`; without keys the research servers run on their
anonymous limits. `openalex` needs Node 24 or later (its own requirement), `semantic-scholar` needs
`uv`. The first start of each downloads its package, which can take longer than the 30 s Claude Code
waits for a server; `setup.py` starts them once so they are cached before the first session. A standalone registration takes the same values as `LANGUAGETOOL_URL`,
`LANGUAGETOOL_HOME`, `OPENALEX_MAILTO`, `OPENALEX_API_KEY` and `SEMANTIC_SCHOLAR_API_KEY` in the
environment. The server never stores secrets.

The `toolkit` tool is the catalog of everything else; `servers/study/setup.py` is its executable
form. `servers/study/setup.py --workspace <dir> [--all] [--mermaid] [--skills-from <dir>]` keeps
that inside one workspace, and registers no server there: the plugin provides them, so the workspace
works the same however the server is installed. **Basics** write `.env` (CHROME_PATH for Marp),
`TOOLKIT.md`, `puppeteer-config.json`, download `styles/apa.csl`, create `.claude/skills/`, and
install `markmap` locally. **`--all`** also clones the `video-audio` MCP into `tools/`, installs
`mermaid` + `Marp` locally, installs the system CLIs (pandoc, ffmpeg, graphviz, LibreOffice for
editable PPTX), and installs skill
plugins via `claude plugin install` (deep-research via superpowers). Plugin skills install at user
scope and apply everywhere; `--skills-from` copies your own skill folders in for a portable bundle.

## Choosing an engine

There is no default. Before building a document or a deck, the server's guidance tells Claude to
**ask** which engine fits:

| Deliverable | Engine |
|---|---|
| Editable `.docx`, automatic APA citations from `.bib` | pandoc |
| Strict APA 7 paper or thesis | LaTeX (TinyTeX + apa7) |
| Designed PDF: report, dossier, data-driven document | `render_document` (ReportLab) |
| Visual deck, or PPTX / HTML output | Marp |
| Technical deck: vector charts, reveal builds, exact layout | `render_document` (ReportLab) |

ReportLab ships with the server (it is a `studykit` dependency, ~7 MB of pure Python) and needs no
system install: no LaTeX, no Chromium. It does **not** read BibTeX or process CSL — build the
reference strings with `cite` or pandoc first, then pass them in.

## Output contract

`concept_map` returns a standard image block plus a `path=<abs> mime=image/png size=NxN` line.
`render_document` writes a PDF and returns JSON with its path, format and page count. The server
stays UI-agnostic; rendering the artifact to a user is the host agent's job.

See [`src/studykit`](src/studykit) for the underlying library.

## Install as a Claude Code plugin

```
/plugin install study --marketplace jahirxtrap/custom-mcps
```

The plugin runs the copy Claude Code installed, with `uv run` (it needs [uv](https://docs.astral.sh/uv/)), and stays on that version until you update the plugin. It also starts the `openalex` and `semantic-scholar` research servers (pinned versions, through `npx` and `uvx`), and its options hold the keys and the LanguageTool location (see above). Its optional toolkit setup is still its own step. To register it on its own for any MCP client instead, see the [root README](../../README.md#use-it-from-claude-code).
