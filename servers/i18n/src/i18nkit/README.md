# i18nkit

A small, dependency-free toolkit for **translation health** — the read-only logic behind
the `i18n` MCP server. It works on JSON locale files (flat like Minecraft `lang/*.json`,
or nested like `react-i18next` `locales/*.json`), flattening nested objects to dot-paths so
both compare with the same semantics.

## What it gives you

| Module | Provides |
|---|---|
| `parse` | `load_locale` (flat+nested), `flatten`, `list_locales`, `pick_base` |
| `diff` | `locale_diff` (missing/extra keys), `completeness` (% per locale) |
| `format` | `check_format` (placeholder consistency, empty values), `placeholders` |
| `scan` | `find_unused` (used-but-undefined / defined-but-unused), `used_keys` |
| `rules` | `guide` (embedded i18n conventions) |

## Example

```python
from i18nkit import locale_diff, completeness

report = locale_diff("frontend/src/locales")   # base auto-detected (en/en_us)
for locale, info in report["diff"].items():
    if not info["in_sync"]:
        print(locale, "missing", info["missing_count"], "keys")

print(completeness("frontend/src/locales"))
```

All functions are read-only and return plain dicts. The base locale is the given one,
else `en`/`en_us`, else the first found.
