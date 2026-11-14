# convkit

A dependency-free toolkit for **developer conventions** — the logic behind the `devkit` MCP
server. It carries the user's conventions (verified against real projects) and the checks
that enforce them across stacks: Java, Kotlin/Compose, TypeScript/React, GDScript, Python.

## What it gives you

| Module | Provides |
|---|---|
| `guide` | `guide(topic)`, `topics()` — embedded conventions (commit/code/dry/hardcoding/design/patterns/docs/naming) |
| `git` | `commit_style` (analyze recent subjects), `commit_context` (diffstat + files + style) |
| `analyze` | `find_hardcoded` (colors/sizes/raw-tailwind, multi-stack), `find_duplication` (repeated blocks) |

## Example

```python
from convkit import guide, commit_style, find_hardcoded

print(guide("hardcoding"))
print(commit_style("/path/to/repo"))                 # prefixes, % conventional, length, case
print(find_hardcoded("/path/to/app/src"))            # hex / Color(0xFF...) / 14.dp / px / raw-tailwind
```

## `find_hardcoded` (multi-stack)

Flags, per language, what should live in a token/theme file:
- `#rrggbb` (web/CSS-in-code), `Color(0xFF...)` / `0xFFRRGGBB` (Compose/Kotlin/Java),
- web size values `14px` / `1.5rem` (as `"12px"` / `[12px]`),
- raw Tailwind palette classes (`text-blue-500`).

Compose `.dp` / `.sp` spacing is idiomatic and intentionally not flagged; comments and token
files (`themes.*`, `palette.*`, …) are skipped.

Token files (`themes.*`, `palette.*`, `tokens.*`, `tailwind.config`, …) are skipped; add more
via `allow`.

All functions are read-only and return plain dicts/strings.
