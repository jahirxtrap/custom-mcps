"""Editable Word documents from a spec, written over a template handed out by an institution or from scratch."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

_PARAGRAPH = qn("w:p")
_TEXT = qn("w:t")
_TEXT_BOX = qn("w:txbxContent")
_PRESERVE = qn("xml:space")
_HEADING = {1: "Heading 1", 2: "Heading 2", 3: "Heading 3"}
_TITLE = "Title"
_BULLET = "List Bullet"
_NUMBER = "List Number"
_QUOTE = "Quote"
_CAPTION = "Caption"
_GRID = "Table Grid"
BLOCK_STYLES = (_TITLE, *_HEADING.values(), _BULLET, _NUMBER, _QUOTE, _CAPTION, _GRID)
TEXT_LIMIT = 160
_HANGING = Cm(1.27)
_QUOTE_INDENT = Cm(1.27)
_TOC_FIELD = 'TOC \\o "1-3" \\h \\z \\u'
_HEADER_PARTS = ("header", "footer", "first_page_header", "first_page_footer", "even_page_header", "even_page_footer")
_AFTER_UPDATE_FIELDS = {
    qn(name)
    for name in (
        "w:hdrShapeDefaults", "w:footnotePr", "w:endnotePr", "w:compat", "w:docVars", "w:rsids", "m:mathPr",
        "w:attachedSchema", "w:themeFontLang", "w:clrSchemeMapping", "w:doNotIncludeSubdocsInStats",
        "w:doNotAutoCompressPictures", "w:forceUpgrade", "w:captions", "w:readModeInkLockDown", "w:smartTagType",
        "w:shapeDefaults", "w:doNotEmbedSmartTags", "w:decimalSymbol", "w:listSeparator",
    )
}


def _paragraph_of(text_element: Any) -> Any:
    node = text_element.getparent()
    while node is not None and node.tag != _PARAGRAPH:
        node = node.getparent()
    return node


def texts_by_paragraph(root: Any) -> dict[Any, list[Any]]:
    grouped: dict[Any, list[Any]] = {}
    for text in root.iter(_TEXT):
        grouped.setdefault(_paragraph_of(text), []).append(text)
    return grouped


def substitution(replacements: dict[str, str]) -> re.Pattern[str] | None:
    keys = sorted((key for key in replacements if key), key=len, reverse=True)
    return re.compile("|".join(re.escape(key) for key in keys)) if keys else None


def _replace_in(texts: list[Any], pattern: re.Pattern[str], replacements: dict[str, str]) -> int:
    joined = "".join(text.text or "" for text in texts)
    found = len(pattern.findall(joined))
    if not found:
        return 0
    within = sum(len(pattern.findall(text.text or "")) for text in texts)
    if within == found:
        for text in texts:
            if pattern.search(text.text or ""):
                text.text = pattern.sub(lambda match: replacements[match.group(0)], text.text)
                text.set(_PRESERVE, "preserve")
        return found
    texts[0].text = pattern.sub(lambda match: replacements[match.group(0)], joined)
    texts[0].set(_PRESERVE, "preserve")
    for text in texts[1:]:
        text.text = ""
    return found


def header_roots(document: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    seen: set[int] = set()
    for section in document.sections:
        for name in _HEADER_PARTS:
            part = getattr(section, name)
            if part.is_linked_to_previous:
                continue
            root = part.part.element
            if id(root) not in seen:
                seen.add(id(root))
                found.append((name, root))
    return found


def _roots(document: Any) -> list[Any]:
    return [document.element.body, *(root for _, root in header_roots(document))]


def replace_text(document: Any, replacements: dict[str, str]) -> int:
    pattern = substitution(replacements)
    if pattern is None:
        return 0
    return sum(
        _replace_in(texts, pattern, replacements)
        for root in _roots(document)
        for texts in texts_by_paragraph(root).values()
    )


def _names(text: str, exact: set[str], prefixes: set[str]) -> bool:
    stripped = text.strip()
    return stripped in exact or any(stripped.startswith(prefix) for prefix in prefixes)


def remove_paragraphs(document: Any, texts: list[str]) -> int:
    exact = {text.strip() for text in texts if text.strip()}
    prefixes = {text for text in texts if len(text) >= TEXT_LIMIT}
    removed = 0
    for paragraph in list(document.paragraphs):
        if _names(paragraph.text, exact, prefixes):
            paragraph._element.getparent().remove(paragraph._element)
            removed += 1
    return removed


def _has_style(document: Any, name: str) -> bool:
    return any(style.name == name for style in document.styles)


def _apply_font(document: Any, font: dict[str, Any]) -> None:
    normal = document.styles["Normal"]
    name = font.get("name")
    if name:
        normal.font.name = str(name)
        normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), str(name))
    if font.get("size"):
        normal.font.size = Pt(float(font["size"]))
    if font.get("line_spacing"):
        normal.paragraph_format.line_spacing = float(font["line_spacing"])


def _apply_margins(document: Any, margins: dict[str, Any]) -> None:
    for section in document.sections:
        for side in ("top", "bottom", "left", "right"):
            if margins.get(side) is not None:
                setattr(section, f"{side}_margin", Cm(float(margins[side])))


def _heading(document: Any, text: str, level: int) -> None:
    style = _HEADING.get(max(1, min(level, 3)), _HEADING[3])
    if _has_style(document, style):
        document.add_paragraph(text, style=style)
        return
    run = document.add_paragraph().add_run(text)
    run.bold = True


def _list(document: Any, block: dict[str, Any]) -> None:
    style = _NUMBER if block.get("ordered") else _BULLET
    styled = _has_style(document, style)
    for index, item in enumerate(block.get("items", []), start=1):
        if styled:
            document.add_paragraph(str(item), style=style)
        else:
            marker = f"{index}. " if block.get("ordered") else "- "
            document.add_paragraph(f"{marker}{item}")


def _quote(document: Any, text: str) -> None:
    if _has_style(document, _QUOTE):
        document.add_paragraph(text, style=_QUOTE)
        return
    paragraph = document.add_paragraph(text)
    paragraph.paragraph_format.left_indent = _QUOTE_INDENT
    paragraph.paragraph_format.right_indent = _QUOTE_INDENT


def _caption(document: Any, text: str) -> None:
    if _has_style(document, _CAPTION):
        document.add_paragraph(text, style=_CAPTION)
    else:
        document.add_paragraph().add_run(text).italic = True


def _table(document: Any, block: dict[str, Any]) -> None:
    header = [str(cell) for cell in block.get("header", [])]
    rows = [[str(cell) for cell in row] for row in block.get("rows", [])]
    if not header and not rows:
        raise ValueError("a table block needs 'header' or 'rows'")
    columns = max(len(header), *(len(row) for row in rows)) if rows else len(header)
    if block.get("caption"):
        _caption(document, str(block["caption"]))
    table = document.add_table(rows=len(rows) + (1 if header else 0), cols=columns)
    if _has_style(document, _GRID):
        table.style = _GRID
    offset = 0
    if header:
        for index, text in enumerate(header):
            cell = table.cell(0, index)
            cell.text = ""
            cell.paragraphs[0].add_run(text).bold = True
        offset = 1
    for row_index, row in enumerate(rows):
        for column, text in enumerate(row):
            table.cell(row_index + offset, column).text = text
    document.add_paragraph()


def _usable_width(document: Any) -> Any:
    section = document.sections[-1]
    return section.page_width - section.left_margin - section.right_margin


def _image(document: Any, block: dict[str, Any]) -> None:
    width = Cm(float(block["width_cm"])) if block.get("width_cm") else _usable_width(document)
    document.add_picture(str(block["path"]), width=width)
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if block.get("caption"):
        _caption(document, str(block["caption"]))


def _references(document: Any, block: dict[str, Any]) -> None:
    _heading(document, str(block.get("title", "References")), 1)
    for item in block.get("items", []):
        paragraph = document.add_paragraph(str(item))
        paragraph.paragraph_format.left_indent = _HANGING
        paragraph.paragraph_format.first_line_indent = -_HANGING


def _field(paragraph: Paragraph, instruction: str, placeholder: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(_PRESERVE, "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, text, end):
        run._r.append(element)


def _update_fields_on_open(document: Any) -> None:
    settings = document.settings.element
    if settings.find(qn("w:updateFields")) is not None:
        return
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    later = [child for child in settings if child.tag in _AFTER_UPDATE_FIELDS]
    if later:
        later[0].addprevious(update)
    else:
        settings.append(update)


def _toc(document: Any, spec: dict[str, Any]) -> None:
    _heading(document, str(spec.get("toc_title", "Contents")), 1)
    placeholder = str(spec.get("toc_placeholder", "Update this field to build the table of contents."))
    _field(document.add_paragraph(), _TOC_FIELD, placeholder)
    _update_fields_on_open(document)
    document.add_page_break()


def _title_block(document: Any, spec: dict[str, Any]) -> None:
    title = str(spec.get("title", "")).strip()
    if not title:
        return
    if _has_style(document, _TITLE):
        document.add_paragraph(title, style=_TITLE).alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run(title).bold = True
    for key in ("subtitle", "author", "date"):
        value = str(spec.get(key, "")).strip()
        if value:
            document.add_paragraph(value).alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_page_break()


def render_docx(spec: dict[str, Any], out: Path) -> dict[str, Any]:
    template = spec.get("template")
    document = Document(str(template)) if template else Document()
    if spec.get("font"):
        _apply_font(document, dict(spec["font"]))
    if spec.get("margins_cm"):
        _apply_margins(document, dict(spec["margins_cm"]))
    replaced = replace_text(document, {str(k): str(v) for k, v in dict(spec.get("replace", {})).items()})
    removed = remove_paragraphs(document, [str(text) for text in spec.get("remove", [])])
    if not template:
        _title_block(document, spec)
    if spec.get("toc"):
        _toc(document, spec)
    blocks = spec.get("blocks", [])
    for block in blocks:
        kind = str(block.get("type", "text")).lower()
        if kind == "heading":
            _heading(document, str(block.get("text", "")), int(block.get("level", 1)))
        elif kind == "text":
            document.add_paragraph(str(block.get("text", "")))
        elif kind == "quote":
            _quote(document, str(block.get("text", "")))
        elif kind == "list":
            _list(document, block)
        elif kind == "table":
            _table(document, block)
        elif kind == "image":
            _image(document, block)
        elif kind == "references":
            _references(document, block)
        elif kind == "pagebreak":
            document.add_page_break()
        else:
            raise ValueError(f"unknown block type '{kind}'")
    document.save(str(out))
    return {
        "path": str(out),
        "format": "docx",
        "template": str(template) if template else None,
        "replaced": replaced,
        "removed": removed,
        "blocks": len(blocks),
        "paragraphs": len(document.paragraphs),
    }
