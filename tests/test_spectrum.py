from __future__ import annotations

import numpy as np

from notification_sound_db.spectrum import measure_spectrum


def test_spectrum_finds_sine_peak_and_populates_narrow_bands() -> None:
    sample_rate = 48000
    time = np.arange(sample_rate, dtype=np.float64) / sample_rate
    tone = 0.5 * np.sin(2 * np.pi * 1000 * time)

    result = measure_spectrum(tone, sample_rate)

    assert abs(result["peak_frequency_hz"] - 1000) < 15
    assert abs(result["spectral_centroid_hz"] - 1000) < 15
    assert result["speech_band_200_8000_hz_energy_percent"] > 99
    assert all(
        band["energy_dbfs"] is not None
        for band in result["third_octave_band_energy_dbfs"]
    )
