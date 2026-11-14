# tokenkit

A small, dependency-free toolkit for **design tokens and contrast** — the read-only logic
behind the `uikit` MCP server. It reads a theme from whatever shape it ships in, works out
which colors the code actually puts together, and measures those pairs against WCAG.

The colour maths is the easy half. The reason this exists is the other one: a contrast
report is only worth reading when the pairs in it are the pairs the interface really draws,
and those are written in the code, not in a table somebody typed.

## What it gives you

| Module | Provides |
|---|---|
| `color` | `parse` (#hex, `rgb()`, `hsl()`, `oklch()`, `oklab()`), `over` (alpha compositing), `luminance`, `contrast`, `to_hex` |
| `tokens` | `read_theme` (one file), `read_tokens` (a whole folder) |
| `pairs` | `declared_pairs` (naming), `variant_pairs` (variant maps), `used_pairs` (classes used together), `find_pairs` |
| `check` | `check_contrast` (a whole theme), `measure` (one pair), `contrast_of` (two colors) |
| `guide` | `design_guide` (usability heuristics, psychology laws, WCAG thresholds, tokens) |

## The three theme shapes it reads

```
source object   light: { surface: "#FFFFFF", text: "#0F1111" }      .ts .tsx .js .kt
theme JSON      { "kind": "dark", "colors": { "surface": "#0f0f0f" } }
CSS variables   :root { --surface: #fff; }  .dark { --surface: #0f0f0f; }
```

## How a pair is found

Three ways, in order of how much they can be trusted:

1. **The naming declares it:** a token called `on-surface` says where it belongs, so
   `on-surface` over `surface` is a pair nobody had to guess.
2. **A variant map ties it:** the variant that styles a surface and the variant of the same
   name that styles its text (`tva`, `cva` and friends) => that fill and that ink go together.
3. **The classes appear together:** a `bg-*` and a `text-*` in the same class attribute.

## Example

```python
from tokenkit import check_contrast

report = check_contrast(
    "packages/theme/src/themes/brand.ts",
    src="apps",
    prefix="app",            # bg-app-surface resolves to the token `surface`
)

for theme, entry in report["report"].items():
    print(theme, entry["failing"], "of", entry["pairs"], "pairs fail")
    for row in entry["failures"]:
        print(f"  {row['ratio']}:1  {row['front']} on {row['back']}  ({row['source']})")
```

A translucent token is composited onto what sits behind it before being measured, so a
`#ffffff0d` hover reports what the eye actually sees. Decorative tokens (logo, shadow,
scrollbar, hover) are left out unless asked for, and anything that reads as a border or an
outline is held to 3:1 rather than 4.5:1, the way WCAG splits them.

All functions are read-only and return plain dicts.
