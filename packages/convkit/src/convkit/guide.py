"""Embedded developer conventions by topic (verified against the user's real projects)."""
from __future__ import annotations

_TOPICS: dict[str, list[str]] = {
    "commit": [
        "Conventional commits: feat / fix / chore / refactor / docs. Short, lowercase subject "
        "(e.g. 'feat: tab system', 'fix: some fixes').",
        "NEVER add Co-Authored-By or any attribution footer.",
        "If a just-made commit has a small error or omission and is not yet pushed, fix it by "
        "amending that commit (git commit --amend) instead of adding a separate fixup commit.",
        "Changelog: plain past-tense bullets (Added/Fixed/Updated/Removed), no headers/versions/"
        "dates, derived from the commits since the last release; replace the whole file.",
        "Match the repo's existing style before committing (run commit_style).",
    ],
    "code": [
        "No comments. Self-explanatory names; a short docstring only when a constraint cannot be "
        "expressed in code itself.",
        "A docstring is one purely descriptive line. Rationale ('why' / 'how') belongs in the MR "
        "or the chat, never in the source -- no inline rationale, no TODO essays.",
        "The only documentation that lives inside the code is documentation as DATA, and there it "
        "is mandatory: the database COMMENT on every table and column, and the i18n label files. "
        "A migration without them is incomplete.",
        "English for code and diagnostics; respond to the user in Spanish.",
        "Latest stable versions of everything; nothing obsolete.",
        "Terse, expression-oriented; trust platform guarantees over defensive boilerplate.",
        "Imports at the top of the file.",
    ],
    "ssot": [
        "One authoritative definition per fact; everything else references or derives it, never "
        "copies it.",
        "A derived fact is never entered by hand: do not build a manual-entry form for something "
        "another module should produce -- leave it read-only until that source exists.",
        "A pointer to the owner instead of a copied value is the sign a split was designed right.",
        "Specs and architecture docs are an INPUT to the design, not the source of truth; the SSOT "
        "lives in the code and the data.",
        "Configuration is read in ONE module and the rest of the code asks that module, never the "
        "environment directly. Where the config file lives is one definition too.",
        "A form never restates a constraint the API already publishes: generate the validation "
        "schema from the contract and validate with it. A hand-written length, regex or required "
        "flag is a second source of truth that drifts the day the backend changes.",
        "A hand-declared entity type in a screen is a bug -- it means the endpoint is untyped "
        "upstream. Fix the response type at the source instead of patching the shape in the UI.",
        "Declare a resource once and render it per platform; copying a resource config into the "
        "second platform is the mistake this rule exists to prevent.",
    ],
    "dry": [
        "Extract LOGIC into reusable modules; keep UI construction where it is (do not over-extract widgets).",
        "Check the component/util catalog before building anything new -- most primitives already exist.",
        "Before writing a helper, search for it. A helper both apps need belongs in the shared "
        "package, never copied into the second one.",
        "Prefer a maintained library over writing the widget yourself (auth buttons, captcha, "
        "phone parsing, tables, forms); check the registry before building from scratch.",
        "No duplicated code; unify into shared methods/components.",
        "Thin routers/handlers delegate to services; the UI never calls the network (axios/fetch) "
        "directly -- it goes through a service.",
    ],
    "boundaries": [
        "Shared code is an ambient capability: it holds MECHANISMS -- anything any module may "
        "legitimately use. A capability that belongs to one module exclusively stays in that "
        "module, or everyone can import it and bypass the boundary.",
        "'How many modules use it today' is the wrong test -- it punishes whoever needs it first. "
        "Ask instead: is this a mechanism, or one module's exclusive capability?",
        "Share the logic, inject the platform: types, API client, auth and i18n live once in the "
        "shared package; each app supplies only its platform glue (storage implementation, base "
        "URL, navigation, screens). Never duplicate shared logic inside an app.",
        "Within a module the port (interface + value objects) lives in the domain layer and its "
        "adapter in the infrastructure layer.",
        "Modules that own separate capabilities do not import each other; they talk through "
        "published contracts and events.",
    ],
    "scope": [
        "Nothing is left dangling. A system built end to end, wired to nothing and called by "
        "nobody, is dead code however good it looks.",
        "Preparing the ground IS allowed when the consumer is real, named and on its way -- say "
        "who it is for. If the honest answer is 'maybe someone, someday', it is a dead system.",
        "Build the destination, not the current state. A document describing a migration away from "
        "a system you do not have is protecting a legacy owner, not describing work to do.",
        "Verify ownership before building: search whether those entities already have an owner in "
        "what is already built.",
    ],
    "hardcoding": [
        "No hardcoded user-facing text -- use i18n keys (t()/tr()); never t('KEY') || 'fallback'.",
        "No hardcoded colors or sizes -- use tokens from one place (themes.ts / Palette.kt). No "
        "scattered #hex, Color(0xFF...), .dp/.sp, or raw Tailwind palette classes.",
        "No secrets in the repo: configuration comes from the environment, the real env file is "
        "gitignored, and only the .example template is committed. Never a credential, connection "
        "string or key in code.",
        "Reference lists (countries, currencies, timezones) are data in a table, not literals in "
        "code -- see the data topic.",
        "New content is data (JSON) + a registry, not a new class; no magic numbers.",
        "Icons come from a library, not inline <svg>.",
    ],
    "data": [
        "The question is never 'is this a table or a row?' -- it is 'does production need this "
        "row?'. Schema plus the reference catalogs production genuinely needs go in a migration; "
        "anything that exists only so you can develop goes in the ONE dev seeder.",
        "A catalog derived from declarations in code is never seeded and never hand-edited: it is "
        "generated from the declaration, and a check fails on drift.",
        "Reference data comes from a maintained library, is written into the migration as literal "
        "rows, and lives in a table. Never hardcoded in application code, never a partial sample, "
        "never imported at runtime -- the migration is deterministic and its checksum covers it.",
        "A test fixture in a migration ships your test data to a customer; a reference catalog in "
        "the dev seed makes production start without it.",
        "All schema changes go through migrations; every migration has a working down(), and the "
        "runner tracks applied versions with a source checksum. Never hand-edit the database.",
        "Always scaffold a migration with the generator -- never hand-name the file or pick its "
        "timestamp; only edit the generated up/down.",
        "The schema is defined by the migrations. The ORM reflects the database, never the reverse "
        "-- never generate DDL from ORM metadata, and when you change one, change the other.",
        "Timestamps are timezone-aware; every table and column carries an English comment; "
        "connection and schema come from the environment.",
        "In development migrations are NOT immutable -- fix them in place, reconcile the recorded "
        "checksum, then prove the whole set applies from scratch on a throwaway database. Once "
        "live this flips: applied migrations are immutable and changes go forward.",
        "Numbers are stored as numeric types with digits only, no symbols and no formatting. A "
        "phone number is digits; a monetary amount always sits beside an explicit currency-code "
        "column.",
    ],
    "i18n": [
        "Code is English -- identifiers, keys, enum values, column names, docstrings. The UI "
        "language is always DATA: never code, never a fixed column.",
        "Translatable labels are a locale map stored as data ({'en': ..., 'es': ...}) with a "
        "required base locale and optional others. Per-language columns (name_es / name_en) do "
        "not scale -- never use them.",
        "Adding a language must be data only: no backend and no frontend code change. That is the "
        "test of whether the rule is being honoured.",
        "Never blur the two locale concepts: a translatable label is a MAP; a language preference "
        "(which language someone wants) is a scalar locale-code column.",
        "Catalog rows carry a stable English key plus the localized labels: the key identifies, "
        "the labels display.",
        "Business logic returns an i18n KEY, never user-facing text; the screen renders t(key), so "
        "logic stays decoupled from copy.",
        "Pluralization is a locale rule, never an if. count === 1 ? 'item' : 'items' breaks the "
        "moment a language has more than two forms -- CLDR defines up to six categories (zero, "
        "one, two, few, many, other). Pass the number to the library (i18next: t(key, {count}) "
        "resolving key_one / key_other / key_few / key_many through Intl.PluralRules) so a new "
        "locale stays just keys.",
        "Interpolate, never concatenate. One string with placeholders ('Hello {{name}}, you have "
        "{{count}} messages'), not fragments glued together in code -- word order and grammar "
        "differ per language, and a translator cannot fix a sentence they never see whole.",
        "camelCase names the KEY, never the suffix. The library looks up "
        "<key><separator><CLDR category> (count_one, count_many, count_other) and those category "
        "names are fixed by the standard -- renaming one to countOne makes the lookup miss and the "
        "plural fall back silently.",
        "The underscore is the library's reserved grammar (plurals and context), so keep it out of "
        "the key body: in an all-snake_case key like trad_text_column_one nobody can tell the "
        "suffix from the name, and a content key ending in _few / _many / _two collides with a "
        "real CLDR category. camelCase body + underscore only for suffixes keeps it unambiguous.",
        "Gendered or state-dependent variants use the library's context (key_male / key_female), "
        "not a string assembled by branching -- same rule, the suffix keeps the library's format.",
        "Dates, numbers, currency and lists are formatted by locale at the edge (Intl.DateTimeFormat "
        "/ NumberFormat / RelativeTimeFormat / ListFormat); store raw values and format on display.",
        "A key is a MEANING, not a string: never reuse one key in two places because the words "
        "happen to match today. Group keys in per-feature namespaces.",
        "Missing keys fall back to the base locale, configured once (fallbackLng), not patched per "
        "call site.",
        "Translated text runs 30-50% longer than English: never size a control to fit the English "
        "string.",
    ],
    "runtime": [
        "Fail closed: no privileged access without a fully resolved context, and any gap in the "
        "chain denies with a machine-readable reason.",
        "Never fail silently. Anything that will never succeed raises with a declared reason "
        "instead of passing quietly -- a caller must be able to tell 'nothing to do' from 'broken'.",
        "Push, never poll. No timers: if a deadline is knowable, sleep until it and let a "
        "notification recompute it; if it is not knowable, there is an event to listen for. "
        "'while True: sleep(n); check()' is the banned pattern, and a single drain on reconnect is "
        "the only exception.",
        "Only real errors are logged. No debug/info/warning narration, no 'started / finished / "
        "retrying' lines. Write a log line when something is broken and a human must act, and say "
        "what is now degraded. A transient failure a retry handles, or an outcome already recorded "
        "in a row, is not logged -- the data is the record.",
        "That covers your own logger calls, not the framework's startup banner or access log -- "
        "never silence those.",
    ],
    "verify": [
        "Lint, type-check and tests passing is not evidence that it works. Run it live against the "
        "real dependencies before calling it done.",
        "Every capability that crosses a boundary gets a smoke script that drives it end to end "
        "against the real services -- and the script is RUN, not written and left.",
        "Confirm behaviour with a live request, not by inspecting framework internals: a framework "
        "can stop populating the attribute you were reading and the inspection quietly lies.",
        "Audit by parsing the AST and looking inside the thing that actually does the work; a "
        "file-level grep is not an audit.",
        "Verify the code before repeating a claim about it -- a status list that is repeated "
        "instead of re-checked goes stale and misleads.",
        "Report the reasoning, not just the change: say what duplication was avoided and why.",
    ],
    "design": [
        "Centralize tokens (colors, sizes, accents) in one file; expose a semantic palette.",
        "Unified, catalogued components so the whole system looks consistent (Form*/Modal* on web, "
        "SettingsGroup/PreferenceRow on Compose).",
        "The component library owns component styling (className / tokens); global stylesheets "
        "hold layout helpers only, never component styles.",
        "One accent/theme system; everything else stays neutral and token-driven.",
    ],
    "spacing": [
        "One spacing scale from a single source (Compose: a Dimens/theme object; web: the Tailwind "
        "scale or CSS vars). Gaps, margins and paddings all come from it, not arbitrary values.",
        "Spacing stays on a base grid (steps of 4, ideally 8): 4/8/12/16/24/32. Avoid off-grid "
        "one-offs (5, 13, 18) and values used only once or twice; snap them to the nearest step.",
        "One type scale for text sizes from the theme (Compose: MaterialTheme.typography; web: "
        "text-* or a font-size token). No inline .sp or font-size px one-offs.",
        "Symmetry and rhythm: equal padding on matched sides, the same gap between sibling items, "
        "the same spacing for the same relationship across screens. Reuse one token per semantic "
        "role (screen padding, list gap) so it changes in one place.",
    ],
    "format": [
        "Imports at the top; never use a fully-qualified class name inline (import it and use the "
        "short name). Remove unused imports.",
        "Consistent indentation matching the file/language; never mix tabs and spaces, and don't "
        "drop 4-space blocks into a 2-space project (or vice versa).",
        "Data files (JSON) follow the project's existing format: indent unit (2 spaces for MC "
        "assets/data), no spurious trailing newline, and do NOT reorder/alphabetize keys unless the "
        "project already does (watch JSON.stringify/json.dump defaults).",
        "When editing a file, preserve its existing format; change only what you must, don't "
        "reformat the whole file. Prefer the project's formatter (ruff/prettier/ktlint) over ad-hoc style.",
    ],
    "patterns": [
        "Prefer NO response envelope: return the typed model directly so the client and its "
        "validation schemas can be generated from the contract (OpenAPI -> orval + zod). An "
        "envelope makes every generated response data: unknown and throws the types away. In a "
        "project that already has one, stay consistent with it there.",
        "Auto-discovery: drop a file (router / MCP tool / server) and it registers itself; no manual wiring.",
        "Data-driven: add content via JSON + a registry, with base/patch inheritance; never a class per item.",
        "Extract logic to reusable modules (services / RefCounted); the UI stays in the panel.",
        "Version contract for client/server apps (pyproject supported-app / supported-cli).",
        "Storage/config lives in a single module, not scattered.",
        "A new module must look like the ones that already exist: same naming, same guards, same "
        "error shapes, same list shape, same file layout.",
        "Reuse the existing base classes and shared components instead of re-deriving them.",
    ],
    "docs": [
        "README is the public showcase (prose, capabilities); CLAUDE.md is the internal guide "
        "(architecture, how to extend, hard rules).",
        "README style: no em-dash; parentheses for inline info; '=>' for 'leads to'; ':' after bold names.",
        "No trailing newline in README or data JSON (last byte is the last visible character).",
    ],
    "naming": [
        "Consistent, prose-based names with related words; do not mix get/fetch/load (or build/make/"
        "create) for the same idea -- names should read as one coherent system.",
        "By context: components PascalCase; hooks useXxx; vars/functions camelCase; locale keys "
        "camelCase, grouped in nested objects inside a per-feature namespace file "
        "(customers.json -> columns.createdAt) -- that is the base key only, plural and context "
        "suffixes keep the library's format (see i18n); backend wire fields snake_case; Java vars "
        "named by type.",
    ],
}


def topics() -> list[str]:
    return list(_TOPICS)


def guide(topic: str = "") -> str:
    """Render all conventions, or a single topic (commit/code/ssot/dry/boundaries/scope/
    hardcoding/data/i18n/runtime/verify/design/spacing/format/patterns/docs/naming)."""
    selected = {topic: _TOPICS[topic]} if topic in _TOPICS else _TOPICS
    lines = ["# Developer conventions"]
    for name, items in selected.items():
        lines += ["", f"## {name}"]
        lines += [f"- {item}" for item in items]
    return "\n".join(lines)
