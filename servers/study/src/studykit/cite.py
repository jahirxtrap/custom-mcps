"""APA 7 citation formatting, BibTeX entries, and DOI lookup."""
from __future__ import annotations

import re
import unicodedata
import urllib.request
from typing import Any

_BIBTYPE = {"article": "article", "book": "book", "chapter": "incollection", "web": "misc"}


def _split_authors(authors: Any) -> list[str]:
    if isinstance(authors, list):
        return [str(a).strip() for a in authors if str(a).strip()]
    if not authors:
        return []
    return [a.strip() for a in re.split(r";| and |&", str(authors)) if a.strip()]


def _surname(name: str) -> str:
    if "," in name:
        return name.split(",", 1)[0].strip()
    parts = name.split()
    return parts[-1] if parts else name


def _initials(given: str) -> str:
    return " ".join(f"{p[0].upper()}." for p in re.split(r"[\s.]+", given.strip()) if p)


def _format_author(name: str) -> str:
    if "," in name:
        surname, given = (s.strip() for s in name.split(",", 1))
        initials = _initials(given)
        return f"{surname}, {initials}".strip().rstrip(",")
    parts = name.split()
    if len(parts) == 1:
        return parts[0]
    surname = parts[-1]
    return f"{surname}, {_initials(' '.join(parts[:-1]))}"


def _join_authors(names: list[str]) -> str:
    formatted = [_format_author(n) for n in names]
    if not formatted:
        return ""
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) > 20:
        formatted = formatted[:19] + ["..."] + [formatted[-1]]
        return ", ".join(formatted)
    return ", ".join(formatted[:-1]) + ", & " + formatted[-1]


def bibtex_key(fields: dict[str, Any]) -> str:
    authors = _split_authors(fields.get("authors"))
    surname = _surname(authors[0]) if authors else "anon"
    year = str(fields.get("year", "")).strip() or "nd"
    ascii_key = unicodedata.normalize("NFKD", f"{surname}{year}".lower()).encode("ascii", "ignore").decode()
    key = re.sub(r"[^a-z0-9]", "", ascii_key)
    return key or "ref"


def in_text_citation(fields: dict[str, Any]) -> str:
    authors = [_surname(a) for a in _split_authors(fields.get("authors"))]
    year = str(fields.get("year", "n.d.")).strip() or "n.d."
    if not authors:
        return f"(Anonymous, {year})"
    if len(authors) == 1:
        names = authors[0]
    elif len(authors) == 2:
        names = f"{authors[0]} & {authors[1]}"
    else:
        names = f"{authors[0]} et al."
    return f"({names}, {year})"


def _join(parts: list[str], sep: str = " ") -> str:
    return sep.join(p for p in parts if p)


def format_citation(fields: dict[str, Any], style: str = "apa") -> str:
    kind = str(fields.get("type", "article")).lower()
    authors = _join_authors(_split_authors(fields.get("authors")))
    year = str(fields.get("year", "n.d.")).strip() or "n.d."
    title = str(fields.get("title", "")).strip()
    doi = str(fields.get("doi", "")).strip()
    url = str(fields.get("url", "")).strip()
    link = f"https://doi.org/{doi}" if doi else url
    head = f"{authors} ({year})." if authors else f"({year})."

    publisher = str(fields.get("publisher", "")).strip()
    publisher_part = f"{publisher}." if publisher else ""

    if kind == "book":
        edition = str(fields.get("edition", "")).strip()
        ed = f" ({edition})" if edition else ""
        body = _join([f"*{title}*{ed}.", publisher_part])
        return _join([head, body, link])
    if kind in ("chapter", "incollection"):
        editors = str(fields.get("editors", "")).strip()
        container = str(fields.get("container", fields.get("booktitle", ""))).strip()
        pages = str(fields.get("pages", "")).strip()
        pp = f" (pp. {pages})" if pages else ""
        editor_part = f"In {editors} (Ed.), " if editors else ""
        body = _join([f"{title}.", f"{editor_part}*{container}*{pp}.", publisher_part])
        return _join([head, body, link])
    if kind in ("web", "misc"):
        site = str(fields.get("site", fields.get("publisher", ""))).strip()
        body = _join([f"*{title}*.", f"{site}." if site else ""])
        return _join([head, body, link])

    journal = str(fields.get("journal", fields.get("container", ""))).strip()
    volume = str(fields.get("volume", "")).strip()
    issue = str(fields.get("issue", "")).strip()
    pages = str(fields.get("pages", "")).strip()
    locator = f"*{journal}*" if journal else ""
    if volume:
        locator += f", *{volume}*"
        if issue:
            locator += f"({issue})"
    if pages:
        locator += f", {pages}"
    body = _join([f"{title}.", f"{locator}." if locator else ""])
    return _join([head, body, link])


def bibtex_entry(fields: dict[str, Any]) -> str:
    kind = _BIBTYPE.get(str(fields.get("type", "article")).lower(), "misc")
    key = str(fields.get("key", "")).strip() or bibtex_key(fields)
    rows: list[tuple[str, str]] = []
    authors = _split_authors(fields.get("authors"))
    if authors:
        rows.append(("author", " and ".join(authors)))
    mapping = {
        "title": "title",
        "year": "year",
        "journal": "journal",
        "container": "journal",
        "booktitle": "booktitle",
        "volume": "volume",
        "issue": "number",
        "pages": "pages",
        "publisher": "publisher",
        "doi": "doi",
        "url": "url",
        "site": "howpublished",
    }
    seen: set[str] = set()
    for source, target in mapping.items():
        value = str(fields.get(source, "")).strip()
        if value and target not in seen:
            rows.append((target, value))
            seen.add(target)
    lines = ",\n".join(f"  {name} = {{{value}}}" for name, value in rows)
    return f"@{kind}{{{key},\n{lines}\n}}"


def doi_to_bibtex(doi: str) -> str:
    clean = doi.strip().removeprefix("https://doi.org/").removeprefix("doi:").strip()
    request = urllib.request.Request(
        f"https://doi.org/{clean}",
        headers={"Accept": "application/x-bibtex; charset=utf-8", "User-Agent": "studykit"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", "replace").strip()
