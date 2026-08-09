from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pytest


@pytest.fixture
def sine_wave(tmp_path: Path) -> Path:
    path = tmp_path / "tone.wav"
    sample_rate = 48000
    amplitude = 10 ** (-6 / 20)
    frames = bytearray()
    for index in range(sample_rate):
        value = int(round(32767 * amplitude * math.sin(2 * math.pi * 1000 * index / sample_rate)))
        frames.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(frames)
    return path
