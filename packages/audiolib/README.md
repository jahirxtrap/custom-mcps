# audiolib

Engine-agnostic sound-effect synthesis primitives, built on NumPy + Pillow, with audio
I/O that prefers ffmpeg and falls back to libsndfile (`soundfile`). No project or engine
assumptions — the "synthesize by data" toolkit used by the `sfx` MCP server.

## What it gives you

| Module | Provides |
|---|---|
| `synth` | `osc`, `sweep`, `fm`, `noise`, `envelope`, `low_pass`/`high_pass`, `bitcrush`, `drive`, `mix`, `peak_normalize` |
| `io` | `write` (ffmpeg > soundfile), `read`, `waveform_image`, `inspect`, `ffmpeg_path` |
| `rules` | `guide` (embedded general SFX-design guidance) |

## The pipeline

```python
import numpy as np
from audiolib import sweep, osc, envelope, mix, peak_normalize, write

dur, sr = 0.3, 44100
body = sweep("sine", 220, 880, dur, sr) * envelope("decay", dur, sr, power=2.5)
spark = osc("triangle", 1320, dur, sr) * envelope("decay", dur, sr, power=8) * 0.4
samples = peak_normalize(mix([body, spark]), 0.9)
write(samples, "pickup.ogg", sample_rate=sr)   # ffmpeg if present, else libsndfile
```

Synthesize by building float samples (transient + body + tail), peak-normalize, then
write. Verify by eye with `waveform_image` and by numbers with `inspect`.

## Encoder

`write(..., encoder="auto")` picks the best available: **ffmpeg** when on PATH (quality
`-q:a`, more formats), otherwise **soundfile**/libsndfile (Ogg/Vorbis, Opus, WAV, FLAC).
Force it with `encoder="ffmpeg"` or `encoder="soundfile"`.
