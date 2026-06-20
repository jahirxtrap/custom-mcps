from __future__ import annotations

import numpy as np
import pytest
from sfx_mcp.builder import build_from_spec


def test_build_normalizes_to_target():
    spec = {
        "duration": 0.2,
        "normalize": 0.9,
        "layers": [{"type": "osc", "wave": "sine", "freq": 440, "env": {"shape": "decay", "power": 2}}],
    }
    samples, settings = build_from_spec(spec)
    assert abs(float(np.max(np.abs(samples))) - 0.9) < 1e-2
    assert settings["sample_rate"] == 44100
    assert settings["channels"] == 1


def test_build_layers_mix():
    spec = {
        "duration": 0.1,
        "layers": [
            {"type": "sweep", "wave": "saw", "f0": 200, "f1": 800, "gain": 0.6},
            {"type": "noise", "filter": 0.8, "gain": 0.3},
        ],
    }
    samples, _ = build_from_spec(spec)
    assert len(samples) == int(0.1 * 44100)
    assert float(np.max(np.abs(samples))) > 0


def test_build_respects_settings():
    spec = {
        "duration": 0.05,
        "sample_rate": 22050,
        "channels": 2,
        "format": "wav",
        "quality": 3,
        "layers": [{"type": "osc", "freq": 440}],
    }
    _, settings = build_from_spec(spec)
    assert settings == {"sample_rate": 22050, "channels": 2, "format": "wav", "quality": 3}


def test_normalize_can_be_disabled():
    spec = {"duration": 0.05, "normalize": 0, "layers": [{"type": "osc", "freq": 440, "gain": 0.3}]}
    samples, _ = build_from_spec(spec)
    assert float(np.max(np.abs(samples))) < 0.5


def test_unknown_layer_type_raises():
    with pytest.raises(ValueError):
        build_from_spec({"layers": [{"type": "bogus"}]})
