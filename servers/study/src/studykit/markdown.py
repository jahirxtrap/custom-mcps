"""Markdown and pandoc markup taken out of a text, keeping where each remaining character came from."""
from __future__ import annotations

import re

_WHOLE = 0
_MARKUP: list[tuple[re.Pattern[str], tuple[int, ...]]] = [
    (re.compile(r"\A---\n.*?\n(?:---|\.\.\.)[ \t]*\n", re.DOTALL), (_WHOLE,)),
    (re.compile(r"^(?:```|~~~).*?^(?:```|~~~)[ \t]*$", re.DOTALL | re.MULTILINE), (_WHOLE,)),
    (re.compile(r"<!--.*?-->", re.DOTALL), (_WHOLE,)),
    (re.compile(r"`[^`\n]+`"), (_WHOLE,)),
    (re.compile(r"<[^<>\n]+>"), (_WHOLE,)),
    (re.compile(r"!\[[^\]\n]*\]\([^)\n]*\)"), (_WHOLE,)),
    (re.compile(r"(\[)([^\]\n]*)(\]\([^)\n]*\))"), (1, 3)),
    (re.compile(r"\[[^\]\n]*@[^\]\n]*\]"), (_WHOLE,)),
    (re.compile(r"\[\^[^\]\n]+\]:?"), (_WHOLE,)),
    (re.compile(r"(?<![\w@])@[\w:.#$%&+?<>~/-]*\w"), (_WHOLE,)),
    (re.compile(r"\{[^{}\n]*\}"), (_WHOLE,)),
    (re.compile(r"https?://[^\s<>)\]]+"), (_WHOLE,)),
    (re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+", re.MULTILINE), (_WHOLE,)),
    (re.compile(r"^[ \t]*(?:[-*+]|\d{1,3}[.)])[ \t]+", re.MULTILINE), (_WHOLE,)),
    (re.compile(r"^[ \t]*>[ \t]?", re.MULTILINE), (_WHOLE,)),
    (re.compile(r"^:[ \t]+", re.MULTILINE), (_WHOLE,)),
    (re.compile(r"^:{3,}.*$", re.MULTILINE), (_WHOLE,)),
    (re.compile(r"^[ \t]*[|:\- \t]*-{3,}[|:\- \t]*$", re.MULTILINE), (_WHOLE,)),
    (re.compile(r"^[ \t]*(?:\*{3,}|_{3,})[ \t]*$", re.MULTILINE), (_WHOLE,)),
    (re.compile(r"\|"), (_WHOLE,)),
    (re.compile(r"(\*{1,3}|_{1,3})(?=\S)(.+?)(?<=\S)(\1)"), (1, 3)),
    (re.compile(r"(\\)[\\`*_{}\[\]()#+\-.!>|~]"), (1,)),
]


def _tidy_gaps(text: str, keep: list[bool]) -> None:
    index = 0
    while index < len(text):
        if keep[index]:
            index += 1
            continue
        end = index
        while end < len(text) and not keep[end]:
            end += 1
        if index > 0 and keep[index - 1] and text[index - 1] == " " and end < len(text) and text[end] == " ":
            keep[index - 1] = False
        index = end


def plain_text(text: str) -> tuple[str, list[int]]:
    keep = [True] * len(text)
    for pattern, groups in _MARKUP:
        for match in pattern.finditer(text):
            for group in groups:
                start, stop = match.span(group)
                keep[start:stop] = [False] * (stop - start)
    _tidy_gaps(text, keep)
    origins = [index for index, kept in enumerate(keep) if kept]
    return "".join(text[index] for index in origins), origins
