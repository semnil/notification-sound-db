from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from notification_sound_db.catalog import SourceDefinition, classify, update_source
from notification_sound_db.jsonio import read_json

ROOT = Path(__file__).resolve().parents[1]


def test_classification_rules() -> None:
    assert classify("calls_incoming_ring_v2", "unknown") == "incoming_call"
    assert classify("calls_they_joined_call_v2", "unknown") == "call_state"
    assert classify("Mail Fetch Error", "unknown") == "error"
    assert classify("Mail Sent", "unknown") == "completion"
    assert classify("discord_message1", "unknown") == "message"
    assert classify("mystery", "unknown") == "unknown"


def test_update_does_not_read_links_that_leave_the_source(
    tmp_path: Path, sine_wave: Path
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    shutil.copy(sine_wave, bundle / "inside.wav")
    outside = tmp_path / "outside"
    outside.mkdir()
    shutil.copy(sine_wave, outside / "private.wav")
    try:
        (bundle / "link.wav").symlink_to(outside / "private.wav")
    except OSError as exc:
        pytest.skip(f"symbolic links cannot be created here: {exc}")
    repository = tmp_path / "repository"
    definition = SourceDefinition(
        id="example",
        vendor="Example",
        names={"en": "Example", "ja": "Example"},
        kind="application",
        default_path=bundle,
        official_url="https://example.com/",
        default_event_type="unknown",
    )

    count, analyzed, failed = update_source(repository, definition, bundle)

    record = read_json(repository / "data/sources/example.json")
    assert (count, analyzed, failed) == (2, 1, 1)
    assert [sound["relative_path"] for sound in record["sounds"]] == ["inside.wav"]
    assert record["measurement_failures"] == [
        {
            "name": "link",
            "relative_path": "link.wav",
            "sha256": None,
            "error_type": "OutsideSourcePath",
            "reason": "A symbolic link resolves outside the source path; not read.",
        }
    ]
    schema = read_json(ROOT / "data/schemas/source.schema.json")
    Draft202012Validator(schema).validate(record)
