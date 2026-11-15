# uikit MCP server

Interface design **measured, not argued**. It reads a theme's design tokens, works out which
colors the code really puts together, checks those pairs against WCAG, and measures a mockup
against the design the app's code really uses. Framework agnostic and entirely read-only.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`tokenkit`](src/tokenkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `design_guide` | The embedded guidance: `heuristics` / `laws` / `contrast` / `targets` / `tokens` / `mockup`. |
| `read_tokens` | Every theme under a path, with its tokens normalized to hex. Reads source objects, theme JSON and CSS variables. |
| `find_pairs` | Which foreground/background pairs are really in play, and how each one was found. |
| `check_contrast` | Measures every pair of every theme against WCAG 2.2, failures first. |
| `review_context` | The evidence a usability review needs, for the four heuristics that leave a trace in the code. |
| `contrast` | Two colors in, the ratio and the AA/AAA verdicts out. |
| `check_mockup` | Every design value a mockup uses that the app's own code never does, with the closest value the app does use. |

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

## Mockups measured against the code

A mockup decides a design before any code, so it has to be drawn with the app's design and not
with a framework's defaults. The server's instructions carry the rule: a new screen, a new panel
or a redesign that touches more than one component starts by asking the user whether to make a
mockup, and waits for the answer, because a mockup takes time; a change to a single control needs
none. `design_guide('mockup')` is the procedure once the answer is yes: discover the app's design
by reading and counting (the tokens file, the root stylesheet, the font packages and the icon
library; for Compose, the theme, typography and shapes files), build with the values found, show
the states that decide, deliver one self-contained HTML file where the user asked for it, and
measure it. How a client displays the file is the client's business.

`check_mockup` is the measurement, and it knows no app. It reads what the code says about its own
look: CSS and preprocessor files, Tailwind classes on their default scale, Compose `dp`/`sp` and
`Color(0x...)`, theme JSON, and `package.json` or Gradle for the font and icon packages. Then it
lists every color, CSS variable, font family, length (spacing, size, type, radius, in px), shadow
and icon library the mockup uses that the app never does, each with the closest value the app does
use. It judges nothing and does not measure composition.

Not reported, because they are not design values: spacings and sizes above 200 px (layout), pill
radii of 999 px and up, black and white at any opacity, and the fallbacks of a font stack (only
its first family counts). A value a library supplies without the app writing it shows up too:
pass that folder in `extra`, or judge it.

Measured on six real mockups against the two apps they were drawn for (a Svelte and Tailwind
desktop client, a Compose player) it reports between 12 and 62 findings each, and every one is a
value the mockup really uses off the app's scale: a 30 px control where the app draws 32, type at
13.5 px, paddings of 7 and 22, a palette copied from another product.

## Usage

```
design_guide    topic=contrast
design_guide    topic=mockup
check_mockup    mockup=mockups/settings.html  path=src  extra=packages/ui
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

See [`src/tokenkit`](src/tokenkit) for the underlying library.
