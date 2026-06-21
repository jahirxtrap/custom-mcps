from __future__ import annotations

from studykit import (
    area_add,
    bibtex_entry,
    bibtex_key,
    burstiness,
    format_citation,
    in_text_citation,
    reference_add,
    render_concept_map,
    study_guide,
    toolkit,
    workspace_init,
    workspace_status,
    writing_check,
)


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


def test_study_guide_and_toolkit():
    assert "em dash" in study_guide("writing").lower()
    assert "apa" in study_guide("citations").lower()
    assert "openalex" in toolkit("research").lower()
    assert "Unknown" in toolkit("nope")


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
