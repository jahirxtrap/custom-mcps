from __future__ import annotations

import pytest
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
from pptx import Presentation
from studykit import final_check, inspect_template, render_document, workspace_init, workspace_status
from studykit.grammar import HOME_VAR, URL_VAR


@pytest.fixture
def picture(tmp_path):
    path = tmp_path / "figure.png"
    Image.new("RGB", (320, 180), (30, 80, 150)).save(path)
    return path


@pytest.fixture
def word_template(tmp_path):
    document = Document()
    document.sections[0].header.paragraphs[0].text = "UNIVERSITY OF EXAMPLE"
    split = document.add_paragraph()
    split.add_run("STUDENT ")
    split.add_run("NAME")
    document.add_paragraph("COURSE")
    document.add_paragraph("Sample paragraph to drop.")
    run = document.add_paragraph("Cover: ").add_run()
    picture = OxmlElement("w:pict")
    box = OxmlElement("w:txbxContent")
    paragraph = OxmlElement("w:p")
    inner_run = OxmlElement("w:r")
    text = OxmlElement("w:t")
    text.text = "PROGRAM"
    inner_run.append(text)
    paragraph.append(inner_run)
    box.append(paragraph)
    picture.append(box)
    run._r.append(picture)
    path = tmp_path / "format.docx"
    document.save(path)
    return path


def test_docx_on_a_template_replaces_cover_texts_and_appends_content(tmp_path, word_template, picture):
    spec = {
        "format": "docx",
        "template": str(word_template),
        "replace": {
            "STUDENT NAME": "Ana Perez",
            "COURSE": "Didactics",
            "PROGRAM": "Pedagogy",
            "UNIVERSITY OF EXAMPLE": "UNIVERSITY X",
        },
        "remove": ["Sample paragraph to drop."],
        "toc": True,
        "font": {"name": "Times New Roman", "size": 12, "line_spacing": 2},
        "blocks": [
            {"type": "heading", "text": "Introduction", "level": 1},
            {"type": "text", "text": "First paragraph."},
            {"type": "quote", "text": "A quote."},
            {"type": "list", "items": ["one", "two"]},
            {"type": "list", "items": ["a", "b"], "ordered": True},
            {"type": "table", "header": ["A", "B"], "rows": [["1", "2"]], "caption": "Table 1. Test"},
            {"type": "image", "path": str(picture), "width_cm": 8, "caption": "Figure 1"},
            {"type": "pagebreak"},
            {"type": "references", "items": ["Author, A. (2020). Title. Publisher."]},
        ],
    }
    out = tmp_path / "work.docx"
    result = render_document(spec, out)
    assert (result["format"], result["replaced"], result["removed"], result["blocks"]) == ("docx", 4, 1, 9)

    report = inspect_template(str(out))
    texts = [item["text"] for item in report["body"]]
    assert texts[:4] == ["Ana Perez", "Didactics", "Cover:", "Pedagogy"]
    assert report["text_boxes"] == ["Pedagogy"]
    assert report["headers_footers"] == {"header": ["UNIVERSITY X"]}
    assert "Sample paragraph to drop." not in texts
    assert "Introduction" in texts and "First paragraph." in texts and "A quote." in texts
    assert (report["tables"], report["images"]) == (1, 1)
    assert "Heading 1" in report["styles"]["paragraph"] and "Table Grid" in report["styles"]["table"]

    document = Document(str(out))
    assert document.styles["Normal"].font.name == "Times New Roman"
    references = [p for p in document.paragraphs if p.text.startswith("Author, A.")]
    assert references[0].paragraph_format.first_line_indent < 0
    assert document.settings.element.find(qn("w:updateFields")) is not None


def test_docx_without_template_writes_a_title_block(tmp_path):
    out = tmp_path / "plain.docx"
    spec = {"format": "docx", "title": "My essay", "author": "Ana", "blocks": [{"type": "text", "text": "Body."}]}
    render_document(spec, out)
    texts = [item["text"] for item in inspect_template(str(out))["body"]]
    assert texts == ["My essay", "Ana", "Body."]


def test_docx_rejects_unknown_blocks(tmp_path):
    with pytest.raises(ValueError):
        render_document({"format": "docx", "blocks": [{"type": "video"}]}, tmp_path / "bad.docx")


def test_pptx_fills_layouts_by_alias_and_drops_empty_placeholders(tmp_path, picture):
    spec = {
        "format": "pptx",
        "slides": [
            {"layout": "cover", "title": "Title", "subtitle": "Sub"},
            {
                "layout": "bullets",
                "title": "Points",
                "items": ["one", {"lead": "Two.", "text": "detail", "level": 1}],
                "notes": "say this",
            },
            {"layout": "image", "title": "Figure", "image": str(picture)},
            {"layout": "table", "title": "Table", "table": {"header": ["A", "B"], "rows": [["1", "2"]]}},
            {"layout": "two", "title": "Both", "items": ["x"], "image": str(picture)},
        ],
    }
    out = tmp_path / "deck.pptx"
    result = render_document(spec, out)
    assert result["slides"] == 5 and result["layouts_used"][0] == "Title Slide"

    report = inspect_template(str(out))
    assert report["slide_cm"] == [33.87, 19.05]
    assert [slide["title"] for slide in report["slides"]] == ["Title", "Points", "Figure", "Table", "Both"]
    assert report["slides"][1]["texts"] == ["Points", "one\nTwo. detail"]
    presentation = Presentation(str(out))
    assert presentation.slides[1].notes_slide.notes_text_frame.text == "say this"
    frames = [shape.text_frame.text for slide in presentation.slides for shape in slide.shapes if shape.has_text_frame]
    assert not any("Click to add" in text for text in frames)
    assert any(getattr(shape, "image", None) is not None for shape in presentation.slides[2].shapes)
    assert any(shape.has_table for shape in presentation.slides[3].shapes)
    assert any(getattr(shape, "image", None) is not None for shape in presentation.slides[4].shapes)


def test_pptx_on_a_template_keeps_or_drops_its_slides(tmp_path):
    base = tmp_path / "format.pptx"
    sample = {"format": "pptx", "slides": [{"layout": "cover", "title": "INSTITUTION", "subtitle": "Sample"}]}
    render_document(sample, base)

    kept = render_document(
        {"format": "pptx", "template": str(base), "keep_slides": True, "replace": {"INSTITUTION": "My School"},
         "slides": [{"layout": "Title Only", "title": "Extra"}]},
        tmp_path / "kept.pptx",
    )
    assert (kept["template_slides_dropped"], kept["replaced"], kept["slides"]) == (0, 1, 1)
    report = inspect_template(str(tmp_path / "kept.pptx"))
    assert [slide["title"] for slide in report["slides"]] == ["My School", "Extra"]

    only = {"format": "pptx", "template": str(base), "slides": [{"layout": 1, "title": "Only"}]}
    dropped = render_document(only, tmp_path / "dropped.pptx")
    assert dropped["template_slides_dropped"] == 1
    assert [slide["title"] for slide in inspect_template(str(tmp_path / "dropped.pptx"))["slides"]] == ["Only"]


def test_pptx_names_the_available_layouts_on_a_miss(tmp_path):
    with pytest.raises(ValueError, match="Title Slide"):
        render_document({"format": "pptx", "slides": [{"layout": "nonexistent", "title": "x"}]}, tmp_path / "bad.pptx")


def test_template_inspect_rejects_other_files(tmp_path):
    other = tmp_path / "notes.txt"
    other.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        inspect_template(str(other))


def test_final_check_bundles_the_three_checks(monkeypatch):
    monkeypatch.delenv(URL_VAR, raising=False)
    monkeypatch.delenv(HOME_VAR, raising=False)
    monkeypatch.setattr("studykit.grammar.shutil.which", lambda name: None)
    report = final_check("It is important to note that we delve into it. Short.", "en-US")
    assert set(report) == {"summary", "writing", "burstiness", "grammar"}
    assert report["writing"]["score"] < 100 and report["grammar"]["available"] is False
    assert report["summary"].startswith("writing ") and "grammar not checked" in report["summary"]


def test_workspace_status_lists_what_the_workspace_really_holds(tmp_path):
    workspace_init(str(tmp_path), ["Physics"])
    (tmp_path / "tools" / "cover.py").write_text('"""Cover page with the institution banner."""\n', encoding="utf-8")
    (tmp_path / "templates" / "format.docx").write_bytes(b"x")
    (tmp_path / "memory" / "works" / "2026-11-15-essay.md").write_text(
        "---\ndate: 2026-11-15\narea: physics\nkind: essay\nformat: docx\nstatus: delivered\n"
        "files:\n  - areas/physics/out/essay.docx\n---\nbrief\n",
        encoding="utf-8",
    )
    area = tmp_path / "areas" / "physics"
    (area / "documents" / "essay").mkdir(parents=True)
    (area / "documents" / "essay" / "build.py").write_text("", encoding="utf-8")
    (area / "slides" / "talk").mkdir(parents=True)
    (area / "out").mkdir()
    (area / "out" / "essay.docx").write_bytes(b"")
    (area / "out" / "talk.pptx").write_bytes(b"")

    status = workspace_status(str(tmp_path))
    assert status["tools"] == [{"module": "cover", "does": "Cover page with the institution banner."}]
    templates = {"docx": ["format.docx"], "json": ["concept-map-example.json"], "tex": ["paper-apa7.tex"]}
    assert status["templates"] == templates
    assert status["works"] == {"count": 1, "by_status": {"delivered": 1}}
    physics = status["areas"][0]
    assert physics["works"] == {"documents": ["essay"], "slides": ["talk"]}
    assert (physics["scripts"], physics["deliverables"]) == (1, {"docx": 1, "pptx": 1})
    assert (tmp_path / "tools" / "README.md").exists() and (tmp_path / "memory" / "works" / "README.md").exists()
