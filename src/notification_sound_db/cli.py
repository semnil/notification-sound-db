"""Command-line interface for collecting, validating, and publishing data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from notification_sound_db.analyzer import analyze
from notification_sound_db.catalog import (
    discover_audio,
    load_sources,
    project_root,
    update_source,
)
from notification_sound_db.exporter import write_csv
from notification_sound_db.validation import validate_repository


def _assignments(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        if not separator or not key or not item:
            raise argparse.ArgumentTypeError(f"Expected SOURCE=VALUE, got: {value}")
        result[key] = item
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notification-sound-db",
        description="Measure and publish the current notification sound snapshot.",
    )
    parser.add_argument("--root", type=Path, help="Repository root (auto-detected by default)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("sources", help="List configured sources")

    inventory = subparsers.add_parser("inventory", help="List discoverable files without measuring")
    inventory.add_argument("--source", action="append", default=[], help="Source ID; repeatable")
    inventory.add_argument("--path", action="append", default=[], metavar="SOURCE=PATH")

    update = subparsers.add_parser("update", help="Measure and update the current snapshot")
    update.add_argument("--source", action="append", default=[], help="Source ID; repeatable")
    update.add_argument("--path", action="append", default=[], metavar="SOURCE=PATH")
    update.add_argument(
        "--distribution-url", action="append", default=[], metavar="SOURCE=URL"
    )
    update.add_argument(
        "--distribution-sha256", action="append", default=[], metavar="SOURCE=HASH"
    )
    update.add_argument("--force", action="store_true", help="Re-analyze unchanged assets")

    single = subparsers.add_parser("analyze", help="Analyze one file and print JSON")
    single.add_argument("path", type=Path)

    subparsers.add_parser("validate", help="Validate schemas and cross-record references")

    export = subparsers.add_parser("export", help="Generate the flat CSV export")
    export.add_argument("--output", type=Path)

    build = subparsers.add_parser("build-site", help="Generate the static bilingual report")
    build.add_argument("--output", type=Path)
    return parser


def _select_sources(definitions, selected: list[str]):
    by_id = {source.id: source for source in definitions}
    if not selected or selected == ["all"]:
        return definitions
    unknown = sorted(set(selected) - set(by_id))
    if unknown:
        raise ValueError(f"Unknown source ID(s): {', '.join(unknown)}")
    return [by_id[source_id] for source_id in selected]


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        root = (args.root.resolve() if args.root else project_root())
        definitions = load_sources(root)

        if args.command == "sources":
            for source in definitions:
                status = "available" if source.default_path.exists() else "missing"
                print(f"{source.id}\t{status}\t{source.default_path}")
            return 0

        if args.command == "analyze":
            print(json.dumps(analyze(args.path.resolve()), ensure_ascii=False, indent=2))
            return 0

        if args.command == "validate":
            errors = validate_repository(root)
            if errors:
                for error in errors:
                    print(f"error: {error}", file=sys.stderr)
                return 1
            print("Validation passed.")
            return 0

        if args.command == "export":
            destination = write_csv(root, args.output)
            print(destination)
            return 0

        if args.command == "build-site":
            from notification_sound_db.site import build_site

            destination = build_site(root, args.output)
            print(destination)
            return 0

        selected = _select_sources(definitions, args.source)
        overrides = _assignments(args.path)

        if args.command == "inventory":
            missing = False
            for source in selected:
                path = Path(overrides.get(source.id, source.default_path))
                if not path.exists():
                    print(f"{source.id}\tmissing\t{path}")
                    missing = True
                    continue
                files = discover_audio(path)
                print(f"{source.id}\t{len(files)}\t{path}")
                for file_path in files:
                    print(f"  {file_path.relative_to(path).as_posix()}")
            return 1 if missing and args.source else 0

        if args.command == "update":
            urls = _assignments(args.distribution_url)
            distribution_hashes = _assignments(args.distribution_sha256)
            failures = 0
            for source in selected:
                path = Path(overrides.get(source.id, source.default_path)).resolve()
                if not path.exists():
                    print(f"skip: {source.id}: not found at {path}", file=sys.stderr)
                    failures += 1 if args.source else 0
                    continue
                count, analyzed_count, failure_count = update_source(
                    root,
                    source,
                    path,
                    force=args.force,
                    distribution_url=urls.get(source.id),
                    distribution_sha256=distribution_hashes.get(source.id),
                )
                print(
                    f"{source.id}: {count} discovered, {analyzed_count} analyzed, "
                    f"{failure_count} failed"
                )
            return 1 if failures else 0
    except (FileNotFoundError, ValueError, RuntimeError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
