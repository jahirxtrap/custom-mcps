"""The three text checks run together once over a finished text, answered as one report."""
from __future__ import annotations

from typing import Any

from .grammar import grammar_check
from .text import burstiness, writing_check


def final_check(text: str, language: str) -> dict[str, Any]:
    writing = writing_check(text)
    rhythm = burstiness(text)
    grammar = grammar_check(text, language)
    if grammar.get("available") and "error" not in grammar:
        grammar_line = f"grammar {grammar['total_hits']} findings"
    else:
        grammar_line = "grammar not checked (" + str(grammar.get("reason") or grammar.get("error")) + ")"
    summary = (
        f"writing {writing['score']}/100 with {writing['total_hits']} tells, "
        f"burstiness {rhythm['score']}/100, {grammar_line}"
    )
    return {"summary": summary, "writing": writing, "burstiness": rhythm, "grammar": grammar}
