"""Declarative SFX spec -> float samples, applying the synthesis pipeline."""
from __future__ import annotations

from typing import Any

import numpy as np
from audiolib import (
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


def _envelope(spec: dict[str, Any], duration: float, sample_rate: int) -> Samples:
    return envelope(
        spec.get("shape", "decay"),
        duration,
        sample_rate,
        power=float(spec.get("power", 2.0)),
        attack=float(spec.get("attack", 0.01)),
        decay=float(spec.get("decay", 0.1)),
        sustain=float(spec.get("sustain", 0.6)),
        release=float(spec.get("release", 0.1)),
    )


def _source(layer: dict[str, Any], duration: float, sample_rate: int) -> Samples:
    kind = layer.get("type", "osc")
    if kind == "osc":
        return osc(layer.get("wave", "sine"), float(layer["freq"]), duration, sample_rate)
    if kind == "sweep":
        return sweep(
            layer.get("wave", "sine"),
            float(layer["f0"]),
            float(layer["f1"]),
            duration,
            sample_rate,
            bool(layer.get("exponential", True)),
        )
    if kind == "noise":
        return noise(duration, sample_rate, filter_coef=float(layer.get("filter", 0.0)), seed=int(layer.get("seed", 0)))
    if kind == "fm":
        return fm(
            float(layer["carrier"]),
            float(layer["mod"]),
            float(layer.get("index", 2.0)),
            duration,
            sample_rate,
            layer.get("wave", "sine"),
        )
    raise ValueError(f"unknown layer type: {kind}")


def _build_layer(layer: dict[str, Any], duration: float, sample_rate: int) -> Samples:
    signal = _source(layer, duration, sample_rate)
    if "env" in layer:
        signal = signal * _envelope(layer["env"], duration, sample_rate)
    if "lowpass" in layer:
        signal = low_pass(signal, float(layer["lowpass"]))
    if "highpass" in layer:
        signal = high_pass(signal, float(layer["highpass"]))
    if "bitcrush" in layer:
        signal = bitcrush(signal, int(layer["bitcrush"]))
    if "drive" in layer:
        signal = drive(signal, float(layer["drive"]))
    return signal * float(layer.get("gain", 1.0))


def build_from_spec(spec: dict[str, Any]) -> tuple[Samples, dict[str, Any]]:
    """Build samples from layers, then peak-normalize. Returns (samples, output settings)."""
    duration = float(spec.get("duration", 0.3))
    sample_rate = int(spec.get("sample_rate", 44100))
    layers = [_build_layer(layer, duration, sample_rate) for layer in spec.get("layers", [])]
    samples = mix(layers) if layers else np.zeros(1)
    target = spec.get("normalize", 0.9)
    if target:
        samples = peak_normalize(samples, float(target))
    settings = {
        "sample_rate": sample_rate,
        "channels": int(spec.get("channels", 1)),
        "format": spec.get("format"),
        "quality": int(spec.get("quality", 5)),
    }
    return samples, settings
