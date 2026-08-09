from __future__ import annotations

import json
from pathlib import Path

from notification_sound_db.audio import (
    ACTIVE_ABSOLUTE_THRESHOLD_DBFS,
    ACTIVE_FRAME_MS,
    ACTIVE_RELATIVE_THRESHOLD_DB,
    ENVELOPE_MAX_POINTS,
    ENVELOPE_MIN_FRAME_MS,
)
from notification_sound_db.loudness import (
    MOMENTARY_WINDOW_SECONDS,
    SHORT_TERM_WINDOW_SECONDS,
    TAIL_PADDING_SECONDS,
)
from notification_sound_db.site import build_site
from notification_sound_db.validation import validate_repository

ROOT = Path(__file__).resolve().parents[1]


def test_current_data_is_valid() -> None:
    assert validate_repository(ROOT) == []


def test_bilingual_static_site_builds(tmp_path: Path) -> None:
    destination = build_site(ROOT, tmp_path / "site")
    assert (destination / "index.html").exists()
    assert (destination / "ja/index.html").exists()
    assert (destination / "methodology.html").exists()
    assert (destination / "ja/methodology.html").exists()
    assert len(list((destination / "sounds").glob("*.html"))) > 0
    assert len(list((destination / "ja/sounds").glob("*.html"))) > 0
    assert (destination / ".nojekyll").exists()
    assert (destination / "assets/language.js").exists()
    english = (destination / "index.html").read_text(encoding="utf-8")
    japanese = (destination / "ja/index.html").read_text(encoding="utf-8")
    assert 'data-source="line"' in english
    assert 'data-source="line"' in japanese
    assert english.count('class="sort-button"') == 8
    assert japanese.count('class="sort-button"') == 8
    assert 'data-sort-integrated="' in english
    assert 'data-sort-true-peak="' in english
    assert '<th class="details-heading">Details</th>' in english
    assert '<th class="details-heading">詳細</th>' in japanese
    assert 'data-label="RMS"' in english
    assert 'data-label="RMS"' in japanese
    assert 'id="table-scroll-controls"' in english
    assert 'id="measurement-table-wrap" class="table-wrap" tabindex="0"' in english
    assert 'src="assets/language.js"' in english
    assert 'src="../assets/language.js"' in japanese
    assert 'hreflang="ja"' in english
    assert 'hreflang="en"' in japanese
    detail_path = next((destination / "sounds").glob("*.html"))
    detail = detail_path.read_text(encoding="utf-8")
    assert 'class="level-chart"' in detail
    assert 'class="chart-level-line"' in detail
    assert "Short-window RMS level over time" in detail


def test_methodology_language_switch_keeps_current_page(tmp_path: Path) -> None:
    destination = build_site(ROOT, tmp_path / "site")
    english = (destination / "methodology.html").read_text(encoding="utf-8")
    japanese = (destination / "ja/methodology.html").read_text(encoding="utf-8")
    assert 'class="language-link" href="ja/methodology.html"' in english
    assert 'class="language-link" href="../methodology.html"' in japanese


def test_analysis_profile_matches_implementation() -> None:
    profile = json.loads((ROOT / "config/analysis-profile.json").read_text(encoding="utf-8"))
    assert profile["rms"]["active_frame_milliseconds"] == ACTIVE_FRAME_MS
    assert profile["rms"]["active_absolute_threshold_dbfs"] == ACTIVE_ABSOLUTE_THRESHOLD_DBFS
    assert profile["rms"]["active_relative_threshold_db"] == ACTIVE_RELATIVE_THRESHOLD_DB
    assert profile["rms"]["envelope"]["minimum_frame_milliseconds"] == ENVELOPE_MIN_FRAME_MS
    assert profile["rms"]["envelope"]["maximum_point_count"] == ENVELOPE_MAX_POINTS
    assert profile["loudness"]["momentary_window_seconds"] == MOMENTARY_WINDOW_SECONDS
    assert profile["loudness"]["short_term_window_seconds"] == SHORT_TERM_WINDOW_SECONDS
    assert profile["loudness"]["tail_padding_seconds"] == TAIL_PADDING_SECONDS


def test_repository_contains_no_source_audio_or_vendor_packages() -> None:
    prohibited = {
        ".aif",
        ".aiff",
        ".caf",
        ".dmg",
        ".flac",
        ".m4a",
        ".mp3",
        ".ogg",
        ".opus",
        ".pkg",
        ".wav",
    }
    found = [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in prohibited
    ]
    assert found == []
