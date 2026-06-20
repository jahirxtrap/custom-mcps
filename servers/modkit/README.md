# modkit MCP server

A **personal** MCP server for **multiloader mod workspaces** — the mechanical, repetitive
half of mod-dev that complements `minecraft-dev` (which handles the API/decompile side).
It scans by the `<modid>-<version>-multi` folder convention and **never hardcodes a mod
name**, so it works on any such workspace. All tools are **read-only**.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`loaderkit`](../../packages/loaderkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `list_mods` | Inventory: every mod under a root + its version folders + the most recent one. |
| `mod_info` | A version folder's `gradle.properties` + the Java version expected for its MC version. |
| `loader_sync` | Compare fabric/forge/neoforge Java; report files missing or differing between loaders. |
| `check_structure` | `common/` has no `.java`, loaders present, gradle files in place, Java matches MC, repositories only in root. |
| `check_json` | Scan assets/data JSON for trailing newline and CRLF (byte-level conventions). |
| `find_symbol` | Find an API/class/method across all loaders' Java; returns file + line per hit. |

## What it does NOT do

It does not analyze API changes, decompile, or diff Minecraft versions — that is
`minecraft-dev`'s job. `modkit` is the mechanical layer: inventory, structure, sync,
search. Publishing order is intentionally excluded (it is mod-specific, not generic).

## Embedded conventions

Generic Minecraft knowledge (a Java-per-MC table, JSON byte rules, canonical structure)
lives in `loaderkit` — never a specific mod. See its README.

## Run / register

```bash
uv run modkit-mcp                    # run over stdio
uv run python scripts/register.py    # register every server (this one included) at user scope
```
