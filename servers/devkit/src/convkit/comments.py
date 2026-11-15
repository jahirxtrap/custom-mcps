"""Comments and docstrings that break the no-comments convention, found per comment family."""
from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path
from typing import Any

from .analyze import _DETAIL_LIMIT, _SUMMARY_LIMIT, _fragments, _vendored

_HASH_EXT = (".gd", ".sh", ".ps1")
_SLASH_EXT = (
    ".java", ".kt", ".kts", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".rs", ".go", ".cs", ".dart",
    ".swift", ".c", ".h", ".cpp", ".hpp", ".css", ".scss", ".less",
)
_MARKUP_EXT = (".html", ".svelte", ".vue")
_SQL_EXT = (".sql",)
_DIRECTIVE = re.compile(
    r"^(?:#!|# -\*-|# noqa|# type:|# pragma|# fmt:|# pylint|# ruff|# mypy|# isort|# shellcheck|#requires"
    r"|#region|#endregion|#\[|#(?:include|define|if|ifdef|ifndef|endif|else|elif|pragma|undef|error|import)\b"
    r"|// ?eslint|// ?@ts-|// ?prettier|/// ?<reference|//go:|// ?biome|// ?region|// ?endregion"
    r"|// ?svelte-ignore|// ?noinspection|// ?@formatter|// ?webpack|// ?@?vite|// ?@flow|// ?@jsx"
    r"|<!-- ?svelte-ignore|<!-- ?prettier|<!-- ?eslint|<!DOCTYPE"
    r"|-- ?name:|--sql)",
    re.IGNORECASE,
)
_RATIONALE = re.compile(
    r"\b(?:because|so that|to avoid|in order to|due to|workaround|hack|todo|fixme)\b|note:", re.IGNORECASE
)
_DECLARED = re.compile(
    r"\b(?:class|interface|object|fun|fn|function|def|struct|enum|trait|type|record|val|var|let|const|mod|func)"
    r"\s+([A-Za-z_]\w*)"
)
_NAMED = re.compile(r"([A-Za-z_]\w*)\s*(?:\(|=|:|;)")
_WORD = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])")
_DOC_WORD = re.compile(r"[A-Za-z]+")
_STOP = {
    "the", "a", "an", "of", "to", "for", "and", "or", "in", "on", "its", "this", "that", "it", "is", "are",
    "be", "with", "by", "from", "as", "at", "one", "all", "every", "each", "into", "under", "over",
    "return", "returns", "get", "gets", "set", "sets", "given", "when", "if", "then",
}
_DOC_MARKERS = ("/**", "*/", "///", "//!", "##")
_MATCH_PREFIX = 4
_CLIP = 120
_KINDS = ("comment", "doc_lines", "doc_repeats_name", "doc_rationale")


def families(suffix: str) -> set[str]:
    """The comment families a file extension carries; empty when the check does not read that file."""
    suffix = suffix.lower()
    if suffix == ".py":
        return {"python"}
    if suffix == ".gd":
        return {"hash", "gddoc"}
    if suffix in _HASH_EXT:
        return {"hash"}
    if suffix in _SLASH_EXT:
        return {"slash"}
    if suffix in _MARKUP_EXT:
        return {"markup", "slash"}
    if suffix in _SQL_EXT:
        return {"sql", "slash"}
    return set()


def _clip(text: str) -> str:
    text = text.strip()
    return text if len(text) <= _CLIP else text[: _CLIP - 1] + "…"


def _same_word(a: str, b: str) -> bool:
    return a == b or (min(len(a), len(b)) >= _MATCH_PREFIX and (a.startswith(b) or b.startswith(a)))


def repeats_name(doc: str, name: str) -> bool:
    """Whether every content word of the docstring is already in the name it describes."""
    identifier = [word.lower() for word in _WORD.findall(name)]
    content = [word.lower() for word in _DOC_WORD.findall(doc) if word.lower() not in _STOP]
    return bool(content) and bool(identifier) and all(
        any(_same_word(word, part) for part in identifier) for word in content
    )


def _doc_findings(content: list[str], line: int, name: str, source_line: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    text = _clip(source_line)
    if len(content) > 1:
        findings.append({"line": line, "kind": "doc_lines", "lines": len(content), "name": name, "text": text})
    joined = " ".join(content)
    if _RATIONALE.search(joined):
        findings.append({"line": line, "kind": "doc_rationale", "name": name, "text": text})
    if name and repeats_name(joined, name):
        findings.append({"line": line, "kind": "doc_repeats_name", "name": name, "text": text})
    return findings


def _declared_name(lines: list[str], start: int) -> str:
    for line in lines[start:]:
        stripped = line.strip()
        declared = _DECLARED.search(stripped)
        if not stripped or (stripped.startswith(("@", "}", ")", "]")) and not declared):
            continue
        match = declared or _NAMED.search(stripped)
        return match.group(1) if match else ""
    return ""


def _python(text: str, lines: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.COMMENT and not _DIRECTIVE.match(token.string):
                line = token.start[0]
                findings.append({"line": line, "kind": "comment", "lines": 1, "text": _clip(lines[line - 1])})
    except (tokenize.TokenError, SyntaxError):
        findings = _by_lines(lines, {"hash"})
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc is None or getattr(node, "decorator_list", None):
            continue
        line = node.body[0].lineno
        content = [item.strip() for item in doc.splitlines() if item.strip()]
        findings.extend(_doc_findings(content, line, getattr(node, "name", ""), lines[line - 1]))
    return sorted(findings, key=lambda item: item["line"])


def _block_end(lines: list[str], start: int, opener: int, closer: str) -> int:
    if closer in lines[start].strip()[opener:]:
        return start
    for index in range(start + 1, len(lines)):
        if closer in lines[index]:
            return index
    return len(lines) - 1


def _run(lines: list[str], start: int, prefix: str) -> int:
    index = start
    while index + 1 < len(lines) and lines[index + 1].strip().startswith(prefix):
        index += 1
    return index


def _doc_content(raw: list[str]) -> list[str]:
    content = []
    for item in raw:
        stripped = item.strip()
        for marker in _DOC_MARKERS:
            stripped = stripped.replace(marker, " ")
        stripped = stripped.strip().lstrip("*").strip()
        if stripped:
            content.append(stripped)
    return content


def _doc_prefix(stripped: str, kinds: set[str]) -> str | None:
    if "slash" in kinds and stripped.startswith(("///", "//!")):
        return stripped[:3]
    if "gddoc" in kinds and stripped.startswith("##"):
        return "##"
    return None


def _comment_end(lines: list[str], index: int, stripped: str, kinds: set[str]) -> int | None:
    if "slash" in kinds and stripped.startswith("{/*"):
        return _block_end(lines, index, 3, "*/")
    if "slash" in kinds and stripped.startswith("/*"):
        return _block_end(lines, index, 2, "*/")
    if "markup" in kinds and stripped.startswith("<!--"):
        return _block_end(lines, index, 4, "-->")
    if "slash" in kinds and stripped.startswith("//"):
        return _run(lines, index, "//")
    if "hash" in kinds and stripped.startswith("#"):
        return _run(lines, index, "#")
    if "sql" in kinds and stripped.startswith("--"):
        return _run(lines, index, "--")
    return None


def _by_lines(lines: list[str], kinds: set[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped or _DIRECTIVE.match(stripped):
            index += 1
            continue
        number = index + 1
        doc_prefix = _doc_prefix(stripped, kinds)
        if "slash" in kinds and stripped.startswith("/**") and not stripped.startswith("/**/"):
            end = _block_end(lines, index, 3, "*/")
        elif doc_prefix:
            end = _run(lines, index, doc_prefix)
        else:
            end = None
        if end is not None:
            content = _doc_content(lines[index : end + 1])
            findings.extend(_doc_findings(content, number, _declared_name(lines, end + 1), lines[index]))
            index = end + 1
            continue
        end = _comment_end(lines, index, stripped, kinds)
        if end is None:
            index += 1
            continue
        findings.append({"line": number, "kind": "comment", "lines": end - index + 1, "text": _clip(lines[index])})
        index = end + 1
    return findings


def review_text(text: str, suffix: str) -> list[dict[str, Any]]:
    """Every comment, and every docstring over one line, repeating its name or carrying rationale, in a file."""
    kinds = families(suffix)
    if not kinds:
        return []
    lines = text.splitlines()
    if "python" in kinds:
        return _python(text, lines)
    return _by_lines(lines, kinds)


def find_comments(path: str, exclude: str = "", detail: bool = False) -> dict[str, Any]:
    """Comments and convention-breaking docstrings across a tree, by kind, with complete counts."""
    base = Path(path)
    limit = _DETAIL_LIMIT if detail else _SUMMARY_LIMIT
    fragments = _fragments(exclude)
    hits: dict[str, list[dict[str, Any]]] = {kind: [] for kind in _KINDS}
    scanned = 0
    for file in (base.rglob("*") if base.is_dir() else [base]):
        if not file.is_file() or _vendored(file, fragments) or not families(file.suffix):
            continue
        scanned += 1
        rel = str(file.relative_to(base)) if base.is_dir() else str(file)
        for finding in review_text(file.read_text(encoding="utf-8", errors="replace"), file.suffix):
            hits[finding["kind"]].append({"file": rel, **finding})
    return {
        "scanned_files": scanned,
        **{kind: hits[kind][:limit] for kind in _KINDS},
        **{f"{kind}_count": len(hits[kind]) for kind in _KINDS},
        "detail": detail,
        "note": "comment = a comment line or block (directives such as noqa, ts-expect-error, shebangs and "
        "attributes excepted); doc_lines = a docstring over one line; doc_repeats_name = a docstring whose "
        "words are all in the name it describes; doc_rationale = a docstring explaining why. Python is "
        "read with its tokenizer and ast, the other families (// and /* */, <!-- -->, --, #) by line. "
        "The docstring of a decorated definition is data for the decorator (a tool's or a route's "
        "description) and is not checked. Lists are cut at the limit; the counts are complete; "
        "detail=true lists more.",
    }
