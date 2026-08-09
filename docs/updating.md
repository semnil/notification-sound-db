# Updating the current snapshot

[日本語](updating.ja.md)

Updates are intentionally manual. There is no scheduled package download or measurement job.

## 1. Prepare

Install Python 3.11 or later and current FFmpeg/FFprobe, then install the project in an isolated
environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/notification-sound-db sources
```

Review the source registry and inventory before measuring:

```sh
.venv/bin/notification-sound-db inventory --source macos-system --source slack
```

## 2. Measure an installed source

```sh
.venv/bin/notification-sound-db update --source slack
```

Use `--path source-id=/absolute/path` when the bundle is elsewhere. The update writes a new current
source snapshot, reuses hash-matching assets measured with the same profile, and removes assets no
longer referenced by any source. Add `--force` only when an unchanged file must be reanalyzed.

## 3. Inspect an official package without installing

Use only an official vendor URL. Work in a newly created temporary directory, record the package
SHA-256, extract without running or installing the application, and pass the extracted `.app` path
to the CLI. Provide the resolved distribution URL and package hash:

```sh
.venv/bin/notification-sound-db update \
  --source application-id \
  --path 'application-id=/private/tmp/example/App.app' \
  --distribution-url 'application-id=https://vendor.example/App.pkg' \
  --distribution-sha256 'application-id=<64-lowercase-hex-digits>'
```

Delete the downloaded package, extracted application, and all source audio immediately after a
successful measurement. Never commit them. Do not install or execute the app, and do not bypass
store authentication, encryption, access controls, or DRM. If official distribution cannot be
obtained within those rules, create or update an explicit `unavailable` source snapshot instead of
copying from an unofficial mirror.

## 4. Review classification and scope

Filename rules are conservative. Review new source occurrences in `data/sources/`. Correct
occurrence-level `event_type` when official context establishes it; use `unknown` when it does not.
Exclude primary music, video audio, narration, and other non-event media. Do not modify intrinsic
asset measurements to express classification.

## 5. Validate and generate

```sh
.venv/bin/ruff check .
.venv/bin/pytest
.venv/bin/notification-sound-db validate
.venv/bin/notification-sound-db export
.venv/bin/notification-sound-db build-site
git diff --check
```

Review JSON, CSV, both languages of the report, measurement failures, version/provenance changes,
and the absence of source audio or vendor packages before committing.
