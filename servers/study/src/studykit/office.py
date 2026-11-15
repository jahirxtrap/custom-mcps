"""What a Word or PowerPoint template offers: its texts to replace, its styles and its layouts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.util import Emu

from .deck import layouts_of
from .word import header_roots, texts_by_paragraph

_TEXT_BOX = qn("w:txbxContent")
_STYLE = f"{qn('w:pPr')}/{qn('w:pStyle')}"
_BODY_LIMIT = 80
_EMU_PER_CM = 360000


def _cm(value: Any) -> float:
    return round(Emu(int(value)) / _EMU_PER_CM, 2)


def _paragraph_texts(root: Any) -> list[dict[str, Any]]:
    found = []
    for paragraph, texts in texts_by_paragraph(root).items():
        text = "".join(node.text or "" for node in texts).strip()
        if not text:
            continue
        boxed = any(ancestor.tag == _TEXT_BOX for ancestor in paragraph.iterancestors())
        style = paragraph.find(_STYLE)
        found.append({"text": text, "style": style.get(qn("w:val")) if style is not None else None, "text_box": boxed})
    return found


def _inspect_docx(path: Path) -> dict[str, Any]:
    document = Document(str(path))
    sections = [
        {
            "page_cm": [_cm(section.page_width), _cm(section.page_height)],
            "margins_cm": {
                "top": _cm(section.top_margin),
                "bottom": _cm(section.bottom_margin),
                "left": _cm(section.left_margin),
                "right": _cm(section.right_margin),
            },
        }
        for section in document.sections
    ]
    headers: dict[str, list[str]] = {}
    for name, root in header_roots(document):
        texts = [item["text"] for item in _paragraph_texts(root)]
        if texts:
            headers.setdefault(name, []).extend(texts)
    body = _paragraph_texts(document.element.body)
    return {
        "kind": "docx",
        "sections": sections,
        "styles": {
            "paragraph": [style.name for style in document.styles if style.type == WD_STYLE_TYPE.PARAGRAPH],
            "table": [style.name for style in document.styles if style.type == WD_STYLE_TYPE.TABLE],
        },
        "headers_footers": headers,
        "body": body[:_BODY_LIMIT],
        "body_paragraphs": len(body),
        "text_boxes": [item["text"] for item in body if item["text_box"]],
        "tables": len(document.tables),
        "images": len(document.inline_shapes),
    }


def _inspect_pptx(path: Path) -> dict[str, Any]:
    presentation = Presentation(str(path))
    slides = []
    for index, slide in enumerate(presentation.slides):
        texts = [shape.text_frame.text.strip() for shape in slide.shapes if shape.has_text_frame]
        title = slide.shapes.title.text if slide.shapes.title is not None else ""
        layout = slide.slide_layout.name
        slides.append({"index": index, "layout": layout, "title": title, "texts": [text for text in texts if text]})
    return {
        "kind": "pptx",
        "slide_cm": [_cm(presentation.slide_width), _cm(presentation.slide_height)],
        "layouts": layouts_of(presentation),
        "slides": slides,
    }


def inspect_template(path: str) -> dict[str, Any]:
    target = Path(path)
    suffix = target.suffix.lower()
    if suffix == ".docx":
        return _inspect_docx(target)
    if suffix == ".pptx":
        return _inspect_pptx(target)
    raise ValueError(f"unsupported template '{target.name}'; use a .docx or a .pptx")
