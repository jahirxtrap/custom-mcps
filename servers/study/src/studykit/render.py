"""Typeset a declarative spec into a professional PDF: a report document or a slide deck."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

DEFAULT_PALETTE = {
    "primary": "#23404f",
    "accent": "#c2703d",
    "ink": "#23282d",
    "paper": "#fbfaf7",
}
_MUTED = colors.HexColor("#8b8578")
_RULE = colors.HexColor("#d5cfc2")
_LIGHT = colors.HexColor("#f4f1ea")
_FONTS = {
    "serif": ("Times-Roman", "Times-Bold", "Times-Italic"),
    "sans": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique"),
}
_PAGES = {"a4": A4, "letter": LETTER}
_SLIDE = (960, 540)


def _palette(spec: dict[str, Any]) -> dict[str, colors.Color]:
    values = {**DEFAULT_PALETTE, **(spec.get("palette") or {})}
    return {name: colors.HexColor(value) for name, value in values.items()}


def _fonts(spec: dict[str, Any]) -> tuple[str, str, str]:
    return _FONTS.get(str(spec.get("font", "serif")).lower(), _FONTS["serif"])


def _chart(block: dict[str, Any], palette: dict[str, colors.Color], fonts: tuple[str, str, str],
           width: float, height: float) -> Drawing:
    regular, bold, italic = fonts
    kind = str(block.get("kind", "bar")).lower()
    categories = [str(c) for c in block.get("categories", [])]
    values = [float(v) for v in block.get("values", [])]
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=palette["paper"], strokeColor=_RULE, strokeWidth=0.5))
    title = str(block.get("title", "")).strip()
    top = height - 22 if title else height - 8
    if title:
        drawing.add(String(24, height - 20, title, fontName=bold, fontSize=10, fillColor=palette["primary"]))
    plot_x, plot_y = 52, 34
    plot_w, plot_h = width - plot_x - 24, top - plot_y - 10

    if kind == "pie":
        pie = Pie()
        pie.x, pie.y = width / 2 - plot_h / 2, plot_y
        pie.width = pie.height = plot_h
        pie.data = values
        pie.labels = categories
        pie.slices.strokeColor = colors.white
        pie.slices.strokeWidth = 1.5
        pie.slices.fontName = regular
        pie.slices.fontSize = 8
        shades = [palette["primary"], palette["accent"], _MUTED, _RULE, palette["ink"]]
        for index in range(len(values)):
            pie.slices[index].fillColor = shades[index % len(shades)]
        drawing.add(pie)
        return drawing

    chart = HorizontalLineChart() if kind == "line" else VerticalBarChart()
    chart.x, chart.y = plot_x, plot_y
    chart.width, chart.height = plot_w, plot_h
    chart.data = [values]
    chart.categoryAxis.categoryNames = categories
    chart.categoryAxis.labels.fontName = regular
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.dy = -6
    chart.valueAxis.valueMin = 0
    top_value = max(values) if values else 1
    chart.valueAxis.valueMax = float(block.get("max", top_value * 1.15))
    chart.valueAxis.labels.fontName = regular
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.strokeColor = _RULE
    if kind == "line":
        chart.lines[0].strokeColor = palette["primary"]
        chart.lines[0].strokeWidth = 2
    else:
        chart.bars[0].fillColor = palette["primary"]
        chart.bars.strokeColor = None
        chart.barWidth = plot_w / max(1, len(values)) * 0.28
        chart.groupSpacing = plot_w / max(1, len(values)) * 0.5
        chart.barLabels.fontName = bold
        chart.barLabels.fontSize = 8
        chart.barLabelFormat = str(block.get("label_format", "%0.1f"))
        chart.barLabels.dy = 7
        chart.barLabels.fillColor = palette["ink"]
    drawing.add(chart)

    threshold = block.get("threshold")
    if threshold is not None:
        span = chart.valueAxis.valueMax or 1
        y = plot_y + plot_h * float(threshold) / span
        drawing.add(Line(plot_x, y, plot_x + plot_w, y, strokeColor=palette["accent"],
                         strokeDashArray=[3, 3], strokeWidth=0.8))
        drawing.add(String(plot_x + plot_w - 4, y + 4, str(block.get("threshold_label", threshold)),
                           fontName=italic, fontSize=7, fillColor=palette["accent"], textAnchor="end"))
    return drawing


def _table(block: dict[str, Any], palette: dict[str, colors.Color], fonts: tuple[str, str, str],
           total_width: float) -> Table:
    regular, bold, _ = fonts
    header = [str(cell) for cell in block.get("header", [])]
    rows = [[str(cell) for cell in row] for row in block.get("rows", [])]
    data = ([header] if header else []) + rows
    if not data:
        raise ValueError("a table block needs 'header' or 'rows'")
    count = len(data[0])
    weights = block.get("widths") or [1.6] + [1.0] * (count - 1)
    scale = total_width / sum(weights)
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), regular),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, _RULE),
    ]
    first = 0
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), palette["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), _LIGHT),
            ("FONTNAME", (0, 0), (-1, 0), bold),
        ]
        first = 1
    commands += [
        ("ROWBACKGROUNDS", (0, first), (-1, -1), [colors.white, _LIGHT]),
        ("LINEBELOW", (0, -1), (-1, -1), 1.1, palette["primary"]),
    ]
    highlight = block.get("highlight")
    if highlight is not None:
        index = int(highlight) + first
        commands += [("FONTNAME", (0, index), (-1, index), bold),
                     ("TEXTCOLOR", (0, index), (-1, index), palette["accent"])]
    table = Table(data, colWidths=[w * scale for w in weights], hAlign="LEFT")
    table.setStyle(TableStyle(commands))
    return table


class _Report(BaseDocTemplate):
    def __init__(self, path: str, spec: dict[str, Any], palette: dict[str, colors.Color],
                 fonts: tuple[str, str, str]):
        page = _PAGES.get(str(spec.get("page", "a4")).lower(), A4)
        super().__init__(path, pagesize=page, title=str(spec.get("title", "Document")),
                         author=str(spec.get("author", "")))
        self.spec = spec
        self.palette = palette
        self.fonts = fonts
        self.width_available = page[0] - 4.4 * cm
        margin_bottom, margin_top = 2.1 * cm, 4.1 * cm
        full = Frame(2.2 * cm, margin_bottom, self.width_available, page[1] - margin_top, id="full")
        gap = 0.8 * cm
        col = (self.width_available - gap) / 2
        left = Frame(2.2 * cm, margin_bottom, col, page[1] - margin_top, id="left")
        right = Frame(2.2 * cm + col + gap, margin_bottom, col, page[1] - margin_top, id="right")
        cover_frame = Frame(2.5 * cm, 2.5 * cm, page[0] - 5 * cm, 6.5 * cm, id="cover")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=self._cover),
            PageTemplate(id="body", frames=[full], onPage=self._body),
            PageTemplate(id="two", frames=[left, right], onPage=self._body),
        ])
        self._h1 = 0
        self._h2 = 0
        self._seen_h1 = False

    def beforeDocument(self) -> None:
        self._h1 = 0
        self._h2 = 0
        self._seen_h1 = False

    def _cover(self, canvas, doc) -> None:
        regular, bold, italic = self.fonts
        width, height = self.pagesize
        canvas.saveState()
        canvas.setFillColor(self.palette["primary"])
        canvas.rect(0, height - 12.4 * cm, width, 12.4 * cm, stroke=0, fill=1)
        canvas.setFillColor(self.palette["accent"])
        canvas.rect(0, height - 12.7 * cm, width, 0.3 * cm, stroke=0, fill=1)
        canvas.setFillColor(_LIGHT)
        canvas.setFont(bold, 28)
        canvas.drawString(2.5 * cm, height - 6.6 * cm, str(self.spec.get("title", "")))
        subtitle = str(self.spec.get("subtitle", "")).strip()
        if subtitle:
            canvas.setFont(italic, 13)
            canvas.setFillColor(colors.HexColor("#b9c7d0"))
            canvas.drawString(2.5 * cm, height - 7.7 * cm, subtitle)
        canvas.setFont(regular, 10.5)
        canvas.setFillColor(_MUTED)
        footer = [str(self.spec.get(key, "")).strip() for key in ("author", "affiliation", "date")]
        y = 3.4 * cm
        for line in [item for item in footer if item]:
            canvas.drawString(2.5 * cm, y, line)
            y -= 0.6 * cm
        canvas.setStrokeColor(_RULE)
        canvas.line(2.5 * cm, 4.2 * cm, width - 2.5 * cm, 4.2 * cm)
        canvas.restoreState()

    def _body(self, canvas, doc) -> None:
        regular, bold, italic = self.fonts
        width, height = self.pagesize
        mark = str(self.spec.get("watermark", "")).strip()
        if mark:
            canvas.saveState()
            canvas.setFont(bold, 62)
            canvas.setFillColor(colors.Color(0.55, 0.58, 0.60, alpha=0.07))
            canvas.translate(width / 2, height / 2)
            canvas.rotate(52)
            canvas.drawCentredString(0, 0, mark)
            canvas.restoreState()
        canvas.saveState()
        canvas.setFont(italic, 8.5)
        canvas.setFillColor(_MUTED)
        canvas.drawString(2.2 * cm, height - 1.55 * cm, str(self.spec.get("title", "")))
        canvas.setStrokeColor(_RULE)
        canvas.setLineWidth(0.5)
        canvas.line(2.2 * cm, height - 1.75 * cm, width - 2.2 * cm, height - 1.75 * cm)
        canvas.line(2.2 * cm, 1.85 * cm, width - 2.2 * cm, 1.85 * cm)
        canvas.restoreState()

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        name = flowable.style.name
        text = flowable.getPlainText()
        if name == "DocH1":
            self._h1 += 1
            self._seen_h1 = True
            key = f"h1-{self._h1}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, 0, 0)
            self.notify("TOCEntry", (0, text, self.page, key))
        elif name == "DocH2" and self._seen_h1:
            self._h2 += 1
            key = f"h2-{self._h2}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, 1, 0)
            self.notify("TOCEntry", (1, text, self.page, key))


def _numbered_canvas(fonts: tuple[str, str, str], enabled: bool, label: str):
    regular = fonts[0]

    class Numbered(pdfcanvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._states: list[dict[str, Any]] = []

        def showPage(self):
            self._states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._states)
            for state in self._states:
                self.__dict__.update(state)
                if enabled and self._pageNumber > 1:
                    self.setFont(regular, 8.5)
                    self.setFillColor(_MUTED)
                    self.drawCentredString(self._pagesize[0] / 2, 1.35 * cm,
                                           label.format(page=self._pageNumber, total=total))
                super().showPage()
            super().save()

    return Numbered


def _report_styles(palette: dict[str, colors.Color], fonts: tuple[str, str, str]) -> dict[str, ParagraphStyle]:
    regular, bold, italic = fonts
    sample = getSampleStyleSheet()
    body = ParagraphStyle("DocBody", parent=sample["BodyText"], fontName=regular, fontSize=10.5,
                          leading=16, alignment=TA_JUSTIFY, spaceAfter=10, textColor=palette["ink"])
    return {
        "body": body,
        "h1": ParagraphStyle("DocH1", parent=body, fontName=bold, fontSize=17, leading=21,
                             alignment=0, textColor=palette["primary"], spaceBefore=18, spaceAfter=10),
        "h2": ParagraphStyle("DocH2", parent=body, fontName=bold, fontSize=12.5, leading=16,
                             alignment=0, textColor=palette["accent"], spaceBefore=12, spaceAfter=6),
        "quote": ParagraphStyle("DocQuote", parent=body, fontName=italic, fontSize=12, leading=18,
                                textColor=palette["primary"], leftIndent=1 * cm, rightIndent=1 * cm,
                                spaceBefore=8, spaceAfter=12),
        "caption": ParagraphStyle("DocCaption", parent=body, fontSize=8.5, leading=12,
                                  textColor=_MUTED, alignment=TA_CENTER, spaceBefore=4),
        "abstract": ParagraphStyle("DocAbstract", parent=body, fontSize=9.5, leading=14,
                                   leftIndent=0.8 * cm, rightIndent=0.8 * cm),
        "abstract_head": ParagraphStyle("DocAbstractHead", parent=body, fontName=bold, fontSize=12.5,
                                        leading=16, alignment=0, textColor=palette["accent"],
                                        spaceAfter=6),
        "reference": ParagraphStyle("DocReference", parent=body, fontSize=9.5, leading=14,
                                    leftIndent=1 * cm, firstLineIndent=-1 * cm, spaceAfter=8),
        "bullet": ParagraphStyle("DocBullet", parent=body, leftIndent=0.7 * cm, bulletIndent=0.2 * cm,
                                 spaceAfter=5),
    }


def _report(spec: dict[str, Any], out: Path) -> dict[str, Any]:
    palette = _palette(spec)
    fonts = _fonts(spec)
    doc = _Report(str(out), spec, palette, fonts)
    styles = _report_styles(palette, fonts)
    story: list[Any] = []

    abstract = str(spec.get("abstract", "")).strip()
    if abstract:
        story += [Paragraph(str(spec.get("abstract_title", "Abstract")), styles["abstract_head"]),
                  Paragraph(abstract, styles["abstract"])]
    story += [NextPageTemplate("body"), PageBreak()]
    if spec.get("toc", True):
        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle("TOC1", fontName=fonts[1], fontSize=11, leading=18, textColor=palette["primary"]),
            ParagraphStyle("TOC2", fontName=fonts[0], fontSize=10, leading=15, leftIndent=0.8 * cm,
                           textColor=palette["ink"]),
        ]
        story += [Paragraph(str(spec.get("toc_title", "Contents")), styles["h1"]), toc, PageBreak()]

    columns = "body"
    for block in spec.get("blocks", []):
        kind = str(block.get("type", "text")).lower()
        if kind == "heading":
            level = int(block.get("level", 1))
            story.append(Paragraph(str(block.get("text", "")), styles["h1" if level <= 1 else "h2"]))
        elif kind == "text":
            story.append(Paragraph(str(block.get("text", "")), styles["body"]))
        elif kind == "quote":
            story.append(Paragraph(str(block.get("text", "")), styles["quote"]))
        elif kind == "list":
            for item in block.get("items", []):
                story.append(Paragraph(str(item), styles["bullet"], bulletText="–"))
            story.append(Spacer(1, 6))
        elif kind == "table":
            width = doc.width_available if columns == "body" else (doc.width_available - 0.8 * cm) / 2
            parts: list[Any] = [_table(block, palette, fonts, width)]
            if block.get("caption"):
                parts.append(Paragraph(str(block["caption"]), styles["caption"]))
            story.append(KeepTogether(parts))
            story.append(Spacer(1, 8))
        elif kind == "chart":
            width = doc.width_available if columns == "body" else (doc.width_available - 0.8 * cm) / 2
            parts = [_chart(block, palette, fonts, width, float(block.get("height", 190)))]
            if block.get("caption"):
                parts.append(Paragraph(str(block["caption"]), styles["caption"]))
            story.append(KeepTogether(parts))
            story.append(Spacer(1, 8))
        elif kind == "references":
            story.append(Paragraph(str(block.get("title", "References")), styles["h1"]))
            for item in block.get("items", []):
                story.append(Paragraph(str(item), styles["reference"]))
        elif kind == "columns":
            columns = "two" if int(block.get("count", 1)) > 1 else "body"
            story += [NextPageTemplate(columns), PageBreak()]
        elif kind == "pagebreak":
            story.append(PageBreak())
        else:
            raise ValueError(f"unknown block type '{kind}'")

    numbering = spec.get("page_numbers", True)
    label = str(spec.get("page_label", "{page} / {total}"))
    doc.multiBuild(story, canvasmaker=_numbered_canvas(fonts, bool(numbering), label))
    return {"path": str(out), "format": "report", "pages": doc.page, "blocks": len(spec.get("blocks", []))}


class _Deck:
    def __init__(self, path: Path, spec: dict[str, Any], palette: dict[str, colors.Color],
                 fonts: tuple[str, str, str]):
        self.spec = spec
        self.palette = palette
        self.fonts = fonts
        self.width, self.height = _SLIDE
        self.canvas = pdfcanvas.Canvas(str(path), pagesize=_SLIDE)
        self.canvas.setTitle(str(spec.get("title", "Slides")))
        self.footer = str(spec.get("title", ""))
        self.progress = bool(spec.get("progress", True))
        self.stop = 0
        self.total = max(1, sum(1 for s in spec.get("slides", [])
                                if str(s.get("layout", "bullets")).lower() != "cover"))
        self.pages = 0

    def _chrome(self) -> None:
        regular, _, italic = self.fonts
        canvas = self.canvas
        canvas.setFillColor(self.palette["paper"])
        canvas.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        canvas.setFillColor(self.palette["accent"])
        canvas.rect(0, self.height - 8, self.width, 8, stroke=0, fill=1)
        canvas.setFont(italic, 11)
        canvas.setFillColor(_MUTED)
        canvas.drawString(60, 30, self.footer)
        canvas.setFont(regular, 11)
        canvas.drawRightString(self.width - 60, 30, f"{self.stop} / {self.total}")
        if self.progress:
            canvas.setFillColor(_RULE)
            canvas.rect(60, 52, self.width - 120, 3, stroke=0, fill=1)
            canvas.setFillColor(self.palette["primary"])
            canvas.rect(60, 52, (self.width - 120) * self.stop / self.total, 3, stroke=0, fill=1)

    def _heading(self, text: str) -> None:
        _, bold, _ = self.fonts
        canvas = self.canvas
        canvas.setFont(bold, 34)
        canvas.setFillColor(self.palette["primary"])
        canvas.drawString(60, self.height - 110, text)
        canvas.setStrokeColor(self.palette["accent"])
        canvas.setLineWidth(3)
        canvas.line(60, self.height - 128, 60 + canvas.stringWidth(text, bold, 34), self.height - 128)

    def _emit(self) -> None:
        self.canvas.showPage()
        self.pages += 1

    def _panel(self, slide: dict[str, Any], title_size: int) -> None:
        regular, bold, italic = self.fonts
        canvas = self.canvas
        canvas.setFillColor(self.palette["primary"])
        canvas.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        canvas.setFillColor(self.palette["accent"])
        canvas.rect(60, self.height - 150, 96, 5, stroke=0, fill=1)
        canvas.setFillColor(_LIGHT)
        canvas.setFont(bold, title_size)
        canvas.drawString(60, self.height - 120, str(slide.get("title", "")))
        subtitle = str(slide.get("subtitle", "")).strip()
        if subtitle:
            canvas.setFont(italic, 19)
            canvas.setFillColor(colors.HexColor("#b9c7d0"))
            canvas.drawString(60, self.height - 175, subtitle)
        y = self.height - 235
        canvas.setFont(regular, 15)
        for line in slide.get("lines", []):
            canvas.setFillColor(colors.HexColor("#cfd9e0"))
            canvas.drawString(60, y, str(line))
            y -= 32

    def cover(self, slide: dict[str, Any]) -> None:
        self._panel(slide, 44)
        self._emit()

    def closing(self, slide: dict[str, Any]) -> None:
        self.stop += 1
        self._panel(slide, 36)
        self._emit()

    def bullets(self, slide: dict[str, Any]) -> None:
        self.stop += 1
        regular, bold, _ = self.fonts
        items = []
        for item in slide.get("items", []):
            if isinstance(item, dict):
                items.append((str(item.get("lead", "")), str(item.get("text", item.get("rest", "")))))
            else:
                items.append(("", str(item)))
        steps = range(1, len(items) + 1) if slide.get("reveal") else [len(items)]
        canvas = self.canvas
        for count in steps:
            self._chrome()
            self._heading(str(slide.get("title", "")))
            y = self.height - 200
            for index, (lead, rest) in enumerate(items):
                active = index < count
                canvas.setFillColor(self.palette["primary"] if active else colors.HexColor("#e6e2d9"))
                canvas.circle(74, y + 7, 5, stroke=0, fill=1)
                x = 96
                if lead:
                    canvas.setFont(bold, 20)
                    canvas.setFillColor(self.palette["ink"] if active else colors.HexColor("#e6e2d9"))
                    canvas.drawString(x, y, lead)
                    x += canvas.stringWidth(lead + " ", bold, 20)
                canvas.setFont(regular, 20)
                canvas.setFillColor(colors.HexColor("#4a5157") if active else colors.HexColor("#ece9e1"))
                canvas.drawString(x, y, rest)
                y -= 62
            self._emit()

    def table(self, slide: dict[str, Any]) -> None:
        self.stop += 1
        self._chrome()
        self._heading(str(slide.get("title", "")))
        table = _table(slide, self.palette, self.fonts, self.width - 120)
        table.wrapOn(self.canvas, self.width - 120, self.height)
        table.drawOn(self.canvas, 60, self.height - 200 - table._height)
        note = str(slide.get("note", "")).strip()
        if note:
            self.canvas.setFont(self.fonts[2], 13)
            self.canvas.setFillColor(_MUTED)
            self.canvas.drawString(60, self.height - 230 - table._height, note)
        self._emit()

    def chart(self, slide: dict[str, Any]) -> None:
        self.stop += 1
        self._chrome()
        self._heading(str(slide.get("title", "")))
        drawing = _chart(slide, self.palette, self.fonts, self.width - 220, 300)
        renderPDF.draw(drawing, self.canvas, 110, 90)
        self._emit()

    def save(self) -> None:
        self.canvas.save()


def _slides(spec: dict[str, Any], out: Path) -> dict[str, Any]:
    deck = _Deck(out, spec, _palette(spec), _fonts(spec))
    layouts = {"cover": deck.cover, "closing": deck.closing, "bullets": deck.bullets,
               "table": deck.table, "chart": deck.chart}
    for slide in spec.get("slides", []):
        layout = str(slide.get("layout", "bullets")).lower()
        if layout not in layouts:
            raise ValueError(f"unknown slide layout '{layout}'")
        layouts[layout](slide)
    deck.save()
    return {"path": str(out), "format": "slides", "pages": deck.pages, "slides": len(spec.get("slides", []))}


def render_document(spec: dict[str, Any], out: str | Path) -> dict[str, Any]:
    """Typeset a spec into a PDF. format='report' (document) or 'slides' (16:9 deck)."""
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    fmt = str(spec.get("format", "report")).lower()
    if fmt == "slides":
        return _slides(spec, target)
    if fmt in ("report", "document"):
        return _report(spec, target)
    raise ValueError(f"unknown format '{fmt}'; use 'report' or 'slides'")
