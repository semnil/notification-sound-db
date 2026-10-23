# 現行スナップショットの更新

[English](updating.md)

更新は意図的に手動です。配布物の定期取得や定期測定のジョブはありません。

## 1. 準備

Python 3.11 以降、Node.js（`node --test` による言語テスト用）、現行 FFmpeg／FFprobe を用意し、独立した環境にプロジェクトをインストールします。

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/notification-sound-db sources
```

測定前に取得元レジストリとインベントリを確認します。

```sh
.venv/bin/notification-sound-db inventory --source macos-system --source slack
```

## 2. 導入済み取得元の測定

```sh
.venv/bin/notification-sound-db update --source slack
```

バンドルが別の場所にある場合は `--path source-id=/absolute/path` を使います。更新は新しい現行取得元
スナップショットを書き込み、同一プロファイルで測定済みのハッシュが一致する測定値を再利用し、どの
取得元からも参照されなくなった測定値を削除します。未変更ファイルを再解析する必要がある場合だけ
`--force` を追加します。

## 3. インストールせず公式配布物を調査

公式ベンダー URL だけを使用します。新規作成した一時ディレクトリで作業し、配布物の SHA-256 を記録し、
アプリを実行・インストールせずに展開して、展開した `.app` のパスを CLI に渡します。解決済みの配布
URL と配布物のハッシュを指定します。

```sh
.venv/bin/notification-sound-db update \
  --source application-id \
  --path 'application-id=/private/tmp/example/App.app' \
  --distribution-url 'application-id=https://vendor.example/App.pkg' \
  --distribution-sha256 'application-id=<64-lowercase-hex-digits>'
```

測定成功後は、ダウンロードした配布物、展開済みアプリ、すべての元音源を直ちに削除します。これらは決して
コミットしません。アプリをインストール・実行せず、ストア認証、暗号化、アクセス制御、DRM を回避
しません。この条件で公式配布物を取得できない場合は、非公式ミラーからコピーせず、明示的な
`unavailable` の取得元スナップショットを作成または更新します。

## 4. 分類と対象範囲の確認

ファイル名による規則は保守的です。`data/sources/` で新しい取得元の出現を確認します。公式な文脈で用途
が確定する場合は出現単位の `event_type` を修正し、確定しない場合は `unknown` とします。主要な音楽、
動画音声、ナレーション、その他イベント音でないメディアは除外します。分類を表すためにハッシュ単位の
内在的な測定値を変更しません。

## 5. 検証と生成

```sh
.venv/bin/ruff check .
.venv/bin/pytest
node --test tests/test_language.mjs
.venv/bin/notification-sound-db validate
.venv/bin/notification-sound-db export
.venv/bin/notification-sound-db build-site
git diff --check
```

JSON、CSV、英日両方のレポート、測定失敗、版・来歴の変更、元音源や配布物が存在しないことを確認してから
コミットします。
