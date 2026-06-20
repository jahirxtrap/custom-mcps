"""Audio I/O: write via the best available encoder (ffmpeg > soundfile), waveform, inspect."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

from .synth import Samples

_SF_FORMAT = {
    "ogg": ("OGG", "VORBIS"),
    "opus": ("OGG", "OPUS"),
    "wav": ("WAV", "PCM_16"),
    "flac": ("FLAC", "PCM_16"),
}
_FFMPEG_CODEC = {
    "ogg": "libvorbis",
    "opus": "libopus",
    "mp3": "libmp3lame",
    "flac": "flac",
    "wav": "pcm_s16le",
}


def ffmpeg_path() -> str | None:
    return os.environ.get("FFMPEG") or shutil.which("ffmpeg")


def _to_channels(mono: Samples, channels: int) -> Samples:
    data = np.asarray(mono, dtype=np.float32)
    if channels <= 1:
        return data
    return np.column_stack([data] * channels)


def _write_soundfile(data: Samples, path: Path, sample_rate: int, fmt: str) -> None:
    if fmt not in _SF_FORMAT:
        raise ValueError(f"soundfile cannot write '{fmt}' (use ogg/opus/wav/flac, or install ffmpeg)")
    container, subtype = _SF_FORMAT[fmt]
    sf.write(str(path), data, sample_rate, format=container, subtype=subtype)


def _write_ffmpeg(
    ff: str, data: Samples, path: Path, sample_rate: int, channels: int, fmt: str, quality: int
) -> None:
    tmp = Path(tempfile.gettempdir()) / f"audiolib_{uuid.uuid4().hex[:8]}.wav"
    sf.write(str(tmp), data, sample_rate, format="WAV", subtype="PCM_16")
    cmd = [ff, "-y", "-i", str(tmp), "-ac", str(channels), "-c:a", _FFMPEG_CODEC.get(fmt, "libvorbis")]
    if fmt in ("ogg", "mp3"):
        cmd += ["-q:a", str(quality)]
    cmd += [str(path)]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
    finally:
        tmp.unlink(missing_ok=True)


def write(
    samples: Samples,
    path: str | Path,
    sample_rate: int = 44100,
    channels: int = 1,
    fmt: str | None = None,
    quality: int = 5,
    encoder: str = "auto",
) -> Path:
    """Write samples to `path`, choosing the best encoder (ffmpeg preferred, soundfile fallback)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    chosen = (fmt or out.suffix.lstrip(".") or "ogg").lower()
    data = _to_channels(samples, channels)
    ff = ffmpeg_path()
    if encoder == "ffmpeg" and not ff:
        raise RuntimeError("encoder='ffmpeg' but ffmpeg was not found on PATH")
    if encoder == "ffmpeg" or (encoder == "auto" and ff and chosen in _FFMPEG_CODEC):
        _write_ffmpeg(ff, data, out, sample_rate, channels, chosen, quality)
    else:
        _write_soundfile(data, out, sample_rate, chosen)
    return out


def read(path: str | Path) -> tuple[Samples, int]:
    """Read an audio file as a mono float array. Falls back to ffmpeg for formats soundfile lacks."""
    try:
        data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    except Exception:
        ff = ffmpeg_path()
        if not ff:
            raise
        tmp = Path(tempfile.gettempdir()) / f"audiolib_{uuid.uuid4().hex[:8]}.wav"
        subprocess.run([ff, "-y", "-i", str(path), str(tmp)], capture_output=True, check=True)
        data, sr = sf.read(str(tmp), dtype="float32", always_2d=False)
        tmp.unlink(missing_ok=True)
    if getattr(data, "ndim", 1) > 1:
        data = data.mean(axis=1)
    return data, sr


def waveform_image(samples: Samples, width: int = 640, height: int = 200) -> Image.Image:
    """Render the waveform as an image (attack, body and tail visible) for inspection."""
    img = Image.new("RGBA", (width, height), (24, 24, 30, 255))
    draw = ImageDraw.Draw(img)
    mid = height / 2.0
    draw.line([(0, mid), (width, mid)], fill=(60, 60, 72, 255))
    data = np.asarray(samples, dtype=float)
    n = len(data)
    if n == 0:
        return img
    peak = float(np.max(np.abs(data))) or 1.0
    amp = (height / 2.0) - 3.0
    for x in range(width):
        a = int(x * n / width)
        b = max(a + 1, int((x + 1) * n / width))
        chunk = data[a:b] / peak
        y0 = mid - float(chunk.max()) * amp
        y1 = mid - float(chunk.min()) * amp
        draw.line([(x, y0), (x, y1)], fill=(120, 200, 150, 255))
    return img


def inspect(path: str | Path) -> dict[str, Any]:
    """Report duration, sample rate, peak, RMS, clipping and lead silence of an audio file."""
    data, sr = read(path)
    s = np.asarray(data, dtype=float)
    if len(s) == 0:
        return {"duration": 0.0, "sample_rate": sr, "peak": 0.0, "rms": 0.0,
                "clipping_samples": 0, "lead_silence": 0.0}
    peak = float(np.max(np.abs(s)))
    rms = float(np.sqrt(np.mean(s**2)))
    clipping = int(np.sum(np.abs(s) >= 0.999))
    voiced = np.where(np.abs(s) > 1e-4)[0]
    lead = float(voiced[0] / sr) if len(voiced) else 0.0
    return {
        "duration": round(len(s) / sr, 4),
        "sample_rate": sr,
        "peak": round(peak, 4),
        "rms": round(rms, 4),
        "clipping_samples": clipping,
        "lead_silence": round(lead, 4),
    }
