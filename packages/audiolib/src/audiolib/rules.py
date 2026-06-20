"""Embedded, general sound-effect design guidance (self-contained, no external skill)."""
from __future__ import annotations

_ANATOMY = [
    "Most SFX = transient + body + tail. The TRANSIENT is the short attack that gives "
    "the click/punch; the BODY is the tone/character; the TAIL closes it. Pick the ones you need.",
    "Layer them: a sharp transient over a tonal body reads as one punchy sound.",
]

_TECHNIQUES = [
    "coin / pickup / confirm: ascending tone(s), bright harmonics, short.",
    "laser / shoot: descending sweep + a little noise; fast.",
    "explosion / impact: noise + long envelope + a low-pass that closes; strong transient.",
    "jump / dash: ascending sweep. land: short thump (low sine + noise).",
    "power-up / level-up: ascending sweep or arpeggio, longer and brighter.",
    "magic / sci-fi: FM or ring-mod plus sweeps. UI click/cancel: very short, dry transient.",
    "retro / 8-bit: square/saw oscillators plus bitcrush.",
]

_RULES = [
    "Peak-normalize (never full scale): a pure sine at +-1.0 sounds harsh and too loud.",
    "Keep it short and punchy; trim dead tails.",
    "Mono for SFX; reserve stereo for ambience.",
    "Generate 2+ variants (pitch jitter ~+-10%) so a repeated sound does not fatigue.",
    "Avoid clipping; leave a little headroom (target ~0.9, not 1.0).",
    "Volume per family (impacts loud, footsteps quiet) belongs to the project that consumes "
    "the sound, not to the synth.",
]


def guide() -> str:
    """Render the embedded general SFX-design guidance."""
    sections = [
        ("Anatomy", _ANATOMY),
        ("Techniques by intent", _TECHNIQUES),
        ("Rules", _RULES),
    ]
    lines = ["# Sound-effect design guide"]
    for title, items in sections:
        lines += ["", f"## {title}"]
        lines += [f"- {item}" for item in items]
    return "\n".join(lines)
