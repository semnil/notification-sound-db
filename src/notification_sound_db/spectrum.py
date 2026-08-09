"""Descriptive spectral measurements for short notification sounds."""

from __future__ import annotations

import math

import numpy as np
from scipy import signal

THIRD_OCTAVE_CENTERS = np.array(
    [
        25,
        31.5,
        40,
        50,
        63,
        80,
        100,
        125,
        160,
        200,
        250,
        315,
        400,
        500,
        630,
        800,
        1000,
        1250,
        1600,
        2000,
        2500,
        3150,
        4000,
        5000,
        6300,
        8000,
        10000,
        12500,
        16000,
    ]
)
THIRD_OCTAVE_FACTOR = 2 ** (1 / 6)
BROAD_BANDS = {
    "sub_20_80_hz": (20.0, 80.0),
    "low_80_200_hz": (80.0, 200.0),
    "low_mid_200_500_hz": (200.0, 500.0),
    "mid_500_2000_hz": (500.0, 2000.0),
    "presence_2000_5000_hz": (2000.0, 5000.0),
    "high_5000_10000_hz": (5000.0, 10000.0),
}


def _db_power(value: float) -> float | None:
    if value <= 0 or not math.isfinite(value):
        return None
    return 10.0 * math.log10(value)


def _band_energy(freqs: np.ndarray, psd: np.ndarray, low: float, high: float) -> float:
    high = min(high, float(freqs[-1]))
    mask = (freqs >= low) & (freqs < high)
    if freqs.size < 2 or high <= low:
        return 0.0
    selected = int(np.count_nonzero(mask))
    if selected == 0:
        center = math.sqrt(low * high)
        return float(np.interp(center, freqs, psd) * (high - low))
    if selected == 1:
        return float(psd[mask][0] * (high - low))
    return float(np.trapezoid(psd[mask], freqs[mask]))


def measure_spectrum(mono: np.ndarray, sample_rate: int) -> dict:
    if mono.size < 2:
        raise ValueError("At least two decoded samples are required")
    segment_size = min(4096, mono.size)
    overlap = min(segment_size // 2, segment_size - 1)
    freqs, psd = signal.welch(
        mono,
        fs=sample_rate,
        window="hann",
        nperseg=segment_size,
        noverlap=overlap,
        detrend=False,
        scaling="density",
    )
    usable = (freqs >= 20.0) & (freqs <= min(20000.0, sample_rate / 2.0))
    usable_freqs = freqs[usable]
    usable_psd = psd[usable]
    total_energy = (
        float(np.trapezoid(usable_psd, usable_freqs)) if usable_freqs.size > 1 else 0.0
    )
    if total_energy > 0:
        centroid = float(np.sum(usable_freqs * usable_psd) / np.sum(usable_psd))
        peak_frequency = float(usable_freqs[int(np.argmax(usable_psd))])
    else:
        centroid = None
        peak_frequency = None

    broad = {
        key: _round_nullable(_db_power(_band_energy(freqs, psd, low, high)))
        for key, (low, high) in BROAD_BANDS.items()
    }
    speech_energy = _band_energy(freqs, psd, 200.0, 8000.0)
    speech_ratio = 100.0 * speech_energy / total_energy if total_energy > 0 else None

    third_octave = []
    for center in THIRD_OCTAVE_CENTERS:
        low = center / THIRD_OCTAVE_FACTOR
        high = center * THIRD_OCTAVE_FACTOR
        if low >= sample_rate / 2.0:
            continue
        energy = _band_energy(freqs, psd, low, high)
        third_octave.append(
            {
                "center_hz": float(center),
                "energy_dbfs": _round_nullable(_db_power(energy)),
            }
        )

    return {
        "method": "Welch PSD, Hann window, 4096-sample maximum segment",
        "spectral_centroid_hz": _round_nullable(centroid),
        "peak_frequency_hz": _round_nullable(peak_frequency),
        "speech_band_200_8000_hz_energy_percent": _round_nullable(speech_ratio),
        "broad_band_energy_dbfs": broad,
        "third_octave_band_energy_dbfs": third_octave,
    }


def _round_nullable(value: float | None, digits: int = 3) -> float | None:
    return round(value, digits) if value is not None and math.isfinite(value) else None
