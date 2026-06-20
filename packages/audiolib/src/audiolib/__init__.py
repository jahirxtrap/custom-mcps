"""audiolib: engine-agnostic sound-effect synthesis primitives and audio I/O."""
from __future__ import annotations

from .io import ffmpeg_path, inspect, read, waveform_image, write
from .rules import guide
from .synth import (
    Samples,
    bitcrush,
    drive,
    envelope,
    fm,
    high_pass,
    low_pass,
    mix,
    noise,
    osc,
    peak_normalize,
    sweep,
)

__all__ = [
    "Samples",
    "osc",
    "sweep",
    "fm",
    "noise",
    "envelope",
    "low_pass",
    "high_pass",
    "bitcrush",
    "drive",
    "mix",
    "peak_normalize",
    "write",
    "read",
    "waveform_image",
    "inspect",
    "ffmpeg_path",
    "guide",
]
