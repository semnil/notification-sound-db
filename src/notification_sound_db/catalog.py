"""Discover configured notification sounds and update the current snapshot."""

from __future__ import annotations

import platform
import plistlib
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from notification_sound_db import ANALYSIS_PROFILE, SCHEMA_VERSION
from notification_sound_db.analyzer import analyze, sha256_file
from notification_sound_db.jsonio import read_json, timestamp_now, write_json

AUDIO_EXTENSIONS = {".aif", ".aiff", ".caf", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}

CLASSIFICATION_RULES = [
    (
        re.compile(r"incoming|ringtone|calling|ringback|ringing|callwaitingring", re.I),
        "incoming_call",
    ),
    (re.compile(r"join|left|leave|hangup|call|huddle|mute|deafen", re.I), "call_state"),
    (re.compile(r"error|fail", re.I), "error"),
    (re.compile(r"complete|confirm|sent|delivery|success|checkout", re.I), "completion"),
    (re.compile(r"message|mail|mention|notification|notify", re.I), "message"),
    (re.compile(r"click|pop|boop|snapshot|received|action|skip", re.I), "ui_feedback"),
]


@dataclass(frozen=True)
class SourceDefinition:
    id: str
    vendor: str
    names: dict[str, str]
    kind: str
    default_path: Path
    official_url: str
    default_event_type: str


def project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "config/sources.json").exists():
            return candidate
    raise FileNotFoundError("Run this command inside the notification-sound-db repository")


def load_sources(root: Path) -> list[SourceDefinition]:
    config = read_json(root / "config/sources.json")
    return [
        SourceDefinition(
            id=item["id"],
            vendor=item["vendor"],
            names=item["names"],
            kind=item["kind"],
            default_path=Path(item["default_path"]),
            official_url=item["official_url"],
            default_event_type=item["default_event_type"],
        )
        for item in config["sources"]
    ]


def discover_audio(root: Path) -> list[Path]:
    if root.is_file() and root.suffix.lower() in AUDIO_EXTENSIONS:
        return [root]
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
        ),
        key=lambda item: item.relative_to(root).as_posix().casefold(),
    )


def classify(filename: str, default: str) -> str:
    for pattern, event_type in CLASSIFICATION_RULES:
        if pattern.search(filename):
            return event_type
    return default


def _plist_metadata(path: Path) -> dict:
    plist_path = path / "Contents/Info.plist"
    if not plist_path.exists():
        return {}
    try:
        with plist_path.open("rb") as handle:
            value = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        return {}
    return {
        "bundle_id": value.get("CFBundleIdentifier"),
        "version": value.get("CFBundleShortVersionString"),
        "build": value.get("CFBundleVersion"),
    }


def _command_text(command: list[str]) -> str | None:
    try:
        return subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def platform_metadata() -> dict:
    return {
        "id": "macos",
        "version": _command_text(["sw_vers", "-productVersion"]) or platform.mac_ver()[0],
        "build": _command_text(["sw_vers", "-buildVersion"]),
        "architecture": platform.machine(),
    }


def source_record(
    definition: SourceDefinition,
    bundle_path: Path,
    sounds: Iterable[tuple[Path, str]],
    *,
    measurement_failures: list[dict] | None = None,
    distribution_url: str | None = None,
    distribution_sha256: str | None = None,
) -> dict:
    bundle = _plist_metadata(bundle_path) if bundle_path.suffix == ".app" else {}
    current_platform = platform_metadata()
    occurrences = []
    for path, digest in sounds:
        occurrences.append(
            {
                "asset_sha256": digest,
                "name": path.stem,
                "relative_path": path.relative_to(bundle_path).as_posix(),
                "event_type": classify(path.stem, definition.default_event_type),
            }
        )
    return {
        "$schema": "../schemas/source.schema.json",
        "schema_version": SCHEMA_VERSION,
        "source_id": definition.id,
        "names": definition.names,
        "vendor": definition.vendor,
        "kind": definition.kind,
        "platform": current_platform,
        "application": {
            "bundle_id": bundle.get("bundle_id"),
            "version": bundle.get("version") or current_platform["version"],
            "build": bundle.get("build") or current_platform["build"],
        },
        "observed_at": timestamp_now(),
        "analysis_profile": ANALYSIS_PROFILE,
        "acquisition": {
            "method": "official_distribution" if distribution_url else "local_installation",
            "official_url": definition.official_url,
            "distribution_url": distribution_url,
            "distribution_sha256": distribution_sha256,
            "metadata_url": None,
        },
        "collection": {"status": "measured", "reason_code": None, "reason": None},
        "sounds": occurrences,
        "measurement_failures": measurement_failures or [],
    }


def update_source(
    repository: Path,
    definition: SourceDefinition,
    bundle_path: Path,
    *,
    force: bool = False,
    distribution_url: str | None = None,
    distribution_sha256: str | None = None,
) -> tuple[int, int, int]:
    paths = discover_audio(bundle_path)
    if not paths:
        raise FileNotFoundError(f"No supported audio files found under {bundle_path}")
    asset_dir = repository / "data/assets"
    analyzed = 0
    references: list[tuple[Path, str]] = []
    failures: list[dict] = []
    for path in paths:
        digest = sha256_file(path)
        target = asset_dir / f"{digest}.json"
        references.append((path, digest))
        if target.exists() and not force:
            existing = read_json(target)
            if existing.get("analysis_profile") == ANALYSIS_PROFILE:
                continue
        try:
            write_json(target, analyze(path, sha256=digest))
            analyzed += 1
        except RuntimeError as exc:
            reason = str(exc).replace(str(path), "<source-file>")
            failures.append(
                {
                    "name": path.stem,
                    "relative_path": path.relative_to(bundle_path).as_posix(),
                    "sha256": digest,
                    "error_type": type(exc).__name__,
                    "reason": reason[-1000:],
                }
            )
            references.pop()
    record = source_record(
        definition,
        bundle_path,
        references,
        measurement_failures=failures,
        distribution_url=distribution_url,
        distribution_sha256=distribution_sha256,
    )
    write_json(repository / f"data/sources/{definition.id}.json", record)
    remove_unreferenced_assets(repository)
    return len(paths), analyzed, len(failures)


def remove_unreferenced_assets(repository: Path) -> list[str]:
    referenced: set[str] = set()
    for source_path in sorted((repository / "data/sources").glob("*.json")):
        source = read_json(source_path)
        referenced.update(sound["asset_sha256"] for sound in source.get("sounds", []))
    removed = []
    for asset_path in sorted((repository / "data/assets").glob("*.json")):
        if asset_path.stem not in referenced:
            asset_path.unlink()
            removed.append(asset_path.stem)
    return removed
