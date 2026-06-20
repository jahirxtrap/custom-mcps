"""Language-agnostic text checks: AI-tell detection and sentence burstiness."""
from __future__ import annotations

import re
from typing import Any

_ACCENTS = {
    "a": "[aáàä]", "e": "[eéèë]", "i": "[iíìï]", "o": "[oóòö]",
    "u": "[uúùü]", "n": "[nñ]", "c": "[cç]",
}


def _fold(text: str) -> str:
    return "".join(_ACCENTS.get(ch, ch) for ch in text)


_FILLERS = [
    "en el vibrante mundo de", "en el panorama de", "en la era de", "en el mundo actual",
    "profundizar en", "en conclusion", "en resumen", "cabe destacar", "es importante senalar",
    "es importante destacar", "en ultima instancia", "hoy en dia", "a dia de hoy",
    "sin lugar a dudas", "merece la pena destacar",
    "in conclusion", "in summary", "it's important to note", "it is important to note",
    "it's worth noting", "it is worth noting", "delve into", "in the realm of",
    "in the world of", "in today's world", "needless to say", "at the end of the day",
    "when it comes to", "in the ever-evolving",
]

_AI_VOCAB = [
    "fundamental", "crucial", "pivotal", "robusto", "fomentar", "subrayar", "tapiz",
    "fascinante", "vibrante", "intrincado", "meticuloso", "primordial",
    "delve", "tapestry", "testament", "vibrant", "intricate", "bolster", "underscore",
    "leverage", "robust", "seamless", "showcase", "showcasing", "meticulous", "realm", "foster",
]

_VAGUE = [
    "los expertos coinciden", "los expertos afirman", "estudios demuestran", "estudios muestran",
    "se ha observado que", "se ha demostrado que", "diversos estudios", "numerosos estudios",
    "segun los expertos",
    "experts agree", "studies show", "studies demonstrate", "research suggests", "research shows",
    "it has been shown", "it is widely known", "it is well known", "scientists believe",
]

_META = [
    "como modelo de lenguaje", "como ia", "en este ensayo exploraremos", "en este ensayo",
    "en este trabajo exploraremos", "en este articulo analizaremos", "espero que esto ayude",
    "as an ai language model", "as a language model", "as an ai", "i hope this helps",
    "in this essay we will", "in this essay, we will", "in this article we will",
]

_TRANSITIONS = [
    "ademas", "asimismo", "por otro lado", "es mas", "en definitiva", "por consiguiente",
    "en este sentido",
    "moreover", "furthermore", "additionally", "in addition", "on the other hand",
    "consequently", "that being said", "besides",
]

_HEDGES = [
    "podria", "podrian", "quiza", "quizas", "tal vez", "en cierta medida", "hasta cierto punto",
    "posiblemente", "probablemente", "aparentemente",
    "might", "perhaps", "possibly", "arguably", "to some extent", "to a certain extent",
    "seemingly",
]

_NEGATIVE = [
    re.compile(_fold(pattern), re.IGNORECASE | re.DOTALL)
    for pattern in (
        r"no solo\b.{0,80}?\bsino\b",
        r"no se trata de\b.{0,80}?\bsino\b",
        r"not only\b.{0,80}?\bbut\b",
        r"it(?:'s| is) not (?:just|about|merely|only)\b.{0,80}?\bbut\b",
    )
]

_TRIAD = re.compile(
    _fold(r"\b[\w-]+(?:\s[\w-]+){0,2},\s[\w-]+(?:\s[\w-]+){0,2},?\s(?:y|e|and)\s[\w-]+(?:\s[\w-]+){0,2}"),
    re.IGNORECASE,
)

_WORD = re.compile(r"\b[\w']+\b", re.UNICODE)


def _phrase_re(phrases: list[str]) -> re.Pattern[str]:
    pattern = "|".join(_fold(re.escape(p)) for p in phrases)
    return re.compile(rf"(?<!\w)(?:{pattern})(?!\w)", re.IGNORECASE)


def _word_re(words: list[str]) -> re.Pattern[str]:
    pattern = "|".join(_fold(re.escape(w)) for w in words)
    return re.compile(rf"\b(?:{pattern})\b", re.IGNORECASE)


_FILLER_RE = _phrase_re(_FILLERS)
_VOCAB_RE = _word_re(_AI_VOCAB)
_VAGUE_RE = _phrase_re(_VAGUE)
_META_RE = _phrase_re(_META)
_HEDGE_RE = _word_re(_HEDGES)
_TRANS_RE = re.compile(
    rf"(?:^|[.!?]\s+|\n)\s*({'|'.join(_fold(re.escape(t)) for t in _TRANSITIONS)})\b",
    re.IGNORECASE | re.MULTILINE,
)

_WEIGHTS = {
    "em_dash": 4,
    "filler": 5,
    "ai_vocabulary": 2,
    "negative_parallelism": 6,
    "vague_attribution": 6,
    "meta_commentary": 10,
    "chained_transitions": 3,
    "stacked_hedging": 4,
    "rule_of_three": 2,
}

_CAP = 25


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def _collect(text: str, pattern: re.Pattern[str], group: int = 0) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        hits.append({"match": match.group(group).strip(), "line": _line_of(text, match.start(group))})
    return hits


def writing_check(text: str) -> dict[str, Any]:
    categories: dict[str, list[dict[str, Any]]] = {key: [] for key in _WEIGHTS}

    for match in re.finditer("—", text):
        categories["em_dash"].append({"match": "-", "line": _line_of(text, match.start())})

    categories["filler"] = _collect(text, _FILLER_RE)
    categories["ai_vocabulary"] = _collect(text, _VOCAB_RE)
    categories["vague_attribution"] = _collect(text, _VAGUE_RE)
    categories["meta_commentary"] = _collect(text, _META_RE)
    categories["chained_transitions"] = _collect(text, _TRANS_RE, group=1)
    categories["rule_of_three"] = _collect(text, _TRIAD)

    for pattern in _NEGATIVE:
        for match in pattern.finditer(text):
            categories["negative_parallelism"].append(
                {"match": " ".join(match.group(0).split())[:80], "line": _line_of(text, match.start())}
            )

    for match in re.finditer(r"[^.!?]+[.!?]*", text):
        segment = match.group(0)
        if len(_HEDGE_RE.findall(segment)) >= 2:
            categories["stacked_hedging"].append(
                {"match": " ".join(segment.split())[:80], "line": _line_of(text, match.start())}
            )

    penalty = sum(_WEIGHTS[key] * len(hits) for key, hits in categories.items())
    score = max(0, 100 - penalty)
    total = sum(len(hits) for hits in categories.values())
    nonzero = {key: hits for key, hits in categories.items() if hits}

    return {
        "score": score,
        "total_hits": total,
        "wordcount": len(_WORD.findall(text)),
        "summary": f"score {score}/100, {total} potential AI tells across {len(nonzero)} categories",
        "categories": {
            key: {"count": len(hits), "hits": hits[:_CAP]} for key, hits in categories.items() if hits
        },
    }


def burstiness(text: str) -> dict[str, Any]:
    sentences = split_sentences(text)
    lengths = [len(_WORD.findall(s)) for s in sentences]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return {
            "sentences": len(lengths),
            "score": 0,
            "label": "not enough sentences to measure",
        }
    mean = sum(lengths) / len(lengths)
    variance = sum((n - mean) ** 2 for n in lengths) / len(lengths)
    stdev = variance ** 0.5
    cv = stdev / mean if mean else 0.0
    low, high = mean * 0.75, mean * 1.25
    uniform = sum(1 for n in lengths if low <= n <= high) / len(lengths) * 100
    score = max(0, min(100, round(cv * 140)))
    if score < 35:
        label = "uniform (reads AI-like): vary your sentence length"
    elif score < 60:
        label = "some variation"
    else:
        label = "varied (human-like)"
    return {
        "sentences": len(lengths),
        "mean_words": round(mean, 2),
        "stdev_words": round(stdev, 2),
        "coefficient_of_variation": round(cv, 2),
        "uniform_pct": round(uniform, 1),
        "shortest": min(lengths),
        "longest": max(lengths),
        "score": score,
        "label": label,
    }
