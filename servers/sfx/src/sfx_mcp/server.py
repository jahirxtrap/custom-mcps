"""sfx MCP server: synthesize sound effects by data. Engine-agnostic."""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

from audiolib import guide as guide_text, inspect as audio_inspect, read, waveform_image, write
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from .builder import build_from_spec

mcp = FastMCP(name="sfx")

_MIME = {"ogg": "audio/ogg", "opus": "audio/ogg", "wav": "audio/wav", "mp3": "audio/mpeg", "flac": "audio/flac"}


def _scratch(prefix: str, ext: str, out_dir: str = "") -> Path:
    base = Path(out_dir) if out_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"


def _audio_result(native: Path, out_dir: str) -> list[Any]:
    data, _ = read(native)
    preview = waveform_image(data)
    preview_path = _scratch("waveform", "png", out_dir)
    preview.save(preview_path)
    report = audio_inspect(native)
    ext = native.suffix.lstrip(".").lower()
    summary = (
        f"path={native} mime={_MIME.get(ext, 'audio/ogg')} duration={report['duration']}s "
        f"peak={report['peak']} sr={report['sample_rate']} waveform={preview_path}"
    )
    return [Image(path=str(preview_path)), summary]


@mcp.tool
def sfx_guide() -> str:
    """Return the embedded general SFX-design guidance (anatomy: transient/body/tail,
    techniques by intent for coin/laser/explosion/jump/power-up/UI/retro, and rules)."""
    return guide_text()


@mcp.tool(output_schema=None)
def synth_sfx(spec: str, out_dir: str = "", encoder: str = "auto") -> list[Any]:
    """Synthesize a sound effect from a declarative JSON spec; returns a waveform preview image
    plus a 'path=' summary. Spec: {duration, layers:[...], normalize?, format?, sample_rate?,
    channels?, quality?, out?}. layer = {type: osc|sweep|noise|fm, freq/f0,f1/carrier,mod...,
    env?:{shape:decay|ar|adsr,...}, gain?, lowpass?, highpass?, bitcrush?, drive?}.
    Defaults: normalize peak 0.9, ogg, 44100 Hz, mono. encoder auto picks ffmpeg, else soundfile."""
    data = json.loads(spec)
    samples, settings = build_from_spec(data)
    out = data.get("out")
    fmt = settings["format"] or "ogg"
    native = Path(out) if out else _scratch("sfx", fmt, out_dir)
    write(
        samples,
        native,
        sample_rate=settings["sample_rate"],
        channels=settings["channels"],
        fmt=settings["format"],
        quality=settings["quality"],
        encoder=encoder,
    )
    return _audio_result(native, out_dir)


@mcp.tool(output_schema=None)
def waveform(path: str, out_dir: str = "") -> list[Any]:
    """Render the waveform of an audio file as an image for inspection (you can see the
    attack, body and tail). Returns the image + a 'path=' line."""
    data, _ = read(path)
    image = waveform_image(data)
    image_path = _scratch("waveform", "png", out_dir)
    image.save(image_path)
    return [Image(path=str(image_path)), f"path={image_path} mime=image/png size={image.width}x{image.height}"]


@mcp.tool
def encode(path: str, fmt: str, out: str = "", encoder: str = "auto") -> str:
    """Convert an audio file to another format (wav/ogg/opus/flac/mp3) with the best encoder
    available (ffmpeg if present, else soundfile)."""
    data, sample_rate = read(path)
    target = Path(out) if out else Path(path).with_suffix("." + fmt)
    write(data, target, sample_rate=sample_rate, fmt=fmt, encoder=encoder)
    return json.dumps({"path": str(target), "format": fmt})


@mcp.tool
def inspect(path: str) -> str:
    """Report an audio file's duration, sample rate, peak, RMS, clipping and lead silence."""
    return json.dumps(audio_inspect(path))


def main() -> None:
    mcp.run()
