from __future__ import annotations

import numpy as np
from audiolib import (
    bitcrush,
    envelope,
    inspect,
    mix,
    noise,
    osc,
    peak_normalize,
    read,
    sweep,
    waveform_image,
    write,
)

SR = 44100


def _zero_crossings(x):
    return np.sum(np.abs(np.diff(np.sign(x)))) / 2


def test_osc_length_and_range():
    s = osc("sine", 440, 0.1, SR)
    assert len(s) == int(0.1 * SR)
    assert np.max(np.abs(s)) <= 1.0 + 1e-6


def test_waves_are_distinct():
    assert not np.allclose(osc("sine", 220, 0.05, SR), osc("square", 220, 0.05, SR))


def test_sweep_changes_frequency():
    s = sweep("sine", 100, 2000, 0.2, SR)
    half = len(s) // 2
    assert _zero_crossings(s[half:]) > _zero_crossings(s[:half])


def test_noise_filter_smooths():
    raw = noise(0.1, SR, 0.0, seed=1)
    smooth = noise(0.1, SR, 0.9, seed=1)
    assert np.mean(np.abs(np.diff(smooth))) < np.mean(np.abs(np.diff(raw)))


def test_envelope_decay_decreasing():
    e = envelope("decay", 0.1, SR, power=2)
    assert e[0] > e[-1]
    assert e[0] <= 1.0 + 1e-6


def test_envelope_ar_rises_then_falls():
    e = envelope("ar", 0.2, SR, attack=0.05)
    a = int(0.05 * SR)
    assert e[a - 1] > e[0]
    assert e[-1] < e[a - 1]


def test_peak_normalize_hits_target():
    s = osc("sine", 440, 0.1, SR) * 0.2
    n = peak_normalize(s, 0.9)
    assert abs(float(np.max(np.abs(n))) - 0.9) < 1e-3


def test_mix_sums_and_keeps_longest():
    m = mix([np.ones(10), np.ones(5)])
    assert len(m) == 10
    assert m[0] == 2 and m[7] == 1


def test_bitcrush_reduces_levels():
    s = osc("sine", 440, 0.05, SR)
    assert len(np.unique(bitcrush(s, 3))) < len(np.unique(s))


def test_write_read_roundtrip_wav(tmp_path):
    s = peak_normalize(osc("sine", 440, 0.1, SR), 0.9)
    p = tmp_path / "t.wav"
    write(s, p, sample_rate=SR, encoder="soundfile")
    data, sr = read(p)
    assert sr == SR
    assert abs(float(np.max(np.abs(data))) - 0.9) < 0.02


def test_write_ogg_via_soundfile(tmp_path):
    s = peak_normalize(osc("sine", 440, 0.2, SR), 0.9)
    p = tmp_path / "t.ogg"
    write(s, p, sample_rate=SR, encoder="soundfile")
    assert p.exists() and p.stat().st_size > 0
    report = inspect(p)
    assert report["sample_rate"] == SR
    assert report["duration"] > 0.1


def test_waveform_image_size():
    img = waveform_image(osc("sine", 440, 0.1, SR), width=320, height=120)
    assert img.size == (320, 120)
