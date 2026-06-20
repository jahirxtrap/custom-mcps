# studykit

An **area-agnostic, language-agnostic** study toolkit — the logic behind the `study` MCP server.
It distills the reusable half of an academic-work assistant into plain functions: catch "AI tells"
in writing, format citations, render concept maps by data, and scaffold a multi-area study
workspace. It carries no subject knowledge; the field is chosen by the user.

## What it gives you

| Module | Provides |
|---|---|
| `text` | `writing_check` (AI-tell detection, EN+ES), `burstiness` (sentence-length variation), `split_sentences` |
| `guide` | `study_guide(topic)` (writing/citations/structure/visual), `toolkit(topic)` (ecosystem catalog + install commands) |
| `maps` | `render_concept_map(spec)` -> a Pillow image, following the anti-AI visual rules |
| `cite` | `format_citation` (APA 7), `in_text_citation`, `bibtex_entry`, `bibtex_key`, `doi_to_bibtex` |
| `workspace` | `workspace_init`, `area_add`, `reference_add`, `workspace_status` |

## Example

```python
from studykit import writing_check, burstiness, format_citation, workspace_init

writing_check("It's important to note that we delve into the topic.")  # filler + ai_vocabulary
burstiness("Short. " * 5)                                              # uniform -> low score
format_citation({"type": "article", "authors": ["Smith, John"], "year": 2020,
                 "title": "On X", "journal": "Journal", "volume": 3, "pages": "1-10"})
workspace_init("/path/to/ws", ["Biology", "History"])                 # multi-area scaffold
```

## Notes

- `writing_check` flags em dashes, AI filler, negative parallelism, the rule of three, tell-tale
  vocabulary, vague attributions, meta-commentary, chained transitions and stacked hedging in
  **English and Spanish**, and returns a 0-100 score with hits by category.
- `burstiness` reports mean and standard deviation of sentence length plus a score (detectors
  penalize uniformity); it is language-agnostic.
- `render_concept_map` needs only Pillow; titles are the topic, not a meta label.
- Citations mark italics with `*...*` for clean Markdown paste; `doi_to_bibtex` uses the network.
- The workspace is multi-area: shared `conventions/`, `styles/`, `memory/`, and one folder per
  area under `areas/` with its own knowledge base and reference library.
