# sfx MCP server

A standalone MCP server for **synthesizing sound effects by data**. Engine-agnostic — it
makes `.ogg` (or wav/opus/flac/mp3) effects of any kind: pickups, UI clicks, lasers,
explosions, jumps, power-ups, magic, impacts, whooshes. It knows nothing about any
project, engine or game. The SFX-design principles are embedded, so it needs no external
skill.

Built on [`fastmcp`](https://gofastmcp.com) on top of the shared
[`audiolib`](../../packages/audiolib) library (NumPy + Pillow + soundfile, ffmpeg optional).

## Tools

| Tool | Purpose |
|---|---|
| `sfx_guide` | Embedded SFX-design guidance: anatomy (transient/body/tail), techniques by intent, rules. |
| `synth_sfx` | Synthesize an effect from a declarative JSON spec. Returns the waveform preview + a `path=` line. |
| `waveform` | Render any audio file's waveform as an image for inspection. |
| `encode` | Convert between formats (wav ↔ ogg/opus/flac/mp3) with the best encoder available. |
| `inspect` | Duration, sample rate, peak, RMS, clipping, lead silence of an audio file. |

## The `synth_sfx` spec

```json
{
  "duration": 0.3,
  "normalize": 0.9,
  "format": "ogg",
  "sample_rate": 44100,
  "channels": 1,
  "quality": 5,
  "layers": [
    { "type": "sweep", "wave": "square", "f0": 600, "f1": 1200,
      "env": { "shape": "ar", "attack": 0.01, "release": 0.28 }, "gain": 0.8 },
    { "type": "osc", "wave": "sine", "freq": 880,
      "env": { "shape": "decay", "power": 3 }, "gain": 0.5, "bitcrush": 6 }
  ],
  "out": "powerup.ogg"
}
```

- `layer.type`: `osc` (wave+freq) · `sweep` (wave+f0+f1) · `noise` (filter 0–1) · `fm` (carrier+mod+index).
- `env.shape`: `decay` (`pow(1-t,power)`) · `ar` (attack+release) · `adsr`.
- Per layer: `gain`, plus optional shaping `lowpass` / `highpass` / `bitcrush` / `drive`.
- **Output settings are optional** — defaults: peak `0.9`, `ogg`, `44100` Hz, mono, quality `~5`.

The same spec covers any intent: coin (ascending sine sweep), laser (descending saw + noise),
explosion (noise + long envelope + low-pass), jump (ascending sweep), UI click (very short transient).

## Output contract (UI-agnostic)

`synth_sfx` and `waveform` return a standard image block (the waveform — I can't hear, I verify
by looking) **and** a text line `path=<abs> mime=... duration=... peak=...`. Showing the image or
playing the audio is the host agent's job.

## Encoder

`encoder="auto"` (default) prefers **ffmpeg** when on PATH (quality, more formats) and falls
back to **soundfile**/libsndfile, which is always available. Force `ffmpeg` or `soundfile`.

ffmpeg is **optional** — install it only to widen format/codec coverage:
`winget install Gyan.FFmpeg` | `brew install ffmpeg` | `apt install ffmpeg`. The study server's
`scripts/setup.py --all` also installs it. `sfx_guide` repeats this under "Tools (optional)".

## Run / register

```bash
uv run sfx-mcp                       # run over stdio
uv run python scripts/register.py    # register every server (this one included) at user scope
```
