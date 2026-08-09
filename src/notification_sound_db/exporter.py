"""Create a flat, human-readable CSV export from canonical JSON records."""

from __future__ import annotations

import csv
from pathlib import Path

from notification_sound_db.jsonio import read_json

FIELDS = [
    "source_id",
    "source_name_en",
    "source_name_ja",
    "vendor",
    "platform_version",
    "application_version",
    "application_build",
    "observed_at",
    "acquisition_method",
    "official_url",
    "distribution_url",
    "distribution_sha256",
    "sound_name",
    "event_type",
    "relative_path",
    "sha256",
    "duration_seconds",
    "sample_rate_hz",
    "channel_count",
    "integrated_lufs",
    "maximum_momentary_lufs",
    "maximum_short_term_lufs",
    "loudness_range_lu",
    "true_peak_dbtp",
    "sample_peak_dbfs",
    "rms_dbfs",
    "active_rms_dbfs",
    "sample_crest_factor_db",
    "true_peak_crest_factor_db",
    "spectral_centroid_hz",
    "peak_frequency_hz",
    "speech_band_200_8000_hz_energy_percent",
    "analysis_profile",
    "ffmpeg_version",
    "analyzed_at",
]


def records(repository: Path) -> list[dict]:
    assets = {
        path.stem: read_json(path) for path in sorted((repository / "data/assets").glob("*.json"))
    }
    rows = []
    for path in sorted((repository / "data/sources").glob("*.json")):
        source = read_json(path)
        for sound in source["sounds"]:
            asset = assets[sound["asset_sha256"]]
            row = {
                "source_id": source["source_id"],
                "source_name_en": source["names"]["en"],
                "source_name_ja": source["names"]["ja"],
                "vendor": source["vendor"],
                "platform_version": source["platform"]["version"],
                "application_version": source["application"]["version"],
                "application_build": source["application"]["build"],
                "observed_at": source["observed_at"],
                "acquisition_method": source["acquisition"]["method"],
                "official_url": source["acquisition"]["official_url"],
                "distribution_url": source["acquisition"]["distribution_url"],
                "distribution_sha256": source["acquisition"]["distribution_sha256"],
                "sound_name": sound["name"],
                "event_type": sound["event_type"],
                "relative_path": sound["relative_path"],
                "sha256": sound["asset_sha256"],
                "duration_seconds": asset["audio"]["duration_seconds"],
                "sample_rate_hz": asset["audio"]["sample_rate_hz"],
                "channel_count": asset["audio"]["channel_count"],
                "integrated_lufs": asset["loudness"]["integrated_lufs"],
                "maximum_momentary_lufs": asset["loudness"]["maximum_momentary_lufs"],
                "maximum_short_term_lufs": asset["loudness"]["maximum_short_term_lufs"],
                "loudness_range_lu": asset["loudness"]["loudness_range_lu"],
                "true_peak_dbtp": asset["loudness"]["true_peak_dbtp"],
                "sample_peak_dbfs": asset["levels"]["sample_peak_dbfs"],
                "rms_dbfs": asset["levels"]["rms_dbfs"],
                "active_rms_dbfs": asset["levels"]["active_segment"]["rms_dbfs"],
                "sample_crest_factor_db": asset["levels"]["sample_crest_factor_db"],
                "true_peak_crest_factor_db": asset["levels"][
                    "true_peak_crest_factor_db"
                ],
                "spectral_centroid_hz": asset["spectrum"]["spectral_centroid_hz"],
                "peak_frequency_hz": asset["spectrum"]["peak_frequency_hz"],
                "speech_band_200_8000_hz_energy_percent": asset["spectrum"][
                    "speech_band_200_8000_hz_energy_percent"
                ],
                "analysis_profile": asset["analysis_profile"],
                "ffmpeg_version": asset["toolchain"]["ffmpeg"],
                "analyzed_at": asset["analyzed_at"],
            }
            rows.append(row)
    return rows


def write_csv(repository: Path, output: Path | None = None) -> Path:
    destination = output or repository / "data/exports/measurements.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records(repository))
    return destination
