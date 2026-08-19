# devkit MCP server

A **personal** MCP server that carries the user's **development conventions** and the checks
that verify them — across stacks (Java, Kotlin/Jetpack Compose, TypeScript/React, GDScript,
Python). Guides say what to follow; tools look at the real code/history. All read-only.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`convkit`](../../packages/convkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `conventions` | The embedded conventions, all or one topic: commit/code/ssot/dry/boundaries/scope/hardcoding/data/i18n/runtime/verify/design/spacing/format/patterns/docs/naming. |
| `commit_style` | Analyze a repo's recent commit subjects (prefixes, % conventional, length, case) — the style to imitate. |
| `commit_context` | Diffstat + changed files + recent subjects + style, to draft a commit message that fits the repo. |
| `find_hardcoded` | Hardcoded colors (`#hex`, `Color(0xFF…)`, any stack) + web `px`/`rem` values + raw Tailwind → tokens. |
| `find_inconsistent` | Snapshot the spacing and text-size scales in use; flag rare one-offs, off-grid spacing, and Tailwind arbitrary values. |
| `find_format` | AI-typical format breaks: inline fully-qualified names, unused imports, mixed tab/space indent, JSON indent outliers. |
| `find_duplication` | Repeated normalized line blocks → DRY candidates (heuristic). |

## What it encodes (verified against real projects)

- **commit**: conventional, short, lowercase; never Co-Authored-By; changelog from commits.
- **code**: no comments (the two exceptions are documentation as data: DB `COMMENT` and i18n
  files), one-line descriptive docstrings, English, latest stable versions, terse.
- **ssot**: one authoritative definition per fact, referenced or derived and never copied; a
  derived fact is never hand-entered; config read in one module; forms validate with the schema
  generated from the contract, never a restated constraint.
- **dry / patterns**: extract logic to reusable modules, thin routers → services, search before
  writing a helper, prefer a maintained library; prefer **no** response envelope so the client and
  its zod schemas generate from the contract; auto-discovery, data-driven content (JSON + registry).
- **boundaries**: shared code holds mechanisms, a module's exclusive capability stays with it;
  share the logic and inject the platform.
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
  real errors are logged.
- **verify**: lint + types + tests is not evidence — run it live; smoke scripts get run, not
  written and left; audit the AST, not a grep; verify before repeating a claim.
- **spacing**: one spacing scale and one type scale (gaps/margins/paddings on a base grid, text
  sizes from the theme); symmetry and rhythm; reuse one token per semantic role.
- **format**: imports at the top, never inline fully-qualified names, no unused imports; consistent
  indentation (no tab/space mix); JSON keeps the project's indent, key order and no spurious newline.
- **docs / naming**: README showcase vs CLAUDE internal; consistent prose-based names.

## Usage

```
conventions      topic=hardcoding
commit_style     repo=/path/to/repo
commit_context   repo=/path/to/repo            # then draft the message in that style
find_hardcoded   path=app/src   allow=brand    # extra filename substrings to skip
find_inconsistent path=app/src   rare=2 grid=4  # spacing/text-size scale snapshot + outliers
find_format       path=app/src                  # inline FQN, unused imports, indent, JSON style
find_duplication path=src        window=6
```

Every tool returns structured JSON / text and never writes anything.
