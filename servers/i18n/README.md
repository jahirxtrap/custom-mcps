# i18n MCP server

A standalone, engine-agnostic MCP server for **translation health**: keep your locale files
in sync, complete, and consistent. It works on JSON locales — **flat** (Minecraft
`lang/en_us.json`) or **nested** (`react-i18next` `locales/en.json`) — flattening nested
objects to dot-paths so both compare the same way. All tools are **read-only**.

Built on [`fastmcp`](https://gofastmcp.com) over the dependency-free
[`i18nkit`](../../packages/i18nkit) library.

## Tools

| Tool | Purpose |
|---|---|
| `locale_diff` | Per locale: keys missing vs the base, and keys the base lacks. The "in sync" check. |
| `completeness` | Percentage of base keys translated in each locale. |
| `check_format` | Placeholders (`{name}`, `{0}`, `%s`) that differ from the base, and empty values. |
| `find_unused` | Cross keys with code: used-but-undefined (broken) and defined-but-unused (dead). |
| `i18n_guide` | Embedded conventions (no hardcoded strings, locales in sync, placeholders, naming). |

## Usage

Point `path` at the folder of locale JSON files; the base locale is auto-detected
(`en`/`en_us`) or set with `base`:

```
locale_diff   path=frontend/src/locales
completeness  path=assets/mymod/lang  base=en_us
find_unused   path=frontend/src/locales  src=frontend/src
```

`find_unused`'s `patterns` is an optional JSON array of regexes (default matches `t("KEY")`
and `tr("KEY")`), so it adapts to your framework.

## Output contract

Every tool returns structured JSON (it reports; it never rewrites translations).
