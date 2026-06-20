"""Synthesis primitives: oscillators, noise, sweeps, FM, envelopes, shaping, mix, normalize."""
from __future__ import annotations

import numpy as np

Samples = np.ndarray
_TWO_PI = 2 * np.pi


def _time(duration: float, sample_rate: int) -> Samples:
    n = max(1, int(round(duration * sample_rate)))
    return np.linspace(0.0, duration, n, endpoint=False)


def _wave(shape: str, phase: Samples) -> Samples:
    if shape == "sine":
        return np.sin(phase)
    if shape == "square":
        return np.sign(np.sin(phase))
    frac = phase / _TWO_PI
    if shape == "saw":
        return 2.0 * (frac - np.floor(frac + 0.5))
    if shape == "triangle":
        return 2.0 * np.abs(2.0 * (frac - np.floor(frac + 0.5))) - 1.0
    raise ValueError(f"unknown wave: {shape}")


def osc(wave: str, freq: float, duration: float, sample_rate: int) -> Samples:
    t = _time(duration, sample_rate)
    return _wave(wave, _TWO_PI * freq * t)


def sweep(
    wave: str, f0: float, f1: float, duration: float, sample_rate: int, exponential: bool = True
) -> Samples:
    t = _time(duration, sample_rate)
    span = max(duration, 1e-9)
    if exponential and f0 > 0 and f1 > 0:
        freq = f0 * (f1 / f0) ** (t / span)
    else:
        freq = f0 + (f1 - f0) * (t / span)
    phase = _TWO_PI * np.cumsum(freq) / sample_rate
    return _wave(wave, phase)


def fm(
    carrier: float, mod_freq: float, index: float, duration: float, sample_rate: int, wave: str = "sine"
) -> Samples:
    t = _time(duration, sample_rate)
    return _wave(wave, _TWO_PI * carrier * t + index * np.sin(_TWO_PI * mod_freq * t))


def ring_mod(freq_a: float, freq_b: float, duration: float, sample_rate: int, wave: str = "sine") -> Samples:
    t = _time(duration, sample_rate)
    return _wave(wave, _TWO_PI * freq_a * t) * _wave(wave, _TWO_PI * freq_b * t)


def pluck(freq: float, duration: float, sample_rate: int, decay: float = 0.996, seed: int = 0) -> Samples:
    n = len(_time(duration, sample_rate))
    period = max(2, int(sample_rate / max(freq, 1.0)))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1.0, 1.0, period)
    out = np.empty(n)
    for i in range(n):
        idx = i % period
        out[i] = buf[idx]
        buf[idx] = decay * 0.5 * (buf[idx] + buf[(i + 1) % period])
    return out


def noise(duration: float, sample_rate: int, filter_coef: float = 0.0, seed: int = 0) -> Samples:
    n = len(_time(duration, sample_rate))
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1.0, 1.0, n)
    if filter_coef <= 0.0:
        return x
    y = np.empty_like(x)
    prev = 0.0
    keep = float(filter_coef)
    for i in range(n):
        prev = prev * keep + x[i] * (1.0 - keep)
        y[i] = prev
    return y


def envelope(
    shape: str,
    duration: float,
    sample_rate: int,
    power: float = 2.0,
    attack: float = 0.01,
    decay: float = 0.1,
    sustain: float = 0.6,
    release: float = 0.1,
) -> Samples:
    n = len(_time(duration, sample_rate))
    if shape == "decay":
        tn = np.linspace(0.0, 1.0, n, endpoint=False)
        return np.power(np.clip(1.0 - tn, 0.0, 1.0), power)
    if shape == "hump":
        tn = np.linspace(0.0, 1.0, n, endpoint=False)
        return np.power(np.sin(np.pi * tn), power)
    env = np.zeros(n)
    a = min(n, max(0, int(attack * sample_rate)))
    if shape == "ar":
        if a:
            env[:a] = np.linspace(0.0, 1.0, a)
        rest = n - a
        if rest > 0:
            env[a:] = np.linspace(1.0, 0.0, rest)
        return env
    d = min(n - a, max(0, int(decay * sample_rate)))
    r = min(n - a - d, max(0, int(release * sample_rate)))
    s = max(0, n - a - d - r)
    i = 0
    if a:
        env[i : i + a] = np.linspace(0.0, 1.0, a)
        i += a
    if d:
        env[i : i + d] = np.linspace(1.0, sustain, d)
        i += d
    if s:
        env[i : i + s] = sustain
        i += s
    if r:
        env[i : i + r] = np.linspace(sustain, 0.0, r)
    return env


def low_pass(samples: Samples, coef: float) -> Samples:
    if coef <= 0.0:
        return samples
    y = np.empty_like(samples)
    prev = 0.0
    keep = float(coef)
    for i in range(len(samples)):
        prev = prev * keep + samples[i] * (1.0 - keep)
        y[i] = prev
    return y


def high_pass(samples: Samples, coef: float) -> Samples:
    return samples - low_pass(samples, coef)


def bitcrush(samples: Samples, bits: int) -> Samples:
    if bits <= 0 or bits >= 16:
        return samples
    levels = float(2**bits)
    return np.round(samples * (levels / 2.0)) / (levels / 2.0)


def drive(samples: Samples, amount: float) -> Samples:
    if amount <= 0.0:
        return samples
    return np.tanh(samples * (1.0 + amount))


def mix(layers: list[Samples]) -> Samples:
    if not layers:
        return np.zeros(1)
    n = max(len(layer) for layer in layers)
    out = np.zeros(n)
    for layer in layers:
        out[: len(layer)] += layer
    return out


def peak_normalize(samples: Samples, target: float = 0.9) -> Samples:
    if target <= 0.0:
        return samples
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak == 0.0:
        return samples
    return samples * (target / peak)
