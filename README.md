# notification-sound-db

[日本語](README.ja.md)

**Live report:** https://notification-sound-db.semnil.com/

`notification-sound-db` is a text-first database of reproducible level and spectral
measurements for event sounds bundled with macOS and major communication apps. It publishes
descriptive data—including LUFS, dBTP, RMS, crest factor, timing, and frequency features—without
redistributing the original audio.

The primary use case is investigating situations where a notification played on a viewer's
device may compete with human speech in a live stream. Measurements are deliberately separated
from interpretation: this project does not prescribe a stream level, label a level safe, or rank
applications.

## Current scope

The current snapshot covers macOS system collections, selected Apple apps, Slack, Discord,
Microsoft Teams, and Zoom Workplace. LINE is tracked as an explicit collection gap because its
official macOS distribution is Mac App Store only and the initial collection policy does not
permit installation. See the generated report for current counts and versions.

- Canonical data: pretty-printed JSON in [`data/`](data)
- Flat export: [`data/exports/measurements.csv`](data/exports/measurements.csv)
- Measurement profile: [`config/analysis-profile.json`](config/analysis-profile.json)
- Requirements: [`docs/requirements.md`](docs/requirements.md)
- Methodology: [`docs/methodology.md`](docs/methodology.md)
- Update procedure: [`docs/updating.md`](docs/updating.md)

## Quick start

Python 3.11 or later and FFmpeg/FFprobe are required.

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/notification-sound-db validate
.venv/bin/notification-sound-db build-site
```

Open `site/index.html` for English or `site/ja/index.html` for Japanese. To inspect local sources
without measuring them:

```sh
.venv/bin/notification-sound-db inventory
```

## Data model

`data/assets/<sha256>.json` contains one intrinsic measurement record per unique source file.
`data/sources/<source-id>.json` records where that hash occurs in the current OS or app,
application/platform versions, acquisition provenance, classification, and failures. Updating a
source replaces its current snapshot; older versions remain available only in Git history.

The original sounds and vendor packages are excluded from this repository. Product names,
trademarks, and original sounds remain the property of their respective owners.

## License

Code is available under the [MIT License](LICENSE). Measurement data and documentation are
available under [CC BY 4.0](LICENSE-DATA.md). The original audio files are not part of either
license.
