# notification-sound-db

[English](README.md)

**公開レポート:** https://notification-sound-db.semnil.com/

`notification-sound-db` は、macOS と主要コミュニケーションアプリに同梱されたイベント音について、
再現可能な音量・周波数特性の測定値を収めたテキスト中心のデータベースです。LUFS、dBTP、RMS、
Crest Factor、時間特性、周波数特性などの記述的なデータを公開し、元の音声ファイルは再配布しません。

主な利用場面は、視聴者端末で再生された通知音がライブ配信の人声と競合し得る状況の調査です。
測定と解釈は意図的に分離しており、配信音量の推奨値や安全判定、アプリのランキングは提供しません。

## 現在の対象

現行スナップショットは、macOS のシステム音、選定した Apple 標準アプリ、Slack、Discord、
Microsoft Teams、Zoom Workplace、LINE を収録しています。LINE はローカルにインストールされた
macOS アプリ内の音声ファイルを測定しています。現在の件数とバージョンは生成済みレポートで
確認できます。

- 正本データ: 整形済み JSON の [`data/`](data)
- 表形式エクスポート: [`data/exports/measurements.csv`](data/exports/measurements.csv)
- 測定プロファイル: [`config/analysis-profile.json`](config/analysis-profile.json)
- 要件: [`docs/requirements.ja.md`](docs/requirements.ja.md)
- 測定方法: [`docs/methodology.ja.md`](docs/methodology.ja.md)
- 更新手順: [`docs/updating.ja.md`](docs/updating.ja.md)

## クイックスタート

Python 3.11 以降と FFmpeg／FFprobe が必要です。

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/notification-sound-db validate
.venv/bin/notification-sound-db build-site
```

英語版は `site/index.html`、日本語版は `site/ja/index.html` です。測定せずローカルの対象を
確認するには次を実行します。

```sh
.venv/bin/notification-sound-db inventory
```

## データモデル

`data/assets/<sha256>.json` は、固有の元音源ファイルごとに内在的な測定値のレコードを 1 件保持します。
`data/sources/<source-id>.json` は、現行 OS／アプリ内でそのハッシュが現れる場所、アプリ／プラットフォームの
バージョン、取得来歴、分類、測定失敗を記録します。取得元を更新すると現行スナップショットが置き換わり、
旧版は Git 履歴でのみ参照できます。

元音源とベンダー配布物はリポジトリに含みません。製品名、商標、元音源の権利は各権利者に帰属します。

## ライセンス

コードは [MIT License](LICENSE)、測定データと文書は [CC BY 4.0](LICENSE-DATA.md) です。
元の音声ファイルはいずれのライセンスにも含まれません。
