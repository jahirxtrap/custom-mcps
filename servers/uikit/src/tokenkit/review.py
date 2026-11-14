"""Gather the evidence a usability review needs: signals, never verdicts."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .pairs import source_files

_MUTATION = re.compile(r"\b(?:useMutation|mutateAsync|use(?:Create|Update|Delete|Remove)\w*)\s*\(|\.mutate\s*\(")
_PENDING = re.compile(r"\b(isPending|isLoading|isSubmitting|loading|busy|pending|Spinner|Skeleton)\b")
_HANDLER = re.compile(r"\b(?:onPress|onClick|onLongPress|onSelect)\s*=|^\s*(?:const|function)\s+(?:on|handle)\w*")
_DESTROYS = re.compile(r"\b(?:\w*[Dd]elete|\w*[Rr]emove|\w*[Dd]estroy|\w*[Ww]ipe)\w*\s*\(")
_HOST_API = re.compile(
    r"\.(?:delete|remove|removeChild|removeAttribute|removeEventListener|removeAll\w*|clear)\s*\(|"
    r"\b(?:URL|localStorage|sessionStorage|Reflect|Object)\.|removeAllRanges|removeListener"
)
_CONFIRM = re.compile(r"\b(Confirm\w*|confirm\(|AlertDialog|areYouSure|DestructiveDialog)\b")
_RAW_ERROR = re.compile(r"\{\s*(?:[\w.]*\b(?:error|err|e)\.message|String\(\s*\w*[Ee]rr\w*\s*\))")
_JSX_TEXT = re.compile(r">\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ][^<>{}\n]{2,80}?)\s*</")
_TEXT_ATTR = re.compile(
    r"\b(placeholder|label|title|alt|aria-label|accessibilityLabel)\s*=\s*\"([^\"]{2,80})\""
)
_TYPE_LINE = re.compile(r"^\s*(?:export\s+)?(?:type|interface)\b|^\s*\w+\??\s*:\s*\(|=>\s*\w+;?\s*$")
_CODEY = re.compile(r"[()\[\]{}/\\|+=*;_$@#&]|\.\w|=>|::")
_MARKUP_EXT = (".tsx", ".jsx", ".svelte", ".vue", ".html")
_I18N = re.compile(r"\bt\(\s*[\"'`]")
_I18N_DIRS = ("i18n", "locales", "lang", "messages", "translations")
_WORD = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,}")


def _hit(file: Path, base: Path, number: int, text: str) -> dict[str, Any]:
    where = file.relative_to(base) if base.is_dir() else file
    return {"file": str(where), "line": number, "text": text.strip()[:110]}


def _looks_like_copy(value: str, phrase_only: bool) -> bool:
    if _CODEY.search(value):
        return False
    words = _WORD.findall(value)
    if not words:
        return False
    if phrase_only:
        return len(words) > 1
    return len(value) > 3 and value[0].isupper()


def review_context(path: str | Path) -> dict[str, Any]:
    """Signals under `path` for the heuristics that leave a trace in the code."""
    base = Path(path)
    status: list[dict[str, Any]] = []
    destructive: list[dict[str, Any]] = []
    raw_errors: list[dict[str, Any]] = []
    literals: list[dict[str, Any]] = []
    scanned = 0

    for file in source_files(base):
        text = file.read_text(encoding="utf-8", errors="replace")
        scanned += 1
        in_i18n = any(part in _I18N_DIRS for part in file.parts)
        has_pending = bool(_PENDING.search(text))
        has_confirm = bool(_CONFIRM.search(text))

        for number, line in enumerate(text.splitlines(), 1):
            declaration = bool(_TYPE_LINE.search(line))
            if _MUTATION.search(line) and not has_pending and not declaration:
                status.append(_hit(file, base, number, line))
            destroys = _DESTROYS.search(line) and not _HOST_API.search(line)
            if destroys and _HANDLER.search(line) and not has_confirm and not declaration:
                destructive.append(_hit(file, base, number, line))
            if _RAW_ERROR.search(line):
                raw_errors.append(_hit(file, base, number, line))
            if in_i18n or _I18N.search(line) or declaration:
                continue
            if file.suffix in _MARKUP_EXT:
                for found in _JSX_TEXT.findall(line):
                    if _looks_like_copy(found, phrase_only=True):
                        literals.append(_hit(file, base, number, found))
            for _, found in _TEXT_ATTR.findall(line):
                if _looks_like_copy(found, phrase_only=False):
                    literals.append(_hit(file, base, number, found))

    signals = {
        "status_without_feedback": {
            "heuristic": "1. Visibility of system status",
            "asks": "does this action tell the user it is running?",
            "count": len(status),
            "hits": status[:60],
        },
        "destructive_without_confirm": {
            "heuristic": "5. Error prevention",
            "asks": "is the committing action confirmed, or only reported afterwards?",
            "count": len(destructive),
            "hits": destructive[:60],
        },
        "raw_error_shown": {
            "heuristic": "9. Help users recognise and recover from errors",
            "asks": "is the message plain language, or the exception as it came?",
            "count": len(raw_errors),
            "hits": raw_errors[:60],
        },
        "text_outside_i18n": {
            "heuristic": "2. Match between the system and the real world",
            "asks": "does it speak the user's language, including enum values?",
            "count": len(literals),
            "hits": literals[:60],
        },
    }
    return {
        "path": str(base),
        "scanned_files": scanned,
        "signals": signals,
        "total": sum(entry["count"] for entry in signals.values()),
        "note": "Evidence for a review, not a verdict: every hit is a place to look, and the file "
        "is checked as a whole, so a loading state or a confirmation elsewhere in it clears the "
        "line. Four of the ten heuristics leave a trace a parser can follow; the rest (consistency, "
        "recognition over recall, accelerators, minimalism, documentation) are read, not measured. "
        "Walk the hits with design_guide('heuristics') as the rubric.",
    }
