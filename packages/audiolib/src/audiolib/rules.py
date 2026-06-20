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
    "magic / sci-fi / bell: ring-mod two oscillators (inharmonic) + a long decay.",
    "string / pluck / twang: Karplus-Strong (pluck) at the target pitch.",
    "whoosh / wind: low-pass-filtered noise with a 'hump' envelope.",
    "UI click / cancel: very short, dry transient. retro / 8-bit: square/saw + bitcrush.",
]

_RECIPES = [
    "impact / hit: noise + a steep decay envelope (power ~20) for the click; optional low sine thump.",
    "thump / slam: descending sine sweep (e.g. 160->40 Hz) + decay envelope (power ~2.5) + noise crunch.",
    "whoosh / wind: low-pass-filtered noise (filter ~0.87) + 'hump' envelope (sin(pi*t), power ~1.4).",
    "pluck / string: a single 'pluck' layer at the pitch; raise pluck_decay for more sustain.",
    "bell / metallic: 'ring' layer (two close-but-inharmonic freqs) + long decay envelope.",
    "coin: ascending sine/square sweep + a short bright sine on top.",
]

_NORMALIZATION = [
    "Short SFX (<~0.5s): PEAK-normalize. Do NOT use loudness/LUFS normalization (e.g. ffmpeg "
    "loudnorm): it targets integrated loudness over the whole clip, so a short clip gets AMPLIFIED "
    "near clipping and ends up too loud.",
    "LUFS/loudnorm is only for matching levels ACROSS several longer clips, not for a single short one.",
    "Keep headroom: target peak ~0.9, never 1.0.",
]

_RULES = [
    "Keep it short and punchy; trim dead tails.",
    "Mono for SFX; reserve stereo for ambience.",
    "Generate 2+ variants (pitch jitter ~+-10%) so a repeated sound does not fatigue.",
    "Avoid clipping.",
    "Volume per family (impacts loud, footsteps quiet) belongs to the project that consumes "
    "the sound, not to the synth.",
]


def guide() -> str:
    """Render the embedded general SFX-design guidance."""
    sections = [
        ("Anatomy", _ANATOMY),
        ("Techniques by intent", _TECHNIQUES),
        ("Recipes (reference parameters)", _RECIPES),
        ("Normalization", _NORMALIZATION),
        ("Rules", _RULES),
    ]
    lines = ["# Sound-effect design guide"]
    for title, items in sections:
        lines += ["", f"## {title}"]
        lines += [f"- {item}" for item in items]
    return "\n".join(lines)
