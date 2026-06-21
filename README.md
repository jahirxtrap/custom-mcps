# custom-mcps

A personal collection of **standalone MCP servers** for Claude Code. Each one runs
on its own over **stdio** and is registered once at user scope, so every Claude Code
client — the CLI, the desktop app, the web app, or any host that loads user MCP
servers — can reach it. Nothing stays running: there's no app and no service, the
client launches a server on demand and tears it down when the turn is done.

```
[Any Claude Code client] ──stdio──> [a custom-mcps server, on demand]
```

It's a [uv](https://docs.astral.sh/uv/) workspace — shared libraries in `packages/`,
servers in `servers/` — so adding a server is a single new folder.

## Servers

| Server | What it does |
|---|---|
| **pixelart** | Draw, inspect and verify pixel art by data — any size, no project assumptions. |
| **sfx** | Synthesize sound effects (`.ogg`) by data — any kind, no project assumptions. |
| **modkit** | Inspect and validate multiloader mod workspaces (read-only). Domain-specific. |
| **i18n** | Keep translation locales in sync, complete and consistent (read-only). |
| **devkit** | Your development conventions plus checks (commits, hardcoded tokens, DRY). |
| **study** | Academic study work by data: anti-AI writing checks, APA citations, concept maps, multi-area workspaces. |

`pixelart`, `sfx`, `i18n` and `study` are agnostic; `modkit` (multiloader mod dev) and `devkit`
(your conventions) are personal/domain-specific. All are registered the same way.

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

It's **agnostic by design** — 8×8, 16×16, 32×32, 64×64, with no idea what engine or
game the art is for. Tools that produce an image return both the picture and a
`path=` line, so whatever host you're in can show it.

See [`servers/pixelart`](servers/pixelart) for the full spec and tool reference, and
[`packages/pixellib`](packages/pixellib) for the underlying drawing library.

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

See [`servers/sfx`](servers/sfx) and [`packages/audiolib`](packages/audiolib).

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

See [`servers/modkit`](servers/modkit) and [`packages/loaderkit`](packages/loaderkit).

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

See [`servers/i18n`](servers/i18n) and [`packages/i18nkit`](packages/i18nkit).

## devkit

**devkit** carries **your development conventions** and the checks that verify them, across
stacks (Java, Kotlin/Compose, TS/React, GDScript, Python). The guides say what to follow; the
tools look at the real code and history. Read-only.

- **conventions** returns your rules by topic: commit, code (no comments, latest versions), dry,
  hardcoding, design (tokens), patterns (API envelope, auto-discovery, data-driven), docs, naming.
- **commit_style** / **commit_context** read the repo's git log so a new commit message matches
  the existing style and what actually changed — no Co-Authored-By.
- **find_hardcoded** flags colors (`#hex`, `Color(0xFF…)`, any stack), web `px`/`rem` values and raw
  Tailwind classes that belong in a token file (Compose `.dp` spacing is idiomatic, not flagged).
- **find_duplication** surfaces repeated blocks to unify (DRY).

The conventions were extracted from your real projects (backstube-web, cconnect, vorenth, mods).

See [`servers/devkit`](servers/devkit) and [`packages/convkit`](packages/convkit).

## study

**study** is the academic counterpart — it helps produce study and coursework **by data**, for
**any field and any language**. It distills the reusable half of an academic-work assistant into
tools, and for the parts it doesn't reimplement (documents, deep research, diagrams) it tells you
exactly what to install.

- **writing_check** is the heart: it catches "AI tells" in a draft — em dashes, filler, negative
  parallelism, the rule of three, tell-tale vocabulary, vague attributions, meta-commentary,
  chained transitions and stacked hedging — in **English and Spanish**, with a 0-100 score.
- **burstiness** measures sentence-length variation, the uniformity detectors actually penalize.
- **concept_map** renders a graphic organizer from a JSON spec, following the anti-AI visual rules
  (the title is the topic, two to four colors, no template signatures).
- **cite** formats APA 7 references and BibTeX from fields, or resolves a DOI to BibTeX.
- **study_guide** carries the writing, citation, structure and visual conventions; **toolkit** is
  the ecosystem catalog (what to install, which needs a key, how to configure it).
- **workspace_init**, **area_add**, **reference_add** and **workspace_status** scaffold a reusable,
  **multi-area** study workspace — shared conventions and memory, one folder per subject with its
  own knowledge base and reference library.

It carries **no subject knowledge** — you pick the field. `servers/study/setup.py` installs the
toolkit and writes any API keys to a gitignored `.env`; the server never stores secrets.

See [`servers/study`](servers/study) and [`packages/studykit`](packages/studykit).

## Structure

```
custom-mcps/
├── packages/
│   ├── pixellib/    # pixel-art drawing library — grid, ramps, shading, outline, preview
│   ├── audiolib/    # sound-effect synthesis library — oscillators, noise, envelopes, I/O
│   ├── loaderkit/   # multiloader-workspace library — scan, gradle.properties, loader compare, checks
│   ├── i18nkit/     # translation-health library — parse locales, diff, completeness, placeholders
│   ├── convkit/     # conventions library — guides, commit style, hardcoded/duplication checks
│   └── studykit/    # study library — writing checks, citations, concept maps, workspace
├── servers/
│   ├── pixelart/    # MCP server — draw / inspect / verify pixel art
│   ├── sfx/         # MCP server — synthesize sound effects
│   ├── modkit/      # MCP server — inspect / validate multiloader mod workspaces
│   ├── i18n/        # MCP server — keep translation locales in sync
│   ├── devkit/      # MCP server — development conventions + checks
│   └── study/       # MCP server — academic study work by data
├── scripts/         # register.py (register every server at user scope)
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
show up as `mcp__pixelart__*`:

```bash
claude mcp add pixelart -s user -- uv run --project /path/to/custom-mcps pixelart-mcp
```

Or run it straight from the repo, without a local checkout:

```bash
claude mcp add pixelart -s user -- uvx --from git+https://github.com/jahirxtrap/custom-mcps pixelart-mcp
```

Or register **every** server in the workspace at once — it discovers each one under
`servers/` and adds it at user scope:

```bash
uv run python scripts/register.py
```

## Add a server

Drop a folder under `servers/<name>/` with its own `pyproject.toml` and a
`FastMCP` instance exposing `main()`, reuse `pixellib` (or add a package under
`packages/`), run `uv sync`, and register it. The contributor guide lives in
[CLAUDE.md](CLAUDE.md).

## License

MIT — see [LICENSE](LICENSE).
