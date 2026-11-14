# loaderkit

A small, dependency-free toolkit for **multiloader mod workspaces** — the read-only
logic behind the `modkit` MCP server. It scans by the `<modid>-<version>-multi` folder
convention and never hardcodes a mod name, so it works on any such workspace.

## What it gives you

| Module | Provides |
|---|---|
| `scan` | `list_mods`, `mod_info`, `find_version_dirs`, `parse_version_dir`, `LOADERS` |
| `props` | `parse_properties`, `parse_mc_version`, `java_for_mc` (the MC→Java table) |
| `compare` | `loader_sync` (hash loader source trees), `find_symbol` |
| `checks` | `check_structure`, `check_json` |

## Embedded conventions (generic Minecraft, not any single mod)

- **Java per MC**: `1.17–1.17.1 → 16`, `1.18–1.20.4 → 17`, `1.20.5–1.21.11 → 21`, `26.1+ → 25`.
- **Structure**: `common/` holds resources only (no `.java`); Java is identical across loaders.
- **JSON** (assets/data): no trailing newline (last byte `}`/`]`), LF only (no CRLF).
- **`repositories`**: live in the root build, not in the loaders.

## Example

```python
from loaderkit import list_mods, loader_sync, check_json

for mod in list_mods("/path/to/workspace"):
    print(mod["mod"], "->", mod["latest"]["version"])

report = loader_sync("/path/to/mod/modid-1.21.11-multi")
if not report["in_sync"]:
    print("loaders drifted:", report["differing"])
```

All functions are read-only and return plain dicts/lists.
