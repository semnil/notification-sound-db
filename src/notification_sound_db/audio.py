"""Decode audio and compute time-domain measurements."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from notification_sound_db.process import MediaToolError, probe, run_process

DB_FLOOR = -200.0
ACTIVE_FRAME_MS = 10.0
ACTIVE_ABSOLUTE_THRESHOLD_DBFS = -60.0
ACTIVE_RELATIVE_THRESHOLD_DB = -40.0


@dataclass(frozen=True)
class DecodedAudio:
    samples: np.ndarray
    sample_rate: int
    channels: int
    channel_layout: str | None
    codec_name: str | None
    codec_long_name: str | None
    sample_format: str | None
    bits_per_sample: int | None
    container_format: str | None
    duration_seconds: float


def linear_to_db(amplitude: float) -> float | None:
    if amplitude <= 0 or not math.isfinite(amplitude):
        return None
    return 20.0 * math.log10(amplitude)


def _audio_stream(metadata: dict) -> dict:
    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "audio":
            return stream
    raise MediaToolError("No audio stream found")


def decode(path: Path) -> DecodedAudio:
    """Decode the first audio stream to interleaved float64 without resampling."""
    metadata = probe(path)
    stream = _audio_stream(metadata)
    sample_rate = int(stream["sample_rate"])
    channels = int(stream["channels"])
    result = run_process(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-vn",
            "-sn",
            "-dn",
            "-f",
            "f64le",
            "-acodec",
            "pcm_f64le",
            "-",
        ]
    )
    raw = np.frombuffer(result.stdout, dtype="<f8")
    if raw.size == 0:
        raise MediaToolError("Decoded audio was empty")
    remainder = raw.size % channels
    if remainder:
        raw = raw[:-remainder]
    samples = raw.reshape((-1, channels)).copy()
    samples = np.nan_to_num(samples, nan=0.0, posinf=1.0, neginf=-1.0)
    duration = samples.shape[0] / sample_rate
    bits = stream.get("bits_per_raw_sample") or stream.get("bits_per_sample")
    return DecodedAudio(
        samples=samples,
        sample_rate=sample_rate,
        channels=channels,
        channel_layout=stream.get("channel_layout"),
        codec_name=stream.get("codec_name"),
        codec_long_name=stream.get("codec_long_name"),
        sample_format=stream.get("sample_fmt"),
        bits_per_sample=int(bits) if bits not in (None, "", "0", 0) else None,
        container_format=metadata.get("format", {}).get("format_name"),
        duration_seconds=duration,
    )


def _rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))


def _active_bounds(samples: np.ndarray, sample_rate: int) -> tuple[int, int, float] | None:
    """Return the first/last active frame bounds and the chosen threshold.

    Activity is measured over non-overlapping 10 ms frames after combining
    channel energy. The threshold is max(-60 dBFS, peak frame RMS - 40 dB).
    """
    frame_size = max(1, round(sample_rate * ACTIVE_FRAME_MS / 1000.0))
    frame_count = math.ceil(samples.shape[0] / frame_size)
    padded_count = frame_count * frame_size
    if padded_count != samples.shape[0]:
        padded = np.pad(samples, ((0, padded_count - samples.shape[0]), (0, 0)))
    else:
        padded = samples
    frames = padded.reshape(frame_count, frame_size, samples.shape[1])
    frame_rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=(1, 2)))
    peak_frame_db = linear_to_db(float(np.max(frame_rms)))
    if peak_frame_db is None:
        return None
    threshold_db = max(
        ACTIVE_ABSOLUTE_THRESHOLD_DBFS,
        peak_frame_db + ACTIVE_RELATIVE_THRESHOLD_DB,
    )
    threshold_linear = 10.0 ** (threshold_db / 20.0)
    active = np.flatnonzero(frame_rms >= threshold_linear)
    if active.size == 0:
        return None
    start = int(active[0]) * frame_size
    end = min((int(active[-1]) + 1) * frame_size, samples.shape[0])
    return start, end, threshold_db


def compute_time_metrics(audio: DecodedAudio) -> dict:
    samples = audio.samples
    channel_rms = [_rms(samples[:, index]) for index in range(audio.channels)]
    channel_peaks = [float(np.max(np.abs(samples[:, index]))) for index in range(audio.channels)]
    combined_rms = _rms(samples)
    sample_peak = max(channel_peaks)
    bounds = _active_bounds(samples, audio.sample_rate)
    if bounds is None:
        active = {
            "threshold_dbfs": None,
            "start_seconds": None,
            "end_seconds": None,
            "duration_seconds": 0.0,
            "leading_silence_seconds": audio.duration_seconds,
            "trailing_silence_seconds": 0.0,
            "rms_dbfs": None,
        }
    else:
        start, end, threshold_db = bounds
        active_rms = _rms(samples[start:end])
        active = {
            "threshold_dbfs": round(threshold_db, 3),
            "start_seconds": round(start / audio.sample_rate, 6),
            "end_seconds": round(end / audio.sample_rate, 6),
            "duration_seconds": round((end - start) / audio.sample_rate, 6),
            "leading_silence_seconds": round(start / audio.sample_rate, 6),
            "trailing_silence_seconds": round(
                (samples.shape[0] - end) / audio.sample_rate, 6
            ),
            "rms_dbfs": _round_nullable(linear_to_db(active_rms)),
        }
    rms_dbfs = linear_to_db(combined_rms)
    peak_dbfs = linear_to_db(sample_peak)
    return {
        "rms_dbfs": _round_nullable(rms_dbfs),
        "sample_peak_dbfs": _round_nullable(peak_dbfs),
        "sample_crest_factor_db": (
            round(peak_dbfs - rms_dbfs, 3)
            if peak_dbfs is not None and rms_dbfs is not None
            else None
        ),
        "channels": [
            {
                "index": index,
                "rms_dbfs": _round_nullable(linear_to_db(channel_rms[index])),
                "sample_peak_dbfs": _round_nullable(linear_to_db(channel_peaks[index])),
            }
            for index in range(audio.channels)
        ],
        "active_segment": active,
    }


def mono_energy_mix(samples: np.ndarray) -> np.ndarray:
    """Return an arithmetic channel mean for descriptive spectral analysis."""
    return np.mean(samples, axis=1, dtype=np.float64)


def _round_nullable(value: float | None, digits: int = 3) -> float | None:
    return round(value, digits) if value is not None and math.isfinite(value) else None
