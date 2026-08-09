"""Schema and cross-record validation."""

from __future__ import annotations

from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from notification_sound_db.jsonio import read_json


def _schema_validator(path: Path) -> Draft202012Validator:
    return Draft202012Validator(read_json(path), format_checker=FormatChecker())


def validate_repository(repository: Path) -> list[str]:
    errors: list[str] = []
    schema_dir = repository / "data/schemas"
    asset_validator = _schema_validator(schema_dir / "asset.schema.json")
    source_validator = _schema_validator(schema_dir / "source.schema.json")
    config_validator = _schema_validator(schema_dir / "source-config.schema.json")

    config_path = repository / "config/sources.json"
    config = read_json(config_path)
    for error in sorted(config_validator.iter_errors(config), key=str):
        errors.append(f"{config_path.relative_to(repository)}: {error.message}")
    configured_ids = [source.get("id") for source in config.get("sources", [])]
    if len(configured_ids) != len(set(configured_ids)):
        errors.append("config/sources.json: source IDs must be unique")
    profile_path = repository / "config/analysis-profile.json"
    profile = read_json(profile_path)
    profile_id = profile.get("profile_id")

    asset_hashes: set[str] = set()
    for path in sorted((repository / "data/assets").glob("*.json")):
        record = read_json(path)
        for error in sorted(asset_validator.iter_errors(record), key=str):
            errors.append(f"{path.relative_to(repository)}: {error.message}")
        digest = record.get("sha256")
        if digest != path.stem:
            errors.append(f"{path.relative_to(repository)}: sha256 does not match filename")
        if isinstance(digest, str):
            asset_hashes.add(digest)
        if record.get("analysis_profile") != profile_id:
            errors.append(
                f"{path.relative_to(repository)}: analysis_profile does not match "
                "config/analysis-profile.json"
            )

    referenced: set[str] = set()
    source_ids: set[str] = set()
    for path in sorted((repository / "data/sources").glob("*.json")):
        record = read_json(path)
        for error in sorted(source_validator.iter_errors(record), key=str):
            errors.append(f"{path.relative_to(repository)}: {error.message}")
        source_id = record.get("source_id")
        if source_id != path.stem:
            errors.append(f"{path.relative_to(repository)}: source_id does not match filename")
        if source_id in source_ids:
            errors.append(f"{path.relative_to(repository)}: duplicate source_id {source_id}")
        if isinstance(source_id, str):
            source_ids.add(source_id)
        if record.get("analysis_profile") != profile_id:
            errors.append(
                f"{path.relative_to(repository)}: analysis_profile does not match "
                "config/analysis-profile.json"
            )
        seen_occurrences: set[tuple[str, str]] = set()
        for sound in record.get("sounds", []):
            digest = sound.get("asset_sha256")
            relative_path = sound.get("relative_path")
            key = (str(digest), str(relative_path))
            if key in seen_occurrences:
                errors.append(f"{path.relative_to(repository)}: duplicate sound {key}")
            seen_occurrences.add(key)
            if isinstance(digest, str):
                referenced.add(digest)
                if digest not in asset_hashes:
                    errors.append(
                        f"{path.relative_to(repository)}: missing asset data/assets/{digest}.json"
                    )

    for orphan in sorted(asset_hashes - referenced):
        errors.append(f"data/assets/{orphan}.json: asset is not referenced by a current source")
    configured_id_set = {value for value in configured_ids if isinstance(value, str)}
    for missing in sorted(configured_id_set - source_ids):
        errors.append(f"data/sources/{missing}.json: configured source has no snapshot record")
    for unknown in sorted(source_ids - configured_id_set):
        errors.append(f"data/sources/{unknown}.json: source is not configured")
    return errors
