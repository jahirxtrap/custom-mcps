from __future__ import annotations

import io
import json
import subprocess
import urllib.error
from pathlib import Path

import pytest
from studykit import (
    area_add,
    bibtex_entry,
    bibtex_key,
    burstiness,
    check_links,
    extract_urls,
    format_citation,
    grammar,
    grammar_check,
    image_search,
    in_text_citation,
    links,
    normalize_extracted,
    reference_add,
    render_concept_map,
    render_document,
    study_guide,
    toolkit,
    workspace,
    workspace_init,
    workspace_status,
    writing_check,
)
from studykit.grammar import HOME_VAR, URL_VAR, backend, hits
from studykit.markdown import plain_text


def test_writing_check_detects_spanish_with_accents():
    report = writing_check("Es importante señalar que conviene profundizar en el tema actual.")
    assert report["categories"]["filler"]["count"] >= 2
    assert report["score"] < 100


def test_writing_check_detects_english_and_em_dash():
    report = writing_check("It's important to note that we delve into the topic — really.")
    cats = report["categories"]
    assert "filler" in cats
    assert "em_dash" in cats
    assert report["total_hits"] >= 2


def test_writing_check_negative_parallelism_and_meta():
    report = writing_check("As an AI language model, it is not just fast but reliable.")
    assert "meta_commentary" in report["categories"]
    assert "negative_parallelism" in report["categories"]


def test_writing_check_sees_repeated_openings_in_any_language():
    report = writing_check(
        "La estadística descriptiva organiza los datos.\nLa estadística descriptiva resume la información. "
        "La estadística descriptiva presenta los resultados. Luego viene otra cosa. Luego sigue."
    )
    hits = report["categories"]["repeated_openings"]
    assert hits["count"] == 1
    assert hits["hits"][0] == {"match": "La estadística x3", "line": 1}
    assert report["score"] < 100
    assert "repeated_openings" not in writing_check("The study grew. The study ended.")["categories"]


def test_writing_check_knows_the_cabe_family_and_history_openers():
    report = writing_check(
        "Cabe mencionar que el tema importa. Cabe señalar que hay matices. Cabe recalcar que la fuente es "
        "oficial. A lo largo de la historia el deporte cambió. It is worth mentioning this throughout history."
    )
    assert report["categories"]["filler"]["count"] == 6


def test_writing_check_clean_text_scores_high():
    report = writing_check("The river rose at dawn. Birds left the reeds. We waited by the old bridge.")
    assert report["score"] == 100
    assert report["categories"] == {}


def test_burstiness_uniform_vs_varied():
    uniform = burstiness("Cats run fast here. Dogs jump high now. Birds fly far away.")
    varied = burstiness("It rained. The long, winding road climbed past the silent hills toward dusk. Stop.")
    assert uniform["score"] <= varied["score"]
    assert "label" in uniform


def test_format_citation_article_and_in_text():
    fields = {
        "type": "article",
        "authors": ["Smith, John", "Lee, Ana"],
        "year": 2020,
        "title": "On something",
        "journal": "Journal of Things",
        "volume": 3,
        "issue": 2,
        "pages": "10-20",
        "doi": "10.1/x",
    }
    apa = format_citation(fields)
    assert "Smith, J." in apa
    assert "(2020)" in apa
    assert "https://doi.org/10.1/x" in apa
    assert in_text_citation(fields) == "(Smith & Lee, 2020)"


def test_format_citation_book():
    fields = {"type": "book", "authors": ["Doe, Jane"], "year": 2019, "title": "A Book", "publisher": "Press"}
    apa = format_citation(fields)
    assert "*A Book*" in apa
    assert "Press." in apa


def test_bibtex_entry_and_key():
    fields = {"type": "article", "authors": ["García, Ana"], "year": 2021, "title": "Algo", "journal": "Rev"}
    assert bibtex_key(fields) == "garcia2021"
    entry = bibtex_entry(fields)
    assert entry.startswith("@article{garcia2021,")
    assert "author = {García, Ana}" in entry


def test_concept_map_renders_image():
    spec = {
        "central": "Photosynthesis",
        "branches": [
            {"label": "Inputs", "items": ["Light", "Water", {"label": "Gas", "text": "CO2"}]},
            {"label": "Outputs", "items": ["Glucose", "Oxygen"]},
        ],
    }
    image = render_concept_map(spec)
    assert image.width > 100
    assert image.height > 100


def test_concept_map_font_renders_accents():
    from PIL import Image, ImageDraw
    from studykit.maps import _font

    font = _font(20)

    def ink(text: str) -> bytes:
        canvas = Image.new("L", (120, 40), 255)
        ImageDraw.Draw(canvas).text((2, 2), text, font=font, fill=0)
        return canvas.tobytes()

    assert ink("á") != ink("à")
    assert ink("ñ") != ink("n")


def test_study_guide_and_toolkit():
    assert "em dash" in study_guide("writing").lower()
    assert "apa" in study_guide("citations").lower()
    assert "openalex" in toolkit("research").lower()
    assert "Unknown" in toolkit("nope")


def test_study_guide_images_and_slides_topics():
    images = study_guide("images").lower()
    assert "wikimedia" in images
    assert "pollinations" in images
    assert study_guide("photos") == study_guide("images")
    slides = study_guide("slides").lower()
    assert "marp" in slides
    assert "pdf" in slides
    assert study_guide("marp") == study_guide("slides")
    assert "marp" in toolkit("slides").lower()


def test_render_document_report(tmp_path):
    spec = {
        "format": "report",
        "title": "Water quality",
        "abstract": "Short abstract.",
        "watermark": "DRAFT",
        "blocks": [
            {"type": "heading", "text": "Findings"},
            {"type": "text", "text": "Body paragraph."},
            {"type": "quote", "text": "A pull quote."},
            {"type": "list", "items": ["One", "Two"]},
            {"type": "table", "header": ["Source", "Value"], "rows": [["A", "1.0"], ["B", "2.0"]],
             "highlight": 0, "caption": "Table 1."},
            {"type": "chart", "kind": "bar", "categories": ["A", "B"], "values": [95, 38],
             "threshold": 50, "caption": "Figure 1."},
            {"type": "columns", "count": 2},
            {"type": "heading", "level": 2, "text": "Detail"},
            {"type": "text", "text": "Two column text."},
            {"type": "columns", "count": 1},
            {"type": "references", "items": ["Author, A. (2020). A title."]},
        ],
    }
    out = tmp_path / "report.pdf"
    info = render_document(spec, out)
    assert info["format"] == "report"
    assert info["pages"] >= 3
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")


def test_render_document_slides_reveal(tmp_path):
    spec = {
        "format": "slides",
        "title": "Deck",
        "slides": [
            {"layout": "cover", "title": "Deck", "subtitle": "Subtitle"},
            {"layout": "bullets", "title": "Points", "reveal": True,
             "items": [{"lead": "One.", "text": "first"}, {"lead": "Two.", "text": "second"}]},
            {"layout": "table", "title": "Data", "header": ["K", "V"], "rows": [["a", "1"]]},
            {"layout": "chart", "title": "Chart", "kind": "pie", "categories": ["a", "b"],
             "values": [60, 40]},
            {"layout": "closing", "title": "End", "lines": ["Thanks"]},
        ],
    }
    out = tmp_path / "deck.pdf"
    info = render_document(spec, out)
    assert info["format"] == "slides"
    assert info["pages"] == 6
    assert out.exists()


def test_render_document_rejects_unknown(tmp_path):
    with pytest.raises(ValueError):
        render_document({"format": "poster"}, tmp_path / "x.pdf")
    with pytest.raises(ValueError):
        render_document({"format": "report", "blocks": [{"type": "nope"}]}, tmp_path / "y.pdf")


def test_study_guide_documents_topic():
    guide = study_guide("documents").lower()
    assert "pandoc" in guide
    assert "reportlab" in guide
    assert "bibtex" in guide
    assert study_guide("word") == study_guide("documents")
    assert "reportlab" in study_guide("slides").lower()


def test_image_search_free_sources_and_ai_rule():
    brief = image_search("Great Wall of China", "photo")
    names = {provider["name"] for provider in brief["providers"]}
    assert {"Wikimedia Commons", "Openverse"} <= names
    assert brief["queries"][0] == "Great Wall of China"
    assert "explicitly" in brief["ai_generation"]["when"]
    assert all("commons.wikimedia.org" in p["search"] for p in brief["providers"] if p["name"] == "Wikimedia Commons")


def test_workspace_lifecycle(tmp_path):
    info = workspace_init(str(tmp_path), ["Cell Biology"])
    assert "CLAUDE.md" in info["created"]
    assert info["areas"] == ["cell-biology"]
    assert (tmp_path / "areas" / "cell-biology" / "knowledge.md").exists()
    assert (tmp_path / "templates" / "paper-apa7.tex").exists()

    area_add(str(tmp_path), "World History")
    result = reference_add(
        str(tmp_path),
        "World History",
        {"type": "book", "authors": ["Bloch, Marc"], "year": 1949, "title": "The Historian's Craft"},
    )
    assert result["key"] == "bloch1949"
    bib = (tmp_path / "areas" / "world-history" / "references.bib").read_text(encoding="utf-8")
    assert "bloch1949" in bib

    status = workspace_status(str(tmp_path))
    assert status["area_count"] == 2
    history = next(a for a in status["areas"] if a["area"] == "world-history")
    assert history["references"] == 1


def test_reference_add_copies_and_converts_source(tmp_path):
    workspace_init(str(tmp_path), ["Physics"])
    source = tmp_path / "paper.txt"
    source.write_text("reference content", encoding="utf-8")
    result = reference_add(
        str(tmp_path),
        "Physics",
        {"type": "article", "authors": ["Bohr, Niels"], "year": 1913, "title": "On atoms"},
        file=str(source),
    )
    assert result["source_copied"] is not None
    assert result["markdown"] is not None
    assert (tmp_path / "areas" / "physics" / "library" / "sources" / "paper.txt").exists()
    md = tmp_path / "areas" / "physics" / "library" / "md" / "bohr1913.md"
    assert md.exists()
    assert "reference content" in md.read_text(encoding="utf-8")


def test_reference_add_reads_pdf_in_order_and_cleans_it(tmp_path, monkeypatch):
    workspace_init(str(tmp_path), ["History"])
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"%PDF-1.4")
    commands = []

    def fake_run(command):
        commands.append(command)
        Path(command[-1]).write_text(
            "Header\nA line that goes\non and on. 1\fHeader\nMore text.\n2\fHeader\nEnd.\n3", encoding="utf-8"
        )
        return True

    monkeypatch.setattr(workspace, "_run", fake_run)
    monkeypatch.setattr(workspace.shutil, "which", lambda name: "/usr/bin/pdftotext")
    result = reference_add(
        str(tmp_path),
        "History",
        {"type": "book", "authors": ["Carr, E. H."], "year": 1961, "title": "What is history"},
        file=str(source),
    )
    assert commands[0][:2] == ["pdftotext", str(source)]
    assert Path(result["markdown"]).read_text(encoding="utf-8") == "A line that goes on and on.\n\nMore text.\n\nEnd.\n"


def test_normalize_extracted_removes_page_furniture_and_reflows():
    pages = [
        "Journal of Tests 12 (2024)\nFirst para that continues on the\nnext line and finishes here.\n\n"
        "Second para about hyphen-\nation and ﬁne ligatures.\n1",
        "Figure 1. Caption\nSee the figure.\nJournal of Tests 12 (2024)\nA.  Author Name\nTable 1. Caption text. 2",
        "Journal of Tests 12 (2024)\n3. Heading\nBody starts here.\n3",
        "Journal of Tests 12 (2024)\nLast page text.\n4",
    ]
    text = normalize_extracted("\f".join(pages))
    assert "Journal of Tests" not in text
    assert "\f" not in text
    assert "First para that continues on the next line and finishes here.\n\nSecond para" in text
    assert "hyphenation and fine ligatures." in text
    assert "See the figure.\nA. Author Name\nTable 1. Caption text.\n\n3. Heading\nBody starts here." in text
    assert text.endswith("Last page text.\n")


def test_normalize_extracted_keeps_short_documents_and_uppercase_breaks():
    text = normalize_extracted("Title\nBody of the note.\n12\nCOVID-\n19 figures\n")
    assert text == "Title\nBody of the note.\n12\nCOVID-\n19 figures\n"


def test_grammar_hits_drop_overlaps_and_locate_lines():
    text = "Primera linea.\nEsta claro que si."
    start = text.index("Esta")
    matches = [
        {
            "offset": start,
            "length": 10,
            "message": "agreement",
            "replacements": [{"value": "Este claro"}],
            "rule": {"id": "AGREEMENT", "category": {"id": "GRAMMAR"}},
        },
        {
            "offset": start,
            "length": 4,
            "message": "tilde",
            "replacements": [{"value": f"Est{suffix}"} for suffix in "aeiouy"],
            "rule": {"id": "ESTA_TILDE", "category": {"id": "TYPOS"}},
        },
        {
            "offset": text.index("si."),
            "length": 2,
            "message": "si/si",
            "replacements": [{"value": "sí"}],
            "rule": {"id": "SI", "category": {"id": "TYPOS"}},
        },
    ]
    plain, origins = plain_text(text)
    assert plain == text
    found = hits(text, plain, origins, matches)
    assert [hit["rule"] for hit in found] == ["ESTA_TILDE", "SI"]
    assert (found[0]["line"], found[0]["column"], found[0]["text"]) == (2, 1, "Esta")
    assert len(found[0]["replacements"]) == 5
    assert found[1]["replacements"] == ["sí"]


def test_plain_text_strips_markup_and_keeps_origins():
    source = (
        "---\ntitle: Deck\n---\n# Título\n\nUn **texto** con [enlace](https://x.y/z) y cita [@key2020, p. 3].\n\n"
        "![fig](img.png){width=50%}\n: Pie de figura\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
        "::: {custom-style=\"Figura\"}\nIlustración 1 Fuente\n:::\n\n"
        "Ver <span class=\"x\">nota</span>, `code` y @otra2021 al final.\n"
    )
    plain, origins = plain_text(source)
    markup = ("---", "title:", "#", "**", "](", "https", "@key2020", "{width", "|", "`", "<span", "@otra2021", ":::")
    assert not [piece for piece in markup if piece in plain]
    assert "Un texto con enlace y cita .\n" in plain
    assert "Pie de figura" in plain and " a b \n" in plain and " 1 2 \n" in plain
    assert "\nIlustración 1 Fuente\n" in plain
    assert "Ver nota, y al final.\n" in plain
    for word in ("texto", "enlace", "nota"):
        start = origins[plain.index(word)]
        assert source[start : start + len(word)] == word
    assert len(origins) == len(plain)


def test_grammar_backend_prefers_server_then_home_then_wrapper(tmp_path, monkeypatch):
    monkeypatch.setenv(URL_VAR, "http://localhost:8081/")
    monkeypatch.setenv(HOME_VAR, str(tmp_path))
    assert backend() == {"kind": "server", "url": "http://localhost:8081"}

    monkeypatch.delenv(URL_VAR)
    monkeypatch.setattr(grammar.shutil, "which", lambda name: None)
    assert backend() == {}
    assert "java" in grammar_check("text", "es")["reason"]

    monkeypatch.setattr(grammar.shutil, "which", lambda name: "/usr/bin/java" if name == "java" else None)
    assert "languagetool-commandline.jar" in grammar_check("text", "es")["reason"]
    (tmp_path / "languagetool-commandline.jar").write_bytes(b"")
    assert backend()["command"][:2] == ["/usr/bin/java", "-jar"]

    monkeypatch.delenv(HOME_VAR)
    wrapper = "/usr/local/bin/languagetool"
    monkeypatch.setattr(grammar.shutil, "which", lambda name: wrapper if name == "languagetool" else None)
    assert backend() == {"kind": "commandline", "command": [wrapper]}

    monkeypatch.setattr(grammar.shutil, "which", lambda name: None)
    report = grammar_check("text", "es")
    assert report["available"] is False
    assert URL_VAR in report["reason"] and HOME_VAR in report["reason"]


def test_grammar_check_runs_the_command_line(tmp_path, monkeypatch):
    (tmp_path / "languagetool-commandline.jar").write_bytes(b"")
    monkeypatch.delenv(URL_VAR, raising=False)
    monkeypatch.setenv(HOME_VAR, str(tmp_path))
    monkeypatch.setattr(grammar.shutil, "which", lambda name: "java" if name == "java" else None)
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        payload = {
            "software": {"version": "6.6"},
            "language": {"code": "es"},
            "matches": [
                {
                    "offset": 0,
                    "length": 4,
                    "message": "m",
                    "replacements": [],
                    "rule": {"id": "R", "category": {"id": "TYPOS"}},
                }
            ],
        }
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr(grammar.subprocess, "run", fake_run)
    report = grammar_check("Hola mundo", "es")
    assert report["available"] and report["backend"] == "commandline"
    assert (report["total_hits"], report["by_category"], report["languagetool"]) == (1, {"TYPOS": 1}, "6.6")
    assert report["hits"][0]["text"] == "Hola"
    assert commands[0][:3] == ["java", "-jar", str(tmp_path / "languagetool-commandline.jar")]
    assert commands[0][3:7] == ["-l", "es", "--json", "--clean-overlapping"]


def test_toolkit_grammar_group_and_workspace_final_pass(tmp_path):
    text = toolkit("grammar")
    assert "LanguageTool" in text and URL_VAR in text and HOME_VAR in text
    workspace_init(str(tmp_path))
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "grammar_check" in claude and "once over the complete text" in claude
    assert "Never check paragraph by paragraph" in claude


def test_check_links_reports_dead_urls_with_their_archive(tmp_path, monkeypatch):
    (tmp_path / "references.bib").write_text(
        "@misc{a,\n  url = {https://example.org/alive.pdf}\n}\n"
        "@article{b,\n  doi = {10.1234/abc.5}\n}\n"
        "@misc{c,\n  url = {https://gone.example/file.pdf}\n}\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.md").write_text(
        "See (https://gone.example/file.pdf). Also https://en.wikipedia.org/wiki/Foo_(bar).\n"
        "https://moved.example/old\n",
        encoding="utf-8",
    )
    answers = {
        "https://example.org/alive.pdf": {"status": 200, "type": "application/pdf", "final": "https://example.org/alive.pdf"},
        "https://doi.org/10.1234/abc.5": {"status": 200, "type": "text/html", "final": "https://publisher.example/abc5"},
        "https://gone.example/file.pdf": {"status": 403, "type": "text/html", "final": "https://gone.example/file.pdf"},
        "https://en.wikipedia.org/wiki/Foo_(bar)": {"status": 200, "type": "text/html", "final": "https://en.wikipedia.org/wiki/Foo_(bar)"},
        "https://moved.example/old": {"status": None, "error": "timeout"},
    }
    archive = "https://web.archive.org/web/20251124235719/https://gone.example/file.pdf"
    captures = {"https://gone.example/file.pdf": {"archive": archive, "captured": "2025-11-24"}}
    monkeypatch.setattr(links, "_status", lambda url: answers[url])
    monkeypatch.setattr(links, "_capture", lambda url: captures.get(url, {"archive": None}))

    report = check_links(path=str(tmp_path))
    assert report["checked"] == 5 and report["ok"] == 3 and report["skipped"] == []
    gone, moved = report["failing"]
    assert gone["url"] == "https://gone.example/file.pdf" and gone["status"] == 403
    assert gone["archive"] == archive and gone["captured"] == "2025-11-24"
    assert gone["where"] == ["notes.md:1", "references.bib:8"]
    assert moved["url"] == "https://moved.example/old" and moved["error"] == "timeout" and moved["archive"] is None
    assert report["redirected"] == [{"url": "https://doi.org/10.1234/abc.5", "to": "https://publisher.example/abc5"}]


def test_extract_urls_keeps_balanced_parentheses_and_drops_punctuation():
    text = "A (https://x.example/a). B https://x.example/b, C https://x.example/Foo_(bar); doi: 10.1234/z.9."
    assert extract_urls(text) == [
        "https://x.example/a", "https://x.example/b", "https://x.example/Foo_(bar)", "https://doi.org/10.1234/z.9",
    ]


def test_check_links_asks_the_doi_registry_not_the_publisher(monkeypatch):
    seen: list[str] = []

    def fake_urlopen(request, timeout=0):
        seen.append(request.full_url)
        raise AssertionError("the publisher must not be opened")

    monkeypatch.setattr(links, "_handle", lambda doi: {"status": 200, "type": "doi", "final": f"https://pub.example/{doi}"})
    monkeypatch.setattr(links.urllib.request, "urlopen", fake_urlopen)
    report = check_links(text="https://doi.org/10.5555/abc.1 and doi = {10.5555/abc.1}")
    assert report["checked"] == 1 and report["ok"] == 1 and report["redirected"] == [] and seen == []


def test_check_links_retries_a_refused_connection_once_but_not_a_timeout(monkeypatch):
    calls: list[str] = []

    class Response(io.BytesIO):
        status = 200
        headers = {"Content-Type": "text/html"}

        def geturl(self):
            return "https://refused.example/"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def opening(url, timeout, accept="*/*"):
        calls.append(url)
        if url == "https://refused.example/":
            if calls.count(url) == 1:
                raise urllib.error.URLError(ConnectionRefusedError(111, "refused"))
            return Response()
        raise urllib.error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr(links, "_open", opening)
    report = check_links(text="https://refused.example/ https://slow.example/")
    assert report["ok"] == 1
    assert calls.count("https://refused.example/") == 2 and calls.count("https://slow.example/") == 1
    slow = report["failing"][0]
    assert slow["url"] == "https://slow.example/" and slow["error"] == "timeout"
    assert slow["archive"] is None and slow["archive_error"] == "timeout"


def test_check_links_never_opens_private_hosts_or_credentials_and_keeps_secrets_from_the_archive(monkeypatch):
    opened: list[str] = []
    archived: list[str] = []

    def status(url):
        opened.append(url)
        return {"status": 404, "type": "text/html", "final": url}

    def cdx(url):
        archived.append(url)
        return []

    monkeypatch.setattr(links, "_public", lambda host: host == "host.example")
    monkeypatch.setattr(links, "_status", status)
    monkeypatch.setattr(links, "_cdx", cdx)
    report = check_links(
        text="http://localhost:8080/x https://user:pw@host.example/y https://host.example/f?token=abc "
        "https://host.example/g"
    )
    assert opened == ["https://host.example/f?token=abc", "https://host.example/g"]
    assert [item["reason"] for item in report["skipped"]] == ["not a public host", "carries credentials"]
    assert report["skipped"][1]["url"] == "https://host.example/y"
    assert links._blocked("ftp://host.example/z") == "not an http(s) URL"
    assert archived == ["https://host.example/g"]
    tokened = report["failing"][0]
    assert tokened["archive"] is None and "credential" in tokened["archive_error"]


def test_check_links_refuses_a_redirect_to_a_private_host(monkeypatch):
    monkeypatch.setattr(links, "_public", lambda host: host == "host.example")
    handler = links._Redirects()
    assert handler.redirect_request(None, None, 302, "Found", {}, "http://127.0.0.1/admin") is None
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://user:pw@host.example/") is None


def test_vetted_connection_refuses_a_private_address_at_connect_time(monkeypatch):
    private = [(links.socket.AF_INET, links.socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]
    monkeypatch.setattr(links.socket, "getaddrinfo", lambda *args, **kwargs: private)
    monkeypatch.setattr(links.socket, "socket", lambda *args: pytest.fail("no socket for a private address"))
    connection = links._VettedHTTPS("host.example", 443, context=links._SSL)
    with pytest.raises(OSError, match="not a public host"):
        connection.connect()


def test_vetted_connection_connects_to_the_address_it_vetted(monkeypatch):
    public = [(links.socket.AF_INET, links.socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
    connected: list[tuple] = []

    class Sock:
        def __init__(self, *args):
            pass

        def settimeout(self, value):
            pass

        def connect(self, sockaddr):
            connected.append(sockaddr)

    class Context(links.ssl.SSLContext):
        def wrap_socket(self, sock, server_hostname=None, **kwargs):
            connected.append(("tls", server_hostname))
            return sock

    monkeypatch.setattr(links.socket, "getaddrinfo", lambda *args, **kwargs: public)
    monkeypatch.setattr(links.socket, "socket", Sock)
    connection = links._VettedHTTPS("host.example", 443, context=Context(links.ssl.PROTOCOL_TLS_CLIENT))
    connection.connect()
    assert connected == [("93.184.216.34", 443), ("tls", "host.example")]


def test_secret_parameters_and_fragments_never_reach_the_archive():
    assert links._secret("https://h.example/f?a=1;sid=9")
    assert links._secret("https://h.example/f?jwt=x") and links._secret("https://h.example/f?X-Amz-Signature=x")
    assert links._secret("https://h.example/f?access_key=x") and not links._secret("https://h.example/f?page=2&id=7")
    assert links._bare("https://h.example/f?page=2#sec") == "https://h.example/f?page=2"
    assert links._blocked("https://ho%73t.example/") == "no valid host"
