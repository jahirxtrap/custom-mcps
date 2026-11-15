# devkit MCP server

An MCP server that carries **development conventions** and the checks that verify them — across
stacks (Java, Kotlin/Jetpack Compose, TypeScript/React, GDScript, Python). Guides say what to
follow; tools look at the real code/history. All read-only.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`convkit`](src/convkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `conventions` | One topic of the embedded conventions: commit/code/ssot/dry/boundaries/scope/hardcoding/data/i18n/runtime/verify/design/spacing/format/patterns/docs/naming. Without a topic, the index (one line per topic); an unknown topic answers with the closest name, never with the whole guide. |
| `commit_style` | Analyze a repo's recent commit subjects (prefixes, % conventional, length, case) — the style to imitate. `path` is the repo or any folder inside it. |
| `find_hardcoded` | Hardcoded colors (`#hex`, `Color(0xFF…)`, any stack) + web `px`/`rem` values + raw Tailwind → tokens. |
| `find_inconsistent` | Snapshot the spacing and text-size scales in use; flag rare one-offs, off-grid spacing, and Tailwind arbitrary values. |
| `find_format` | AI-typical format breaks: inline fully-qualified names, unused imports, mixed tab/space indent, JSON indent outliers. Complete counts, lists of 25 (100 with `detail`). |
| `find_duplication` | Repeated normalized line blocks → DRY candidates (heuristic). Occurrences per file and the ten largest blocks; `detail` lists up to fifty with every occurrence. |

## The core rules arrive on their own

The plugin ships a `SessionStart` hook (`hooks/hooks.json`) that prints the four core topics
(code, commit, ssot, dry) into the session context when it starts, resumes or compacts. Measured
over real use, `conventions` was called hundreds of times per long session to reread those same
topics after each compaction; now they are always there, and `conventions(topic)` is for the rest.
The digest comes from the same data as the tool (`convkit.digest`), so there is one text to maintain.

## What it encodes (verified against real projects)

- **commit**: conventional, short, lowercase; never Co-Authored-By; changelog from commits.
  Issue references go in a **footer** (`Closes: #12` / `Refs: #12`), one line per issue — a
  comma-separated list closes only the first; the colon form is the one `git interpret-trailers`
  reads. Breaking changes are marked (`feat!:` or a `BREAKING CHANGE:` footer) so the derived
  changelog leads with them.
- **code**: no comments (the two exceptions are documentation as data: DB `COMMENT` and i18n
  files), one-line descriptive docstrings, English, latest stable versions, terse.
- **ssot**: one authoritative definition per fact, referenced or derived and never copied; a
  derived fact is never hand-entered; config read in one module; forms validate with the schema
  generated from the contract, never a restated constraint.
- **dry / patterns**: extract logic to reusable modules, thin routers → services, search before
  writing a helper, prefer a maintained library; endpoints return their typed model directly so the
  client and its zod schemas generate from the contract (`response_model` everywhere, readable
  `operation_id`, the generator in CI); generated code is regenerated, never authored;
  auto-discovery, data-driven content (JSON + registry).
- **boundaries**: shared code holds mechanisms, a module's exclusive capability stays with it;
  share the logic and inject the platform; each layer knows only the one below, and only the
  repository speaks SQL.
- **scope**: nothing left dangling — no system wired to nobody; preparing ground needs a real,
  named consumer; build the destination, not the legacy state.
- **hardcoding / design**: text → i18n, colors/sizes → one token file, catalogued components, no
  secrets in the repo (commit only `.example`).
- **data**: "does production need this row?" decides migration vs dev seed; reference data comes
  from a library into a migration into a table; scaffold migrations with the generator; the ORM
  reflects the DB, never the reverse.
- **i18n**: code is English and the UI language is always data; locale maps vs a scalar preference;
  pluralization is a CLDR rule (`count` → `_one`/`_other`/`_few`/`_many`), never an `if`;
  interpolate, never concatenate; format dates/numbers with `Intl`.
- **runtime**: fail closed and never silently; push, never poll (no `while True: sleep(n)`); only
  real errors are logged, no `console.*` in the frontend; state is a row, not a log line.
- **verify**: lint + types + tests is not evidence — run it live; smoke scripts get run, not
  written and left; a test arrives with its capability and touches no database; a silenced rule is
  not a passing rule; a convention worth having goes in the linter, not only in a document.
- **spacing**: one spacing scale and one type scale (gaps/margins/paddings on a base grid, text
  sizes from the theme); symmetry and rhythm; reuse one token per semantic role.
- **format**: imports at the top, never inline fully-qualified names, no unused imports; consistent
  indentation (no tab/space mix); JSON keeps the project's indent, key order and no spurious newline.
- **docs / naming**: README showcase vs CLAUDE internal; consistent prose-based names.

## Usage

```
conventions      topic=hardcoding               # no topic: the index of topics
commit_style     path=/path/to/repo             # then write the subject in that style
find_hardcoded   path=app/src   allow=brand     # extra filename substrings to skip
find_inconsistent path=app/src   rare=2 grid=4   # spacing/text-size scale snapshot + outliers
find_format       path=app/src   detail=false    # inline FQN, unused imports, indent, JSON style
find_duplication path=src        window=6 detail=false
```

Every tool returns structured JSON / text and never writes anything.

## Install as a Claude Code plugin

```
/plugin install devkit --marketplace jahirxtrap/custom-mcps
```

The plugin runs the copy Claude Code installed, with `uv run` (it needs [uv](https://docs.astral.sh/uv/)), and stays on that version until you update the plugin. To register it on its own for any MCP client instead, see the [root README](../../README.md#use-it-from-claude-code).
