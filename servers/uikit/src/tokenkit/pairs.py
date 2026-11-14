"""Find which foreground/background token pairs the code actually puts together."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_SKIP_DIRS = {
    ".expo", ".git", ".next", ".nuxt", ".svelte-kit", ".turbo", ".venv", "__pycache__",
    "build", "coverage", "dist", "generated", "node_modules", "out", "target", "venv",
}
_SOURCE_EXT = (".ts", ".tsx", ".js", ".jsx", ".svelte", ".vue", ".html", ".kt")
_CLASS_ATTR = re.compile(r"""(?:class|className)\s*=\s*(?:\{`|\{"|\{'|"|'|`)([^"'`]{0,400})""")
_STRING = re.compile(r"""["'`]([^"'`\n]{0,200})["'`]""")
_FOREGROUND = re.compile(r"\btext-([\w-]+)\b")
_BACKGROUND = re.compile(r"\bbg-([\w-]+)\b")
_BORDER = re.compile(r"\bborder-([\w-]+)\b")
_ON_PREFIX = re.compile(r"^on-(.+)$")
_TAILWIND_WORDS = {
    "center", "left", "right", "start", "end", "justify", "wrap", "nowrap", "balance",
    "pretty", "ellipsis", "clip", "transparent", "current", "inherit", "auto", "xs", "sm",
    "base", "lg", "xl", "2xl", "3xl", "4xl", "5xl", "6xl",
}


def source_files(base: Path):
    """Every source file under `base`, skipping vendored and generated trees."""
    if base.is_file():
        yield base
        return
    for entry in base.iterdir():
        if entry.name in _SKIP_DIRS:
            continue
        if entry.is_dir():
            yield from source_files(entry)
        elif entry.suffix in _SOURCE_EXT:
            yield entry


_files = source_files


def _token(name: str, prefix: str) -> str | None:
    if name in _TAILWIND_WORDS or name.isdigit():
        return None
    if prefix and name.startswith(f"{prefix}-"):
        return name[len(prefix) + 1:]
    return None if prefix else name


def canon(name: str) -> str:
    """One spelling for a token however it is written: primary-soft, primarySoft, primary_soft."""
    return re.sub(r"[-_\s]", "", name).lower()


def declared_pairs(tokens: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Pairs the naming itself declares: an 'on-x' token is meant to sit on 'x'."""
    index = {canon(name): name for name in tokens}
    out: list[tuple[str, str, str]] = []
    for name in tokens:
        found = _ON_PREFIX.match(name)
        back = index.get(canon(found.group(1))) if found else None
        if back:
            out.append((name, back, "named on-*"))
    return out


def used_pairs(src: str | Path, prefix: str = "") -> list[dict[str, Any]]:
    """Foreground and background tokens that appear in the same class attribute or variant map."""
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for file in _files(Path(src)):
        text = file.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            for chunk in _CLASS_ATTR.findall(line) or _STRING.findall(line):
                fronts = {
                    token for raw in _FOREGROUND.findall(chunk)
                    if (token := _token(raw, prefix))
                }
                backs = {
                    token for raw in _BACKGROUND.findall(chunk)
                    if (token := _token(raw, prefix))
                }
                for back in backs:
                    for front in fronts:
                        entry = found.setdefault(
                            (front, back),
                            {"front": front, "back": back, "uses": 0, "where": []},
                        )
                        entry["uses"] += 1
                        if len(entry["where"]) < 3:
                            entry["where"].append(f"{file.name}:{number}")
    return sorted(found.values(), key=lambda item: -item["uses"])


def variant_pairs(src: str | Path, prefix: str = "") -> list[dict[str, Any]]:
    """Pairs a variant map ties together: the same variant name styling a surface and its text."""
    surfaces: dict[str, dict[str, str]] = {}
    inks: dict[str, dict[str, str]] = {}
    for file in _files(Path(src)):
        text = file.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            entry = re.match(r"\s*([\w-]+)\s*:\s*['\"`]([^'\"`]+)['\"`]", line)
            if not entry:
                continue
            variant, classes = entry.group(1), entry.group(2)
            back = next(
                (token for raw in _BACKGROUND.findall(classes) if (token := _token(raw, prefix))),
                None,
            )
            front = next(
                (token for raw in _FOREGROUND.findall(classes) if (token := _token(raw, prefix))),
                None,
            )
            where = f"{file.name}:{number}"
            if back and not front:
                surfaces.setdefault(file.stem, {}).setdefault(variant, back)
                surfaces[file.stem][f"{variant}@"] = where
            if front and not back:
                inks.setdefault(file.stem, {}).setdefault(variant, front)
                inks[file.stem][f"{variant}@"] = where

    out: list[dict[str, Any]] = []
    for stem, variants in surfaces.items():
        for variant, back in variants.items():
            front = inks.get(stem, {}).get(variant)
            if variant.endswith("@") or not front:
                continue
            out.append(
                {
                    "front": front,
                    "back": back,
                    "uses": 1,
                    "variant": f"{stem}.{variant}",
                    "where": [variants.get(f"{variant}@", stem)],
                }
            )
    return out


def find_pairs(tokens: dict[str, Any], src: str | Path | None = None, prefix: str = "") -> list[dict[str, Any]]:
    """Every pair worth measuring, with how it was found."""
    index = {canon(name): name for name in tokens}
    out: list[dict[str, Any]] = [
        {"front": front, "back": back, "uses": 0, "source": reason, "where": []}
        for front, back, reason in declared_pairs(tokens)
    ]
    seen = {(item["front"], item["back"]) for item in out}
    if src:
        for entry in variant_pairs(src, prefix) + used_pairs(src, prefix):
            front = index.get(canon(entry["front"]))
            back = index.get(canon(entry["back"]))
            if not front or not back or (front, back) in seen:
                continue
            seen.add((front, back))
            entry["front"], entry["back"] = front, back
            entry.setdefault("source", "variant map" if "variant" in entry else "used together")
            out.append(entry)
    return [item for item in out if item["front"] in tokens and item["back"] in tokens]
