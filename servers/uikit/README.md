# uikit MCP server

Interface design **measured, not argued**. It reads a theme's design tokens, works out which
colors the code really puts together, and checks those pairs against WCAG. Framework
agnostic and entirely read-only.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`tokenkit`](../../packages/tokenkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `design_guide` | The embedded guidance: `heuristics` / `laws` / `contrast` / `targets` / `tokens`. |
| `read_tokens` | Every theme under a path, with its tokens normalized to hex. Reads source objects, theme JSON and CSS variables. |
| `find_pairs` | Which foreground/background pairs are really in play, and how each one was found. |
| `check_contrast` | Measures every pair of every theme against WCAG 2.2, failures first. |
| `review_context` | The evidence a usability review needs, for the four heuristics that leave a trace in the code. |
| `contrast` | Two colors in, the ratio and the AA/AAA verdicts out. |

## Why the pairs matter more than the maths

A contrast ratio is four lines of arithmetic. What makes a report worth reading is whether
the pairs in it are the ones the interface actually draws: a table written by hand reports
combinations nobody uses and misses the ones that matter.

So the pairs come from the code, three ways:

- **The naming declares it:** `on-surface` says where it belongs (the Material convention).
- **A variant map ties it:** in a `tva` / `cva` block, the variant that styles a surface and
  the one that styles its text belong together.
- **The classes appear together:** a `bg-*` and a `text-*` in the same class attribute.

## The heuristics half

Most of Nielsen's ten are a read, not a measurement: no parser decides whether there is an
accelerator for the frequent user. Four of them do leave a trace, so `review_context` gathers
it and stops there => the tool supplies the evidence, the reviewer supplies the judgement, the
same split `commit_context` makes.

| Signal | Heuristic | What it looks for |
|---|---|---|
| `status_without_feedback` | 1. Visibility of system status | a mutation in a file with no loading state anywhere |
| `destructive_without_confirm` | 5. Error prevention | a delete bound to a UI event, with no confirmation in the file |
| `raw_error_shown` | 9. Recovering from errors | an exception rendered as it came |
| `text_outside_i18n` | 2. The user's language | copy in markup that never passes through `t()` |

It is deliberately conservative: the file is judged as a whole, so a confirmation or a spinner
elsewhere in it clears the line, and anything that reads as code is dropped. Measured on two real
front ends it reports single digits, which is the point => a list nobody reads finds nothing.

## Usage

```
design_guide    topic=contrast
read_tokens     path=packages/theme/src/themes/brand.ts
check_contrast  path=packages/theme/src/themes/brand.ts  src=apps  prefix=app
check_contrast  path=backend/core/packs/cconnect/themes
contrast        front="#2563EB"  back="#D6E2FF"
```

`prefix` strips a token prefix, so `bg-app-surface` resolves to the token `surface`. `src`
is the folder to read the pairs from: leave it out and only the pairs the naming declares
are measured.

## What it will and will not flag

A translucent token is composited onto what sits behind it first, so a `#ffffff0d` hover is
measured as the eye sees it. Borders and outlines are held to 3:1 and body text to 4.5:1,
the way WCAG splits them. Decorative tokens (logo, shadow, scrollbar, hover) are skipped
unless `include_decorative` is set, because a brand mark owes no contrast ratio.

## Output contract

Every tool returns structured JSON and never writes anything.

See [`packages/tokenkit`](../../packages/tokenkit) for the underlying library.
