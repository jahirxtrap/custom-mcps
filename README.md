# custom-mcps

A personal collection of **standalone MCP servers** for Claude Code. Each one runs
on its own over **stdio** and is registered once at user scope, so every Claude Code
client — the CLI, the desktop app, the web app, or any host that loads user MCP
servers — can reach it. Nothing stays running: there's no app and no service, the
client launches a server on demand and tears it down when the turn is done.

```
[Any Claude Code client] ──stdio──> [a custom-mcps server, on demand]
```

It's a [uv](https://docs.astral.sh/uv/) workspace of servers in `servers/`, each folder carrying
its own library, so a server and its plugin are a single folder.

It's also a Claude Code **plugin marketplace**: every server installs as a plugin in one step
(see [Install as a Claude Code plugin](#install-as-a-claude-code-plugin)), while it stays a
standalone server any MCP client can register.

## Servers

| Server | What it does |
|---|---|
| **pixelart** | Draw, inspect and verify pixel art by data — any size, no project assumptions. |
| **sfx** | Synthesize sound effects (`.ogg`) by data — any kind, no project assumptions. |
| **modkit** | Inspect and validate multiloader mod workspaces (read-only). Domain-specific. |
| **i18n** | Keep translation locales in sync, complete and consistent (read-only). |
| **devkit** | Your development conventions plus checks (commits, hardcoded tokens, DRY, comments), and a notice when an edit adds comments. |
| **study** | Academic study work by data: anti-AI writing checks, grammar check through LanguageTool, editable Word and PowerPoint on the institution's template, APA citations, concept maps, typeset PDFs and decks, free-image sourcing, multi-area workspaces. |
| **buildkit** | Design low-poly 3D structures by data: principles, references, spec, iso/silhouette preview, Godot def. |
| **uikit** | Interface design measured against WCAG: tokens, the color pairs the code really uses, contrast, and a mockup checked against the app's own design. |

`pixelart`, `sfx`, `i18n`, `study`, `buildkit` and `uikit` are agnostic; `modkit` (multiloader mod
dev) and `devkit` (conventions and their checks) are domain-specific. All are registered the same way.

## pixelart

**pixelart** treats pixel art as something you build by **data, not by eye**. You
describe a sprite — a silhouette, a color ramp, a light direction — and it renders
the native PNG plus an upscaled, checkerboard **preview you can actually read**,
instead of squinting at a 16-pixel thumbnail.

- **render_sprite** is the heart of it: a declarative JSON spec — silhouette, then
  shading from a consistent top-left light, then a 1px outline, then optional
  symmetry — becomes a finished sprite in one call.
- **from_grid** and **to_grid** move between an explicit pixel matrix and a PNG, so
  you can read a reference, hand-place pixels, or edit an existing sprite as data.
- **preview** upscales any PNG with nearest-neighbor on a checkerboard — it never
  blurs — to judge how a sprite is coming along.
- **palette** extracts and budget-checks a sprite's colors, or generates a
  hue-shifted ramp (art, skin, hair, or neutral grayscale) from a single base color.
- **check** flags the usual mistakes: anti-aliasing, content touching the canvas
  edge, floating pixels, and going over the per-size color budget.
- **pixel_guide** carries the pixel-art principles with it, so the server is
  self-contained; for reference-driven design and animation it points to the complementary
  [pixel-art-sprites](https://github.com/omer-metin/skills-for-antigravity) skill.
- **search_reference** builds a reference brief before you draw — targeted search queries (real
  photos and similar pixel arts), what to extract (silhouette, palette, light) and how to translate
  it to pixels. It doesn't fetch; the host agent runs the queries with its own web tools.

It's **agnostic by design** — 8×8, 16×16, 32×32, 64×64, with no idea what engine or
game the art is for. Tools that produce an image return both the picture and a
`path=` line, so whatever host you're in can show it.

See [`servers/pixelart`](servers/pixelart) for the full spec and tool reference, and
[`servers/pixelart/src/pixellib`](servers/pixelart/src/pixellib) for the underlying drawing library.

## sfx

**sfx** synthesizes sound effects the same way — by **data, not by hand**. You describe a
sound as layers (a sweep, a tone, a burst of noise) with envelopes, and it renders the
`.ogg` plus a **waveform image** so you can verify it at a glance (I can't hear, so I look).

- **synth_sfx** is the heart: a declarative JSON spec — oscillators, sweeps, noise, FM,
  envelopes, and shaping like bitcrush — becomes a finished effect in one call.
- **waveform** draws any audio file's wave so its attack, body and tail are visible.
- **encode** converts between formats, and **inspect** reports peak, RMS, clipping and duration.
- **sfx_guide** carries general SFX-design principles (anatomy, techniques by intent), so the
  server is self-contained.

The same spec makes anything — a coin, a laser, an explosion, a jump, a UI click. Output is
configurable (format, sample rate, channels, normalization) with sane defaults (peak 0.9,
ogg, 44100, mono). It prefers **ffmpeg** when available and falls back to **soundfile**, so
it always works.

See [`servers/sfx`](servers/sfx) and [`servers/sfx/src/audiolib`](servers/sfx/src/audiolib).

## modkit

**modkit** is the odd one out — **domain-specific** rather than agnostic. It helps with
**multiloader mod workspaces**: the mechanical, repetitive half of mod-dev that complements
`minecraft-dev` (which handles API/decompile). It scans by the `<modid>-<version>-multi`
folder convention and **never hardcodes a mod name**, so it works on any such workspace. All
tools are read-only.

- **list_mods** inventories every mod and its version folders, flagging the most recent.
- **loader_sync** compares the loaders' Java and reports same-path files that differ — to spot
  "ported the fix to fabric but a loader kept the old copy" (entrypoints differ by design).
- **mod_info** reads `gradle.properties` and the Java version expected for that MC version.
- **check_structure** / **check_json** / **check_access** validate conventions (common has no
  Java, repositories only in root, JSON byte rules, mixins.json parity, AW/AT parity + header).
- **find_symbol** locates an API across all loaders — handy when migrating versions.
- **decompile_guide** carries the strategy for reading the MC/loader API with `minecraft-dev` and
  `mcmodding-mcp` — per-loader decompile jars and merge steps (including the NeoForge sources-jar
  step), vanilla source, and migration references (primers, misode, mcasset). It points; it never
  decompiles itself.

See [`servers/modkit`](servers/modkit) and [`servers/modkit/src/loaderkit`](servers/modkit/src/loaderkit).

## i18n

**i18n** keeps your translations healthy — in sync, complete and consistent. It works on
JSON locales, **flat** (Minecraft `lang/*.json`) or **nested** (`react-i18next`), flattening
nested objects to dot-paths so both compare the same way. Read-only.

- **locale_diff** reports, per locale, which keys are missing vs the base and which are extra —
  the "every key in one must exist in the others" check.
- **completeness** gives the translated percentage per locale.
- **check_format** flags placeholders (`{name}`, `%s`) that differ between a key's translations,
  and empty values.
- **find_unused** crosses keys with the code: used-but-undefined (broken) and defined-but-unused
  (dead), with configurable `t()`/`tr()` patterns.
- **i18n_guide** carries the conventions (no hardcoded strings, locales in sync, key naming).

See [`servers/i18n`](servers/i18n) and [`servers/i18n/src/i18nkit`](servers/i18n/src/i18nkit).

## devkit

**devkit** carries **your development conventions** and the checks that verify them, across
stacks (Java, Kotlin/Compose, TS/React, GDScript, Python). The guides say what to follow; the
tools look at the real code and history. Read-only.

- **conventions** returns your rules by topic: commit, code (no comments, latest versions), dry,
  hardcoding, design (tokens), spacing (one spacing + type scale, symmetry), format (imports,
  indentation, JSON style), patterns, docs, naming. Without a topic it answers the index, and a
  misspelt topic gets the closest name, never the whole guide.
- The **core rules** (code, commit, ssot, dry) reach every session on their own: a `SessionStart`
  hook prints them when the session starts, resumes or compacts, so they survive compaction
  without being asked for again.
- **commit_style** reads the repo's git log so a new commit message matches the existing style —
  no Co-Authored-By.
- **find_hardcoded** flags colors (`#hex`, `Color(0xFF…)`, any stack), web `px`/`rem` values and raw
  Tailwind classes that belong in a token file (Compose `.dp` spacing is idiomatic, not flagged).
- **find_inconsistent** snapshots the spacing and text-size scales actually in use and flags what
  breaks consistency: rare one-off values, spacing off a base grid, and Tailwind arbitrary `[Npx]`.
- **find_format** catches AI-typical format breaks formatters miss: inline fully-qualified class
  names (import them), unused imports, tab/space mixed indentation, and JSON indent-style outliers.
- **find_duplication** surfaces repeated blocks to unify (DRY): occurrences per file and the
  largest blocks, with a `detail` switch for the full list. **find_format** cuts its lists the same
  way and keeps every count complete.
- **find_comments** finds what the no-comments rule forbids: every comment line or block, directives
  excepted, and the docstrings that run over one line or 100 characters, only repeat the name they
  describe or carry rationale. Python is read with its tokenizer and ast; `//`, `/* */`, `<!-- -->`, `--` and `#`
  families by line. The same detector runs from a `PostToolUse` hook after every `Edit` or `Write`:
  when the edit introduced comments it answers with the lines and the rule, otherwise it stays silent.

The conventions were extracted from your real projects (backstube-web, cconnect, vorenth, mods).

See [`servers/devkit`](servers/devkit) and [`servers/devkit/src/convkit`](servers/devkit/src/convkit).

## study

**study** is the academic counterpart — it helps produce study and coursework **by data**, for
**any field and any language**. It distills the reusable half of an academic-work assistant into
tools, and for the parts it doesn't reimplement (documents, slides, deep research, diagrams) it
tells you exactly what to install.

- **writing_check** is the heart: it catches "AI tells" in a draft — em dashes, filler, negative
  parallelism, the rule of three, tell-tale vocabulary, vague attributions, meta-commentary,
  chained transitions and stacked hedging — in **English and Spanish**, with a 0-100 score.
- **burstiness** measures sentence-length variation, the uniformity detectors actually penalize.
- **grammar_check** runs a local [LanguageTool](https://languagetool.org) (open source, 30+
  languages) over the finished text and returns every finding with its line, message, replacements
  and category. It judges nothing: names and technical terms flagged as spelling stay the author's
  call. The three checks run once over the whole text, never paragraph by paragraph.
- **concept_map** renders a graphic organizer from a JSON spec, following the anti-AI visual rules
  (the title is the topic, two to four colors, no template signatures).
- **cite** formats APA 7 references and BibTeX from fields, or resolves a DOI to BibTeX.
- **check_links** opens every URL of a reference list, a `.bib` or a work folder before delivery and
  reports the ones that do not answer, with their status, where they appear and the latest Internet
  Archive copy as the URL to cite instead. A dead link is the most common way a real source reads as
  an invented one.
- **render_document** builds the deliverable from a spec. **docx**: editable Word on the
  institution's own template — its cover, logos, headers, styles and margins stay, the cover texts
  are replaced, the content follows with its styles (or a clean Word file from scratch). **pptx**:
  editable PowerPoint on a template's layouts and master. **report** and **slides**: ReportLab PDFs
  (navigable outline, fine tables, vector charts, two columns; a 16:9 deck with reveal builds). No
  LaTeX, no Chromium, no Office — it all ships with the server. **template_inspect** reads a
  template first and says what to replace and which layouts exist. **final_check** runs the three
  text checks in one call over the finished text.
- **image_search** briefs where to source a real image from free, openly licensed providers
  (Wikimedia Commons, Openverse, Google reusable, Flickr) with a licensing checklist, and generates
  with AI only when you explicitly ask.
- **study_guide** carries the writing, citation, structure, visual, images, slides, documents and
  assignment conventions: how to read a brief that arrives as a photo and confirm it, and the rule
  to **ask what the institution expects** before building (Word on its template, pandoc for prose
  with automatic citations, LaTeX for strict APA, ReportLab for a designed PDF, PowerPoint on its
  template or Marp for a deck); **toolkit** is the ecosystem catalog (what to install, which needs a
  key, how to configure it).
- **workspace_init**, **area_add**, **reference_add** and **workspace_status** scaffold a reusable,
  **multi-area** study workspace — shared conventions, templates, tools and memory, one folder per
  subject with its own knowledge base, reference library, one folder per work and an `out/` for
  the final files. `workspace_status` reports what is really there: works, scripts, deliverables,
  templates, shared tools and work files by status. A PDF added as a source is converted in
  reading order and cleaned of repeated headers, page numbers, broken lines and ligatures before
  it reaches the library.

It carries **no subject knowledge** — you pick the field. The plugin also brings the **OpenAlex**
and **Semantic Scholar** research servers, pinned to a version, and its options
(`claude plugin configure study@custom-mcps`) hold the optional keys and where LanguageTool is;
`servers/study/setup.py` installs the rest of the toolkit. The server never stores secrets.

See [`servers/study`](servers/study) and [`servers/study/src/studykit`](servers/study/src/studykit).

## buildkit

**buildkit** is the 3D counterpart of `pixelart` — it designs **low-poly 3D structures by data**
(buildings, houses, walls, trees, props). Same loop: gather references, follow the principles, define
the structure by spec, **preview** it, **check** it. Free and self-contained (Pillow + NumPy, **no GPU,
no paid services**); it doesn't sculpt detailed/organic art and doesn't do a final render — the engine
does that.

- **design_guide** carries the principles: blockout first, the silhouette readability gate, real-world
  proportion/scale, composition, limited palette, directional light, consistency.
- **search_reference** builds a reference brief (queries incl. plans/elevations, what to extract, how
  to translate) — it points; the host agent runs the queries with its own web tools.
- **render_preview** projects the spec to an **isometric flat-shaded** image, or a **silhouette** for
  the readability test — a software painter's renderer, deterministic, headless.
- **check** validates proportion/scale, door fit and palette size.
- **godot_def** emits a Godot-ready def — for a building it matches the keys of a runtime builder
  (`size`, `height`, `roof_height`, `wall_color`, `door`), otherwise a primitives def + a GDScript builder.

It fits a procedural Godot pipeline (spec `def` → primitives), the same shape as a project's own
`house_builder`. See [`servers/buildkit`](servers/buildkit) and [`servers/buildkit/src/formkit`](servers/buildkit/src/formkit).

## uikit

**uikit** is interface design **measured, not argued**. It reads a theme's design tokens, works out
which colors the code really puts together, checks those pairs against WCAG, and measures a mockup
against the design the app's code really uses. Framework-agnostic, dependency-free and read-only.

The contrast maths is four lines; the reason this exists is the other half. A report is only worth
reading when the pairs in it are the ones the interface actually draws, and those are written in the
code, not in a table somebody typed. So the pairs come from three places: the **naming** (a token
called `on-surface` says where it belongs), a **variant map** (in a `tva`/`cva` block, the variant
that styles a surface and the one that styles its text), and **classes used together** in the same
attribute.

- **read_tokens** reads the three shapes a theme ships in: a source object (`light: {...}` /
  `dark: {...}`), a theme JSON (a `colors` map, as a pack carries it) and CSS custom properties.
  Colors may be `#hex`, `rgb()`, `hsl()`, `oklch()` or `oklab()`.
- **find_pairs** reports which pairs are in play and **how each one was found**, with file and line.
- **check_contrast** measures every pair of every theme: 4.5:1 for text, 3:1 for large text and for
  anything that reads as a border. A translucent token is composited onto what sits behind it, so a
  `#ffffff0d` hover is measured as the eye sees it; decorative tokens (logo, shadow, scrollbar) are
  skipped, because a brand mark owes no ratio.
- **design_guide** carries the usability heuristics, the psychology laws each from its primary
  source, the thresholds behind the numbers (WCAG 2.2, Material) and, under `mockup`, the procedure
  for a mockup: ask the user first and wait, discover the app's design by reading and counting, build
  with its values, deliver one HTML file, measure it. The server's instructions carry the rule: a new
  screen, a new panel or a redesign that touches more than one component starts by asking whether to
  make a mockup, because a mockup takes time; a change to a single control needs none.
- **check_mockup** is that measurement. It knows no app: it reads what the code says about its own
  look (CSS, Tailwind classes on their default scale, Compose `dp`/`sp`, theme JSON, the font and icon
  packages among the dependencies) and lists every color, CSS variable, font family, length (spacing,
  size, type, radius), shadow and icon library the mockup uses that the app never does, each with the
  closest value the app does use. Layout offsets over 200 px, pill radii, black and white at any
  opacity and the fallbacks of a font stack are not reported. It judges nothing.
- **review_context** gathers the evidence for the four heuristics that leave a trace in the code
  (a mutation with no loading state, a delete with no confirmation, an exception rendered raw,
  copy outside i18n) and stops there — the tool supplies the evidence, the reviewer the judgement,
  the same split `commit_context` makes. The other six are a read, not a measurement.
- **contrast** is the one-off: two colors in, the ratio and the AA/AAA verdicts out.

See [`servers/uikit`](servers/uikit) and [`servers/uikit/src/tokenkit`](servers/uikit/src/tokenkit).

## Structure

```
custom-mcps/
├── .claude-plugin/  # marketplace.json (every server as a Claude Code plugin)
├── servers/         # each one a server, its library in src/, and a plugin
│   ├── pixelart/    # draw / inspect / verify pixel art — pixellib: grid, ramps, shading, outline, preview
│   ├── sfx/         # synthesize sound effects — audiolib: oscillators, noise, envelopes, I/O
│   ├── modkit/      # inspect / validate multiloader mod workspaces — loaderkit: scan, gradle.properties, loader compare
│   ├── i18n/        # keep translation locales in sync — i18nkit: parse locales, diff, completeness, placeholders
│   ├── devkit/      # development conventions + checks — convkit: guides, commit style, hardcoded/duplication/comment checks
│   ├── study/       # academic study work by data — studykit: writing checks, citations, concept maps, PDFs, workspace
│   ├── buildkit/    # design low-poly 3D structures — formkit: spec->primitives, iso/silhouette renderer, principles
│   └── uikit/       # interface design against WCAG — tokenkit: theme readers, pair detection, WCAG contrast, mockup check
├── scripts/         # register.py (every server at user scope), pin.py (each plugin's constraints.txt)
└── tests/           # workspace test suite (pytest)
```

## Setup

```bash
uv sync             # create the venv and install every workspace member
uv run pytest       # run the test suite
```

### Per-server setup (optional)

Servers that lean on an external integration ship their own `servers/<name>/setup.py` — each is
self-contained (no server references another's) and leaves an already-present dependency alone:

```bash
uv run python servers/study/setup.py [--all]   # the full academic ecosystem (its own toolkit)
uv run python servers/sfx/setup.py             # ffmpeg (optional; soundfile fallback otherwise)
uv run python servers/pixelart/setup.py        # the complementary pixel-art-sprites skill
uv run python servers/modkit/setup.py          # register the minecraft-dev MCP (decompiling)
```

## Use it from Claude Code

Register a server once at user scope and it's available in every session — the tools
show up as `mcp__pixelart__*`. Run `uv sync` once first, then register with `--no-sync` so each
launch skips re-syncing (fast, stable startup — no rebuild-on-launch stalls):

```bash
claude mcp add pixelart -s user -- uv run --no-sync --project /path/to/custom-mcps pixelart-mcp
```

Or run it straight from the repo, without a local checkout:

```bash
claude mcp add pixelart -s user -- uvx --from "git+https://github.com/jahirxtrap/custom-mcps#subdirectory=servers/pixelart" pixelart-mcp
```

Or register **every** server in the workspace at once — it discovers each one under
`servers/` and adds it at user scope. It registers the **installed venv entry point** directly
(`.venv/Scripts/<name>-mcp`), so launch is just the server process — no `uv` resolve/sync on every
start, which is what keeps startup fast and avoids stalls:

```bash
uv sync                              # once, so the venv entry points exist
uv run python scripts/register.py
```

## Install as a Claude Code plugin

Every server is also a plugin in this repository's marketplace (`custom-mcps`), so it installs
in one step, with no checkout and no `claude mcp add`:

```
/plugin install devkit --marketplace jahirxtrap/custom-mcps
```

Or add the marketplace once and install the ones you want:

```bash
claude plugin marketplace add jahirxtrap/custom-mcps
claude plugin install devkit@custom-mcps
```

The plugin carries its server and runs the copy Claude Code installed, with `uv run` (it needs
[uv](https://docs.astral.sh/uv/)), so it stays on the version you installed until you update the
plugin. The first start installs the third-party packages its `constraints.txt` pins (6 to 13 s);
later ones, a new version of the plugin included, take about 2 s. Its tools show up as `mcp__plugin_devkit_devkit__*`. Use one route per server, the plugin or
`claude mcp add`, not both. The per-server setup scripts above are still their own step.

## Add a server

Drop a folder under `servers/<name>/` with its own `pyproject.toml`, a
`FastMCP` instance exposing `main()` and its library next to it in `src/`, run `uv sync` and
`scripts/pin.py`, and register it. Give it a `.claude-plugin/plugin.json`, a
`.mcp.json` and its entry in `.claude-plugin/marketplace.json` too (the test suite checks the three
agree). The contributor guide lives in [CLAUDE.md](CLAUDE.md).

## License

MIT — see [LICENSE](LICENSE).
