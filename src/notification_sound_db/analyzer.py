"""Compose all measurements into one hash-addressed asset record."""

from __future__ import annotations

import hashlib
from pathlib import Path

from notification_sound_db import ANALYSIS_PROFILE, SCHEMA_VERSION, __version__
from notification_sound_db.audio import compute_time_metrics, decode, mono_energy_mix
from notification_sound_db.jsonio import timestamp_now
from notification_sound_db.loudness import measure_loudness
from notification_sound_db.process import tool_version
from notification_sound_db.spectrum import measure_spectrum


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze(path: Path, *, sha256: str | None = None) -> dict:
    resolved_hash = sha256 or sha256_file(path)
    audio = decode(path)
    levels = compute_time_metrics(audio)
    loudness = measure_loudness(path, audio.duration_seconds)
    if loudness["true_peak_dbtp"] is not None and levels["rms_dbfs"] is not None:
        levels["true_peak_crest_factor_db"] = round(
            loudness["true_peak_dbtp"] - levels["rms_dbfs"], 3
        )
    else:
        levels["true_peak_crest_factor_db"] = None
    spectrum = measure_spectrum(mono_energy_mix(audio.samples), audio.sample_rate)
    return {
        "$schema": "../schemas/asset.schema.json",
        "schema_version": SCHEMA_VERSION,
        "sha256": resolved_hash,
        "analysis_profile": ANALYSIS_PROFILE,
        "analyzed_at": timestamp_now(),
        "file": {
            "byte_size": path.stat().st_size,
            "extension": path.suffix.lower(),
            "container_format": audio.container_format,
            "codec_name": audio.codec_name,
            "codec_long_name": audio.codec_long_name,
            "sample_format": audio.sample_format,
            "bits_per_sample": audio.bits_per_sample,
        },
        "audio": {
            "duration_seconds": round(audio.duration_seconds, 6),
            "sample_rate_hz": audio.sample_rate,
            "channel_count": audio.channels,
            "channel_layout": audio.channel_layout,
        },
        "loudness": loudness,
        "levels": levels,
        "spectrum": spectrum,
        "toolchain": {
            "notification_sound_db": __version__,
            "ffmpeg": tool_version("ffmpeg"),
            "ffprobe": tool_version("ffprobe"),
        },
    }
