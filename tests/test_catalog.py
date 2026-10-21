from __future__ import annotations

import plistlib
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from notification_sound_db.catalog import (
    SourceDefinition,
    classify,
    source_record,
    update_source,
)
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

    count, analyzed, failed = update_source(repository, _application_definition(bundle), bundle)

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


def _application_definition(bundle: Path) -> SourceDefinition:
    return SourceDefinition(
        id="example",
        vendor="Example",
        names={"en": "Example", "ja": "Example"},
        kind="application",
        default_path=bundle,
        official_url="https://example.com/",
        default_event_type="unknown",
    )


def _write_plist(path: Path, bundle_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        plistlib.dump({"CFBundleIdentifier": bundle_id}, handle)


def test_source_record_reads_the_bundle_info_plist(tmp_path: Path) -> None:
    bundle = tmp_path / "Example.app"
    _write_plist(bundle / "Contents/Info.plist", "com.example.inside")

    record = source_record(_application_definition(bundle), bundle, [])
    assert record["application"]["bundle_id"] == "com.example.inside"


def test_source_record_does_not_read_an_info_plist_that_leaves_the_bundle(
    tmp_path: Path,
) -> None:
    outside_plist = tmp_path / "outside.plist"
    _write_plist(outside_plist, "com.example.outside")
    bundle = tmp_path / "Example.app"
    (bundle / "Contents").mkdir(parents=True)
    try:
        (bundle / "Contents/Info.plist").symlink_to(outside_plist)
    except OSError as exc:
        pytest.skip(f"symbolic links cannot be created here: {exc}")

    record = source_record(_application_definition(bundle), bundle, [])
    assert record["application"]["bundle_id"] is None
