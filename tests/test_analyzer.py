from __future__ import annotations

import shutil

import pytest

from notification_sound_db.analyzer import analyze


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg required"
)
def test_analyzer_measures_known_sine(sine_wave) -> None:
    result = analyze(sine_wave)

    assert result["sha256"]
    assert result["audio"]["sample_rate_hz"] == 48000
    assert result["audio"]["channel_count"] == 1
    assert result["levels"]["sample_peak_dbfs"] == pytest.approx(-6.0, abs=0.02)
    assert result["levels"]["rms_dbfs"] == pytest.approx(-9.01, abs=0.03)
    assert result["loudness"]["integrated_lufs"] is not None
    assert result["loudness"]["true_peak_dbtp"] == pytest.approx(-6.0, abs=0.2)
