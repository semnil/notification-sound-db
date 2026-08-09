# 現行スナップショットの更新

[English](updating.md)

更新は意図的に手動です。配布物の定期取得や定期測定は行いません。

## 1. 準備

Python 3.11 以降と現行 FFmpeg／FFprobe を用意します。

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/notification-sound-db sources
.venv/bin/notification-sound-db inventory --source macos-system --source slack
```

## 2. 導入済み取得元の測定

```sh
.venv/bin/notification-sound-db update --source slack
```

別の場所にある場合は `--path source-id=/absolute/path` を使います。更新は現行取得元レコードを
置き換え、同一プロファイルで測定済みの同一ハッシュを再利用し、どの現行取得元からも参照されない
測定値を削除します。未変更ファイルを再測定する必要がある場合だけ `--force` を使います。

## 3. インストールせず公式配布物を調査

必ず公式ベンダー URL と新規一時ディレクトリを使います。配布物の SHA-256 を記録し、アプリを実行・
インストールせず展開し、展開した `.app` を指定します。

```sh
.venv/bin/notification-sound-db update \
  --source application-id \
  --path 'application-id=/private/tmp/example/App.app' \
  --distribution-url 'application-id=https://vendor.example/App.pkg' \
  --distribution-sha256 'application-id=<64-lowercase-hex-digits>'
```

測定成功後は、配布物、展開済みアプリ、元音源を直ちに削除し、コミットしません。ストア認証、暗号化、
アクセス制御、DRM を回避しません。この条件で公式配布物を取得できない場合は非公式ミラーを使わず、
`unavailable` の取得元スナップショットとして欠落を明示します。

## 4. 分類と対象範囲の確認

ファイル名による分類は保守的です。`data/sources/` の追加項目を確認し、公式な文脈から用途が分かる
場合だけ `event_type` を修正し、不明なら `unknown` とします。主要な音楽、動画音声、ナレーション等は
除外します。分類のためにハッシュ単位の測定値を変更しません。

## 5. 検証と生成

```sh
.venv/bin/ruff check .
.venv/bin/pytest
.venv/bin/notification-sound-db validate
.venv/bin/notification-sound-db export
.venv/bin/notification-sound-db build-site
git diff --check
```

JSON、CSV、英日サイト、測定失敗、版・来歴の変更、元音源や配布物が存在しないことを確認してから
コミットします。
