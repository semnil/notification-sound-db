from __future__ import annotations

import numpy as np

from notification_sound_db.audio import DecodedAudio, compute_time_metrics


def test_time_metrics_distinguish_full_and_active_rms() -> None:
    samples = np.zeros((1000, 1), dtype=np.float64)
    samples[200:600, 0] = 0.5
    audio = DecodedAudio(
        samples=samples,
        sample_rate=1000,
        channels=1,
        channel_layout="mono",
        codec_name="pcm_f64le",
        codec_long_name="PCM float64",
        sample_format="dbl",
        bits_per_sample=64,
        container_format="wav",
        duration_seconds=1.0,
    )

    result = compute_time_metrics(audio)

    assert result["rms_dbfs"] == -10.0
    assert result["sample_peak_dbfs"] == -6.021
    assert result["sample_crest_factor_db"] == 3.979
    assert result["active_segment"]["start_seconds"] == 0.2
    assert result["active_segment"]["end_seconds"] == 0.6
    assert result["active_segment"]["rms_dbfs"] == -6.021


def test_silence_has_null_levels() -> None:
    audio = DecodedAudio(
        samples=np.zeros((100, 2)),
        sample_rate=1000,
        channels=2,
        channel_layout="stereo",
        codec_name=None,
        codec_long_name=None,
        sample_format=None,
        bits_per_sample=None,
        container_format=None,
        duration_seconds=0.1,
    )
    result = compute_time_metrics(audio)
    assert result["rms_dbfs"] is None
    assert result["active_segment"]["rms_dbfs"] is None
    assert result["active_segment"]["duration_seconds"] == 0.0
