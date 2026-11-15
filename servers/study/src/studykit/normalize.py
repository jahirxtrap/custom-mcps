"""Clean the text a PDF extractor leaves: page furniture, broken lines and typographic leftovers."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

_PAGE_BREAK = "\f"
_EDGE_LINES = 2
_MIN_REPEATS = 3
_REPEAT_SHARE = 0.4
_SEQUENCE_SHARE = 0.5
_SPACE_SEPARATOR = "Zs"
_FORMAT_CHARACTER = "Cf"
_LIGATURES = str.maketrans(
    {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}
)
_SPACES = re.compile(r"[ \t]+")
_TRAILING_SPACES = re.compile(r" +$", re.MULTILINE)
_BLANK_RUN = re.compile(r"\n{3,}")
_PAGE_NUMBER = re.compile(r"^\d{1,4}$")
_TRAILING_NUMBER = re.compile(r" (\d{1,4})$")
_HYPHEN_BREAK = re.compile(r"([^\W\d_])-\n([^\W\d_])")
_SOFT_BREAK = re.compile(r"([^\W\d_],?)\n([^\W\d_])")


def _lines(page: str) -> list[str]:
    return [line.strip() for line in page.splitlines()]


def _edges(lines: list[str]) -> list[str]:
    filled = [line for line in lines if line]
    return filled[:_EDGE_LINES] + filled[-_EDGE_LINES:]


def _furniture(pages: list[list[str]]) -> set[str]:
    counts = Counter(line for lines in pages for line in set(_edges(lines)))
    threshold = max(_MIN_REPEATS, round(len(pages) * _REPEAT_SHARE))
    return {line for line, seen in counts.items() if seen >= threshold and not _PAGE_NUMBER.match(line)}


def _without_furniture(lines: list[str], furniture: set[str]) -> list[str]:
    return [line for line in lines if line not in furniture]


def _number_candidate(lines: list[str]) -> tuple[int, int, bool] | None:
    filled = [index for index, line in enumerate(lines) if line]
    if not filled:
        return None
    for index in (filled[-1], filled[0]):
        if _PAGE_NUMBER.match(lines[index]):
            return index, int(lines[index]), True
    last = filled[-1]
    trailing = _TRAILING_NUMBER.search(lines[last])
    if trailing:
        return last, int(trailing.group(1)), False
    return None


def _without_page_numbers(pages: list[list[str]]) -> list[list[str]]:
    candidates = [_number_candidate(lines) for lines in pages]
    offsets = Counter(found[1] - index for index, found in enumerate(candidates) if found)
    if not offsets:
        return pages
    offset, agreeing = offsets.most_common(1)[0]
    if agreeing < max(2, round(len(pages) * _SEQUENCE_SHARE)):
        return pages
    cleaned = []
    for index, (lines, found) in enumerate(zip(pages, candidates, strict=True)):
        if found and found[1] - index == offset:
            position, _, whole = found
            lines = list(lines)
            lines[position] = "" if whole else _TRAILING_NUMBER.sub("", lines[position])
        cleaned.append(lines)
    return cleaned


def _plain_character(char: str) -> str:
    category = unicodedata.category(char)
    if category == _SPACE_SEPARATOR:
        return " "
    if category == _FORMAT_CHARACTER:
        return ""
    return char


def _join_hyphen(match: re.Match[str]) -> str:
    before, after = match.group(1), match.group(2)
    return before + after if after.islower() else match.group(0)


def _join_soft(match: re.Match[str]) -> str:
    before, after = match.group(1), match.group(2)
    return f"{before} {after}" if after.islower() else match.group(0)


def _reflow(text: str) -> str:
    text = "".join(_plain_character(char) for char in text).translate(_LIGATURES)
    text = _SPACES.sub(" ", text)
    text = _TRAILING_SPACES.sub("", text)
    text = _HYPHEN_BREAK.sub(_join_hyphen, text)
    text = _SOFT_BREAK.sub(_join_soft, text)
    return _BLANK_RUN.sub("\n\n", text).strip() + "\n"


def normalize_extracted(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    pages = [_lines(page) for page in text.split(_PAGE_BREAK)]
    furniture = _furniture(pages)
    pages = [_without_furniture(lines, furniture) for lines in pages]
    pages = _without_page_numbers(pages)
    body = "\n\n".join("\n".join(lines).strip("\n") for lines in pages if any(lines))
    return _reflow(body)
