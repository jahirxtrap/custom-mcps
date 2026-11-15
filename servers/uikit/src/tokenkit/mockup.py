"""Measure a mockup against the design values an app's own code really uses."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .color import parse, to_hex
from .pairs import source_files
from .tokens import read_theme

_STYLE_EXT = (".css", ".scss", ".sass", ".less")
_DESIGN_EXT = (*_STYLE_EXT, ".ts", ".tsx", ".js", ".jsx", ".svelte", ".vue", ".html", ".kt", ".kts")
_DEPENDENCY_FILES = ("package.json", "build.gradle", "build.gradle.kts", "libs.versions.toml")
_SKIP_DIRS = {"node_modules", ".git", "build", "dist", ".venv", "venv", "target", ".svelte-kit", ".next", "coverage"}
_THEME_JSON_MAX = 512 * 1024
_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
_FUNCTIONAL = re.compile(r"\b(?:rgba?|hsla?|oklch|oklab)\([^)]*\)")
_VAR_DEFINITION = re.compile(r"--([\w-]+)\s*:\s*([^;}]+)")
_VAR_REFERENCE = re.compile(r"var\(\s*--([\w-]+)")
_VAR_SET = re.compile(r"""setProperty\(\s*["']--([\w-]+)["']""")
_FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}]+)", re.IGNORECASE)
_FONT_SHORTHAND = re.compile(r"(?<![\w-])font\s*:\s*([^;}]+)", re.IGNORECASE)
_FONT_SIZE_TOKEN = re.compile(r"\d[\d.]*(?:px|rem|em|%|pt)(?:\s*/\s*[\d.]+(?:px|rem|em|%)?)?\s+")
_FONT_RESOURCE = re.compile(r"R\.font\.(\w+)")
_FONT_PACKAGE = re.compile(r"@fontsource(?:-variable)?/([\w-]+)")
_FONT_FAMILY_SOURCE = re.compile(r"fontFamily\s*:\s*\{([^}]*)\}", re.DOTALL)
_FONT_ENTRY = re.compile(r"\w+\s*:\s*(?:\[([^\]]*)\]|(['\"][^'\"]*['\"]))")
_FONT_VARIABLE_WORDS = ("font", "sans", "serif", "mono", "family")
_GENERIC_FAMILIES = {
    "sans serif", "serif", "monospace", "system ui", "ui sans serif", "ui serif", "ui monospace", "ui rounded",
    "cursive", "fantasy", "inherit", "initial", "unset", "default", "sansserif", "emoji", "math",
    "apple system", "blinkmacsystemfont",
}
_FAMILY_SHAPE = re.compile(r"^[a-z0-9][a-z0-9 .+]{0,39}$")
_COMPOSE_COLOR = re.compile(r"Color\(\s*0x([0-9a-fA-F]{8})\s*\)")
_LENGTH = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\.?(px|rem|dp|sp)\b")
_CSS_DECLARATION = re.compile(r"(?<![\w-])([a-z-]+)\s*:\s*([^;{}]+)", re.IGNORECASE)
_COMPOSE_CALL = re.compile(
    r"\.?(padding|size|height|width|heightIn|widthIn|offset|spacedBy|RoundedCornerShape|fontSize|lineHeight)\s*\(([^()]*)\)"
)
_COMPOSE_SHADOW = re.compile(r"\b(?:elevation|shadow)\s*(?:\(|=)")
_TAILWIND_SPACING = re.compile(
    r"(?<![\w-])-?(?:p|px|py|pt|pb|pl|pr|ps|pe|m|mx|my|mt|mb|ml|mr|ms|me|gap|gap-x|gap-y|space-x|space-y|inset|top|left|right|bottom)"
    r"-(\d+(?:\.\d+)?|px)\b"
)
_TAILWIND_SIZE = re.compile(r"(?<![\w-])(?:w|h|min-w|min-h|max-w|max-h|size)-(\d+(?:\.\d+)?|px)\b")
_TAILWIND_RADIUS = re.compile(
    r"(?<![\w-])rounded(?:-[trbl]{1,2}|-[se]{1,2})?(?:-(none|sm|md|lg|xl|2xl|3xl|4xl|full))?\b"
)
_TAILWIND_TEXT = re.compile(r"(?<![\w-])text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)\b")
_TAILWIND_ARBITRARY = re.compile(r"(?<![\w-])([a-z-]+)-\[(\d+(?:\.\d+)?)(px|rem)\]")
_TAILWIND_SHADOW = re.compile(r"(?<![\w-])shadow(?:-(none|sm|md|lg|xl|2xl|inner))?\b")
_TAILWIND_RADIUS_PX = {
    None: 4, "none": 0, "sm": 2, "md": 6, "lg": 8, "xl": 12, "2xl": 16, "3xl": 24, "4xl": 32, "full": 9999,
}
_TAILWIND_TEXT_PX = {
    "xs": 12, "sm": 14, "base": 16, "lg": 18, "xl": 20, "2xl": 24, "3xl": 30, "4xl": 36, "5xl": 48, "6xl": 60,
    "7xl": 72, "8xl": 96, "9xl": 128,
}
_TAILWIND_UNIT = 4
_REM = 16
_SHADOW = re.compile(r"box-shadow\s*:\s*([^;}]+)", re.IGNORECASE)
_ICON_WORDS = (
    "lucide", "iconify", "heroicons", "phosphor", "tabler", "fontawesome", "font-awesome", "remixicon",
    "feather", "material-symbols", "material-icons", "octicons", "ionicons", "boxicons",
)
_ICON_SOURCE = re.compile(r"""(?:from\s+|import\s+|href=|src=)["']([^"']+)["']""", re.IGNORECASE)
_COMPOSE_ICONS = re.compile(r"\bIcons\.(?:Default|Filled|Outlined|Rounded|Sharp|TwoTone|AutoMirrored)\b")
_DRAWABLE = re.compile(r"R\.drawable\.\w+")
_STYLE_ATTR = re.compile(r"""style\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.IGNORECASE | re.DOTALL)
_CLASS_ATTR = re.compile(r"""class(?:Name)?\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_SPACING_WORDS = ("padding", "margin", "gap", "inset", "top", "left", "right", "bottom", "spacing", "space")
_SIZE_WORDS = ("width", "height", "size", "basis")
_TYPE_WORDS = ("font-size", "line-height", "letter-spacing", "text", "leading", "tracking")
_RADIUS_WORDS = ("radius", "rounded")
_FAMILIES = ("spacing", "size", "type", "radius")
_ANY = "any"
_UNIVERSAL_INKS = ("#000000", "#ffffff")
_COMPONENT_MAX = 200.0
_PILL_RADIUS = 999.0
_TEMPLATE_MARKS = ("{", "$", "(", "<", ">")


def _named(lowered: str, words: tuple[str, ...], ends: bool = True) -> bool:
    return any(
        lowered == word or lowered.startswith(f"{word}-") or (ends and lowered.endswith(f"-{word}")) for word in words
    )


def _family_of(name: str) -> str | None:
    lowered = name.lower().strip("-")
    if _named(lowered, _RADIUS_WORDS):
        return "radius"
    if _named(lowered, _TYPE_WORDS, ends=False):
        return "type"
    if _named(lowered, _SPACING_WORDS):
        return "spacing"
    if _named(lowered, _SIZE_WORDS):
        return "size"
    return None


def _px(value: str, unit: str) -> float:
    number = float(value)
    return round(number * _REM, 2) if unit == "rem" else number


def _compose_family(call: str) -> str:
    if call in ("padding", "offset", "spacedBy"):
        return "spacing"
    if call == "RoundedCornerShape":
        return "radius"
    if call in ("fontSize", "lineHeight"):
        return "type"
    return "size"


def _family_name(raw: str) -> str | None:
    name = raw.strip().strip("\"'").strip().lower().replace("_", " ").replace("-", " ").strip()
    if name.endswith(" variable"):
        name = name[: -len(" variable")]
    if not name or name in _GENERIC_FAMILIES or not _FAMILY_SHAPE.match(name):
        return None
    return name


def _icon_library(source: str) -> str | None:
    lowered = source.lower()
    return next((word for word in _ICON_WORDS if word in lowered), None)


class _Design:
    def __init__(self) -> None:
        self.colors: Counter[str] = Counter()
        self.variables: set[str] = set()
        self.fonts: Counter[str] = Counter()
        self.lengths: dict[str, Counter[float]] = {family: Counter() for family in (*_FAMILIES, _ANY)}
        self.shadows = 0
        self.icons: Counter[str] = Counter()

    def color(self, text: str) -> None:
        for pattern in (_HEX, _FUNCTIONAL):
            for match in pattern.finditer(text):
                color = parse(match.group(0))
                if color:
                    self.colors[to_hex(color)] += 1

    def font(self, stack: str) -> None:
        name = _family_name(stack.split(",")[0])
        if name:
            self.fonts[name] += 1

    def length(self, family: str, value: float) -> None:
        self.lengths[family][value] += 1

    def icon(self, library: str, count: int) -> None:
        if count:
            self.icons[library] += count

    def lengths_in(self, family: str, value: str) -> None:
        for number, unit in _LENGTH.findall(value):
            self.length(family, _px(number, unit))

    def css(self, text: str) -> None:
        self.color(text)
        for name, value in _VAR_DEFINITION.findall(text):
            self.variables.add(name)
            lowered = name.lower()
            if any(word in lowered for word in _FONT_VARIABLE_WORDS) and ('"' in value or "'" in value):
                self.font(value)
            if "shadow" in lowered:
                self.shadows += 1
            family = _family_of(name)
            if family:
                self.lengths_in(family, value)
        for match in _FONT_FAMILY.finditer(text):
            self.font(match.group(1))
        for match in _FONT_SHORTHAND.finditer(text):
            parts = _FONT_SIZE_TOKEN.split(match.group(1))
            if len(parts) > 1:
                self.font(parts[-1])
        for prop, value in _CSS_DECLARATION.findall(text):
            if prop.startswith("--"):
                continue
            family = _family_of(prop)
            if family:
                self.lengths_in(family, value)
        self.shadows += len(_SHADOW.findall(text))

    def tailwind(self, text: str) -> None:
        for match in _TAILWIND_SPACING.finditer(text):
            self.length("spacing", 1.0 if match.group(1) == "px" else float(match.group(1)) * _TAILWIND_UNIT)
        for match in _TAILWIND_SIZE.finditer(text):
            self.length("size", 1.0 if match.group(1) == "px" else float(match.group(1)) * _TAILWIND_UNIT)
        for match in _TAILWIND_RADIUS.finditer(text):
            self.length("radius", float(_TAILWIND_RADIUS_PX[match.group(1)]))
        for match in _TAILWIND_TEXT.finditer(text):
            self.length("type", float(_TAILWIND_TEXT_PX[match.group(1)]))
        for prop, number, unit in _TAILWIND_ARBITRARY.findall(text):
            self.length(_family_of(prop) or "spacing", _px(number, unit))
        self.shadows += len(_TAILWIND_SHADOW.findall(text))

    def compose(self, text: str) -> None:
        self.color(text)
        for match in _COMPOSE_COLOR.finditer(text):
            argb = match.group(1)
            color = parse(f"#{argb[2:]}{argb[:2]}")
            if color:
                self.colors[to_hex(color)] += 1
        for match in _FONT_RESOURCE.finditer(text):
            self.fonts[match.group(1).lower().replace("_", " ")] += 1
        for call, args in _COMPOSE_CALL.findall(text):
            self.lengths_in(_compose_family(call), args)
        for number, unit in _LENGTH.findall(text):
            self.length("type" if unit == "sp" else _ANY, _px(number, unit))
        self.shadows += len(_COMPOSE_SHADOW.findall(text))
        self.icon("material-icons", len(_COMPOSE_ICONS.findall(text)))
        self.icon("drawables", len(_DRAWABLE.findall(text)))

    def markup(self, text: str) -> None:
        for match in _ICON_SOURCE.finditer(text):
            library = _icon_library(match.group(1))
            if library:
                self.icons[library] += 1

    def dependencies(self, file: Path, text: str) -> None:
        if file.name == "package.json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                return
            for name in {**data.get("dependencies", {}), **data.get("devDependencies", {})}:
                library = _icon_library(name)
                if library:
                    self.icons[name] += 1
                font = _FONT_PACKAGE.fullmatch(name)
                if font:
                    self.fonts[font.group(1).replace("-", " ")] += 1
            return
        for line in text.splitlines():
            library = _icon_library(line)
            if library and ("implementation" in line or "=" in line):
                self.icons[library] += 1

    def theme(self, file: Path) -> None:
        for colors in read_theme(file).values():
            for color in colors.values():
                self.colors[to_hex(color)] += 1

    def has_length(self, family: str, value: float) -> bool:
        return value in self.lengths[family] or value in self.lengths[_ANY]

    def summary(self) -> dict[str, Any]:
        return {
            "colors": len(self.colors),
            "variables": len(self.variables),
            "fonts": sorted(self.fonts),
            "lengths": {family: len(self.lengths[family]) for family in _FAMILIES},
            "shadows": self.shadows,
            "icons": sorted(self.icons),
        }


def _design_files(base: Path):
    if base.is_file():
        yield base
        return
    yield from source_files(base)
    for entry in base.rglob("*"):
        if any(part in _SKIP_DIRS for part in entry.parts) or not entry.is_file():
            continue
        if entry.name in _DEPENDENCY_FILES or entry.suffix in _STYLE_EXT:
            yield entry
        elif entry.suffix == ".json" and "lock" not in entry.name and entry.stat().st_size <= _THEME_JSON_MAX:
            yield entry


def read_design(path: str | Path, extra: str = "") -> _Design:
    """What the app's code says about its own look: colors, variables, fonts, lengths, shadows, icons."""
    design = _Design()
    roots = [Path(path), *(Path(item.strip()) for item in extra.split(",") if item.strip())]
    seen: set[Path] = set()
    for root in roots:
        for file in _design_files(root):
            if file in seen:
                continue
            seen.add(file)
            if file.name in _DEPENDENCY_FILES:
                design.dependencies(file, file.read_text(encoding="utf-8", errors="replace"))
            elif file.suffix == ".json":
                design.theme(file)
            elif file.suffix in (".kt", ".kts"):
                design.compose(file.read_text(encoding="utf-8", errors="replace"))
            elif file.suffix in _STYLE_EXT:
                design.css(file.read_text(encoding="utf-8", errors="replace"))
            elif file.suffix in _DESIGN_EXT:
                text = file.read_text(encoding="utf-8", errors="replace")
                design.css(styled_text(text))
                design.color(text)
                design.tailwind(text)
                design.markup(text)
                for block in _FONT_FAMILY_SOURCE.finditer(text):
                    for listed, quoted in _FONT_ENTRY.findall(block.group(1)):
                        design.font(listed or quoted)
    return design


def styled_text(markup: str) -> str:
    """The CSS a markup file carries: its style blocks and style attributes."""
    return "\n".join(_STYLE_BLOCK.findall(markup)) + "\n" + ";\n".join(_STYLE_ATTR.findall(markup))


def _mockup_text(mockup: str) -> tuple[str, str]:
    candidate = Path(mockup)
    if len(mockup) < 400 and candidate.is_file():
        return candidate.name, candidate.read_text(encoding="utf-8", errors="replace")
    return "inline", mockup


def _closest(value: float, pool: Counter[float]) -> float | None:
    return min(pool, key=lambda known: (abs(known - value), -pool[known], known)) if pool else None


def _reportable(family: str, value: float) -> bool:
    if family in ("spacing", "size"):
        return value <= _COMPONENT_MAX
    if family == "radius":
        return value < _PILL_RADIUS
    return True


def check_mockup(mockup: str, path: str | Path, extra: str = "") -> dict[str, Any]:
    """Report every design value the mockup uses that the app's own code never does."""
    name, html = _mockup_text(mockup)
    app = read_design(path, extra)
    used = _Design()
    styles = styled_text(html)
    used.css(styles)
    used.tailwind(" ".join(_CLASS_ATTR.findall(html)))
    used.markup(html)
    used.variables.update(name for name, _ in _VAR_DEFINITION.findall(html))
    used.variables.update(_VAR_SET.findall(html))
    referenced = set(_VAR_REFERENCE.findall(styles))

    findings: dict[str, list[dict[str, Any]]] = {}
    colors = [
        {"value": color, "count": count}
        for color, count in used.colors.most_common()
        if color not in app.colors and color[:7] not in _UNIVERSAL_INKS
    ]
    if colors:
        findings["colors"] = colors
    variables = sorted(referenced - used.variables - app.variables)
    if variables:
        findings["variables"] = [{"value": f"--{item}"} for item in variables]
    fonts = [{"value": font, "count": count} for font, count in used.fonts.most_common() if font not in app.fonts]
    if fonts:
        findings["fonts"] = fonts
    for family in _FAMILIES:
        pool = app.lengths[family] + app.lengths[_ANY]
        missing = [
            {"value": value, "count": count, "closest": _closest(value, pool)}
            for value, count in sorted(used.lengths[family].items())
            if not app.has_length(family, value) and _reportable(family, value)
        ]
        if missing:
            findings[family] = missing
    if used.shadows and not app.shadows:
        findings["shadows"] = [{"value": "box-shadow", "count": used.shadows}]
    icons = [
        {"value": library, "count": count}
        for library, count in used.icons.items()
        if not _known_icons(library, app.icons)
    ]
    if icons:
        findings["icons"] = icons
    total = sum(len(items) for items in findings.values())
    return {
        "mockup": name,
        "app": str(path),
        "app_design": app.summary(),
        "mockup_uses": used.summary(),
        "findings": findings,
        "total": total,
        "note": "Values the mockup uses that never appear in the app's code, by category, with the closest "
        "value the app does use. Lengths are px (rem x16, dp and sp as px, Tailwind's default scale). "
        "Not reported: spacings and sizes above 200 px (layout), pill radii of 999 px and up, black "
        "and white at any opacity, and the fallbacks of a font stack (only its first family counts). "
        "A value a library supplies without the app writing it shows up here too: pass that folder in "
        "`extra` or judge it. Composition and hierarchy are not measured.",
    }


def _known_icons(library: str, known: Counter[str]) -> bool:
    lowered = library.lower()
    return any(lowered in name.lower() or name.lower() in lowered for name in known)
