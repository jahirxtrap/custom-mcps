# i18n MCP server

A standalone, engine-agnostic MCP server for **translation health**: keep your locale files
in sync, complete, and consistent. All tools are **read-only**.

It reads both layouts and detects which one it is looking at:

| Layout | Looks like | Keys become |
|---|---|---|
| one file per locale | `lang/en_us.json`, `lang/es_es.json` | `some.dot.path` |
| one folder per locale | `locales/en/common.json`, `locales/es/cart.json` | `common:save`, `cart:units` |

Nested objects are flattened to dot-paths, and **keys are matched without their plural
suffix**, so a locale carrying more CLDR forms than the base (Spanish `_many` against English
`_one`/`_other`) is not reported as a difference — while a key pluralized on one side only,
which silently breaks the `count` lookup, is.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`i18nkit`](../../packages/i18nkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `locale_diff` | Per locale: keys missing vs the base, keys the base lacks, and plural forms that disagree. |
| `completeness` | Percentage of base keys translated in each locale. |
| `check_format` | Placeholders (`{{name}}`, `{name}`, `{0}`, `%s`) that differ from the base, and empty values. |
| `find_unused` | Cross keys with code: asked-but-undeclared (broken) and declared-but-unasked (dead). |
| `i18n_guide` | Embedded conventions: text as data, namespaces, pluralization, interpolation, locale formatting. |

## Usage

Point `path` at the folder holding the locales; the base is auto-detected (`en`/`en_us`) or
set with `base`:

```
locale_diff   path=packages/core/src/i18n/locales
completeness  path=assets/mymod/lang  base=en_us
find_unused   path=packages/core/src/i18n/locales  src=apps
find_unused   path=... src=... default_ns=common  ignore=orders:status.delivered,orders:status.failed
```

On the namespaced layout an unprefixed `t("save")` resolves to `default_ns` (`common`), and
that namespace is **exempt from the dead-key report** because it is the shared catalogue and may
legitimately run ahead of its callers. `ignore` takes the keys only a variable ever names — one
per enum value the API publishes. `patterns` is an optional JSON array of regexes (default
matches `t("KEY")` and `tr("KEY")`). Vendored trees (`node_modules`, `dist`, `.next`, …) are
skipped.

## Output contract

Every tool returns structured JSON (it reports; it never rewrites translations).
