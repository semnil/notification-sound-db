# データ構成

[English](README.md)

- `assets/<sha256>.json`: 完全に同一の元ファイル1つに対する内在的な測定値の正本。
- `sources/<source-id>.json`: OS／アプリ取得元ごとの現行パス、分類、版、来歴、収集状態、失敗。
- `schemas/*.schema.json`: 正本レコードと取得元設定の JSON Schema。
- `exports/measurements.csv`: 取得元内の参照1件を1行にした生成済み一覧。

単位はフィールド名の `_lufs`、`_lu`、`_dbtp`、`_dbfs`、`_db`、`_hz`、`_seconds`、`_percent`
で表します。JSON `null` は未取得・未定義でありゼロではありません。全ファイルは UTF-8 の整形済み
テキストで末尾改行を持ちます。元音源は含みません。

データとこの文書は CC BY 4.0 です。詳細は [`../LICENSE-DATA.md`](../LICENSE-DATA.md) を参照してください。
