"""studykit: area-agnostic study toolkit (writing and grammar checks, citations, concept maps, workspace)."""
from __future__ import annotations

from .cite import (
    bibtex_entry,
    bibtex_key,
    doi_to_bibtex,
    format_citation,
    in_text_citation,
)
from .grammar import grammar_check
from .guide import guide_topics, study_guide, toolkit, toolkit_groups
from .images import image_search
from .maps import render_concept_map
from .normalize import normalize_extracted
from .office import inspect_template
from .render import render_document
from .review import final_check
from .text import burstiness, split_sentences, writing_check
from .workspace import area_add, reference_add, workspace_init, workspace_status

__all__ = [
    "writing_check",
    "burstiness",
    "grammar_check",
    "final_check",
    "inspect_template",
    "normalize_extracted",
    "split_sentences",
    "study_guide",
    "guide_topics",
    "toolkit",
    "toolkit_groups",
    "image_search",
    "render_concept_map",
    "render_document",
    "format_citation",
    "in_text_citation",
    "bibtex_entry",
    "bibtex_key",
    "doi_to_bibtex",
    "workspace_init",
    "area_add",
    "reference_add",
    "workspace_status",
]
