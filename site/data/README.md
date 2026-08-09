# Data layout

[日本語](README.ja.md)

- `assets/<sha256>.json`: canonical intrinsic measurements for one exact source file.
- `sources/<source-id>.json`: current paths, classifications, version, provenance, collection
  status, and failures for one OS or app source.
- `schemas/*.schema.json`: JSON Schema definitions for canonical records and source configuration.
- `exports/measurements.csv`: generated flat view, with one row per source occurrence.

Unit suffixes are part of field names: `_lufs`, `_lu`, `_dbtp`, `_dbfs`, `_db`, `_hz`,
`_seconds`, and `_percent`. JSON `null` means unavailable or undefined, never zero. All files are
UTF-8, pretty-printed, and end with a newline. Original audio is not included.

Data and this documentation are licensed under CC BY 4.0; see
[`../LICENSE-DATA.md`](../LICENSE-DATA.md).
