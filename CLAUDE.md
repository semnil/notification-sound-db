# notification-sound-db

- **Override of the global CLAUDE.md's 「ドキュメント」 language rule**: this file is written entirely in English; `README`, `CONTRIBUTING` and `docs/*` are maintained in English at `<name>.md` with the Japanese translation beside it at `<name>.ja.md`; the license files (`LICENSE`, `LICENSE-DATA.md`) are English only

## What this is

A Python CLI (`notification-sound-db`, entry point `notification_sound_db.cli:main` in `src/`) that measures notification-sound audio into pretty-printed JSON under `data/` and renders a committed bilingual static report under `site/`. No original audio is redistributed.

## Commands

Setup, the per-subcommand workflow, and the source-acquisition rules live in `README.md` (Quick start) and `docs/updating.md`; `.github/workflows/test.yml` is the authoritative command list. The one non-obvious point: the test step runs **both** runners, Python and Node.

```sh
ruff check .
pytest
node --test tests/test_language.mjs   # exercises web/static/language.js
```

## Architecture

- `data/assets/<sha256>.json` — one intrinsic measurement per unique source file; `data/sources/<source-id>.json` — where each hash occurs, plus versions, provenance, classification, and failures. Field and layout reference: `data/README.md`.
- `config/sources.json` — source registry; `config/analysis-profile.json` — measurement profile.
- `templates/` (Jinja2) + `web/static/` assets render into `site/`. The CLI subcommands map onto the `analyzer` / `exporter` / `site` / `validation` modules.

## Gotchas

- **Generated outputs are committed and CI-enforced.** `data/exports/measurements.csv` and the whole `site/` tree are checked in; `test.yml` re-runs `export` + `build-site` and fails on `git diff --exit-code -- data/exports site`. Regenerate both in the same change that touches `data/`, `config/`, `templates/`, `web/`, or the export/site code.
- **Never commit vendor packages or extracted source audio.** The acquisition and cleanup rules are in `docs/updating.md` §3, and `.gitignore` enforces it.
