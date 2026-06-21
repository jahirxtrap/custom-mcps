# devkit MCP server

A **personal** MCP server that carries the user's **development conventions** and the checks
that verify them — across stacks (Java, Kotlin/Jetpack Compose, TypeScript/React, GDScript,
Python). Guides say what to follow; tools look at the real code/history. All read-only.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`convkit`](../../packages/convkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `conventions` | The embedded conventions, all or one topic: commit/code/dry/hardcoding/design/spacing/format/patterns/docs/naming. |
| `commit_style` | Analyze a repo's recent commit subjects (prefixes, % conventional, length, case) — the style to imitate. |
| `commit_context` | Diffstat + changed files + recent subjects + style, to draft a commit message that fits the repo. |
| `find_hardcoded` | Hardcoded colors (`#hex`, `Color(0xFF…)`, any stack) + web `px`/`rem` values + raw Tailwind → tokens. |
| `find_inconsistent` | Snapshot the spacing and text-size scales in use; flag rare one-offs, off-grid spacing, and Tailwind arbitrary values. |
| `find_format` | AI-typical format breaks: inline fully-qualified names, unused imports, mixed tab/space indent, JSON indent outliers. |
| `find_duplication` | Repeated normalized line blocks → DRY candidates (heuristic). |

## What it encodes (verified against real projects)

- **commit**: conventional, short, lowercase; never Co-Authored-By; changelog from commits.
- **code**: no comments, English, latest stable versions, terse.
- **dry / patterns**: extract logic to reusable modules, thin routers → services, unified API
  envelope `{success, status, message, data}`, auto-discovery, data-driven content (JSON + registry).
- **hardcoding / design**: text → i18n, colors/sizes → one token file, catalogued components.
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
