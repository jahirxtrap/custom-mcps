"""Editable PowerPoint decks from a spec, on the layouts of an institution's template or the default ones."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.oxml.ns import qn
from pptx.util import Inches

from .word import substitution

_WIDE = (Inches(13.333), Inches(7.5))
_RUN_TEXT = qn("a:t")
_PARAGRAPH = qn("a:p")
_ALIASES = {
    "cover": ("title slide",),
    "bullets": ("title and content",),
    "section": ("section header",),
    "two": ("two content", "comparison"),
    "image": ("picture with caption", "title only"),
    "table": ("title only", "title and content"),
    "closing": ("title slide", "section header"),
    "blank": ("blank",),
}
_TITLES = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE}
_BODIES = {PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT}
_CHROME = {PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.DATE}
_MARGIN = 0.05
_TOP = 0.22
_GAP = 0.03


def layouts_of(presentation: Any) -> list[dict[str, Any]]:
    described = []
    for index, layout in enumerate(presentation.slide_layouts):
        placeholders = [
            {"idx": shape.placeholder_format.idx, "type": shape.placeholder_format.type.name, "name": shape.name}
            for shape in layout.placeholders
        ]
        described.append({"index": index, "name": layout.name, "placeholders": placeholders})
    return described


def _layout(presentation: Any, wanted: Any) -> Any:
    layouts = list(presentation.slide_layouts)
    if isinstance(wanted, int) or (isinstance(wanted, str) and wanted.isdigit()):
        return layouts[int(wanted)]
    key = str(wanted).strip().lower()
    names = [layout.name.lower() for layout in layouts]
    for candidate in (key, *_ALIASES.get(key, ())):
        if candidate in names:
            return layouts[names.index(candidate)]
    for index, name in enumerate(names):
        if key and key in name:
            return layouts[index]
    raise ValueError(f"unknown layout '{wanted}'; this template has: {', '.join(layout.name for layout in layouts)}")


def _drop_slides(presentation: Any) -> int:
    ids = list(presentation.slides._sldIdLst)
    for slide_id in ids:
        presentation.part.drop_rel(slide_id.rId)
        presentation.slides._sldIdLst.remove(slide_id)
    return len(ids)


def _fill_body(frame: Any, slide: dict[str, Any]) -> None:
    items = slide.get("items", [])
    text = str(slide.get("text", "")).strip()
    frame.clear()
    first = True
    for item in items:
        level = int(item.get("level", 0)) if isinstance(item, dict) else 0
        body = str(item.get("text", "")) if isinstance(item, dict) else str(item)
        lead = str(item.get("lead", "")) if isinstance(item, dict) else ""
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        paragraph.level = level
        if lead:
            paragraph.add_run().text = lead + " "
            paragraph.runs[-1].font.bold = True
        paragraph.add_run().text = body
    if text:
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        paragraph.text = text


def _free_area(slide: Any, presentation: Any) -> tuple[int, int, int, int]:
    width, height = presentation.slide_width, presentation.slide_height
    title = slide.shapes.title
    top = title.top + title.height + int(height * _GAP) if title is not None else int(height * _TOP)
    return int(width * _MARGIN), top, int(width * (1 - 2 * _MARGIN)), int(height * (1 - _MARGIN)) - top


def _box(area: Any, slide: Any, presentation: Any) -> tuple[int, int, int, int]:
    if area is None:
        return _free_area(slide, presentation)
    return area.left, area.top, area.width, area.height


def _fill_table(slide: Any, slide_spec: dict[str, Any], box: tuple[int, int, int, int]) -> None:
    table_spec = slide_spec["table"]
    header = [str(cell) for cell in table_spec.get("header", [])]
    rows = [[str(cell) for cell in row] for row in table_spec.get("rows", [])]
    columns = max(len(header), *(len(row) for row in rows)) if rows else len(header)
    count = len(rows) + (1 if header else 0)
    graphic = slide.shapes.add_table(count, columns, *box)
    table = graphic.table
    offset = 0
    if header:
        for index, text in enumerate(header):
            table.cell(0, index).text = text
        offset = 1
    for row_index, row in enumerate(rows):
        for column, text in enumerate(row):
            table.cell(row_index + offset, column).text = text


def _remove(shape: Any) -> None:
    element = shape._element
    element.getparent().remove(element)


def _next_body(bodies: list[Any], used: set[int]) -> Any:
    return next((shape for shape in bodies if shape.placeholder_format.idx not in used), None)


def _take(area: Any, used: set[int]) -> None:
    if area is not None:
        used.add(area.placeholder_format.idx)
        _remove(area)


def _place_image(
    slide: Any, presentation: Any, slide_spec: dict[str, Any], picture: Any, bodies: list[Any], used: set[int]
) -> None:
    if picture is not None:
        used.add(picture.placeholder_format.idx)
        picture.insert_picture(str(slide_spec["image"]))
        return
    area = _next_body(bodies, used)
    left, top, _, height = _box(area, slide, presentation)
    slide.shapes.add_picture(str(slide_spec["image"]), left, top, height=height)
    _take(area, used)


def _place_table(
    slide: Any, presentation: Any, slide_spec: dict[str, Any], table: Any, bodies: list[Any], used: set[int]
) -> None:
    area = table if table is not None else _next_body(bodies, used)
    _fill_table(slide, slide_spec, _box(area, slide, presentation))
    _take(area, used)


def _build(presentation: Any, slide_spec: dict[str, Any]) -> str:
    layout = _layout(presentation, slide_spec.get("layout", "bullets"))
    slide = presentation.slides.add_slide(layout)
    used: set[int] = set()
    bodies: list[Any] = []
    picture = None
    table = None
    for shape in list(slide.placeholders):
        kind = shape.placeholder_format.type
        if kind in _TITLES and "title" in slide_spec:
            shape.text_frame.text = str(slide_spec["title"])
            used.add(shape.placeholder_format.idx)
        elif kind == PP_PLACEHOLDER.SUBTITLE and slide_spec.get("subtitle"):
            shape.text_frame.text = str(slide_spec["subtitle"])
            used.add(shape.placeholder_format.idx)
        elif kind == PP_PLACEHOLDER.PICTURE:
            picture = shape
        elif kind == PP_PLACEHOLDER.TABLE:
            table = shape
        elif kind in _BODIES:
            bodies.append(shape)
    if slide_spec.get("items") or slide_spec.get("text"):
        body = _next_body(bodies, used)
        if body is not None:
            _fill_body(body.text_frame, slide_spec)
            used.add(body.placeholder_format.idx)
    if slide_spec.get("image"):
        _place_image(slide, presentation, slide_spec, picture, bodies, used)
    if slide_spec.get("table"):
        _place_table(slide, presentation, slide_spec, table, bodies, used)
    for shape in list(slide.placeholders):
        if shape.placeholder_format.idx not in used and shape.placeholder_format.type not in _CHROME:
            _remove(shape)
    if slide_spec.get("notes"):
        slide.notes_slide.notes_text_frame.text = str(slide_spec["notes"])
    return layout.name


def replace_text(presentation: Any, replacements: dict[str, str]) -> int:
    pattern = substitution(replacements)
    if pattern is None:
        return 0
    found = 0
    for slide in presentation.slides:
        for paragraph in slide.element.iter(_PARAGRAPH):
            texts = list(paragraph.iter(_RUN_TEXT))
            joined = "".join(text.text or "" for text in texts)
            hits = len(pattern.findall(joined))
            if not hits:
                continue
            found += hits
            texts[0].text = pattern.sub(lambda match: replacements[match.group(0)], joined)
            for text in texts[1:]:
                text.text = ""
    return found


def render_pptx(spec: dict[str, Any], out: Path) -> dict[str, Any]:
    template = spec.get("template")
    presentation = Presentation(str(template)) if template else Presentation()
    dropped = 0
    if template and not spec.get("keep_slides", False):
        dropped = _drop_slides(presentation)
    if not template:
        presentation.slide_width, presentation.slide_height = _WIDE
    replaced = replace_text(presentation, {str(k): str(v) for k, v in dict(spec.get("replace", {})).items()})
    used = [_build(presentation, slide_spec) for slide_spec in spec.get("slides", [])]
    presentation.save(str(out))
    return {
        "path": str(out),
        "format": "pptx",
        "template": str(template) if template else None,
        "template_slides_dropped": dropped,
        "replaced": replaced,
        "slides": len(used),
        "layouts_used": used,
    }
