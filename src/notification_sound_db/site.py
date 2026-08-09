"""Generate the bilingual static report."""

from __future__ import annotations

import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from notification_sound_db.exporter import records, write_csv
from notification_sound_db.jsonio import read_json, write_json
from notification_sound_db.validation import validate_repository

LANGUAGES = ("en", "ja")

TEXT = {
    "en": {
        "title": "Notification Sound Measurements",
        "subtitle": (
            "Measured levels and spectral characteristics of current OS and app event sounds"
        ),
        "skip": "Skip to content",
        "language": "日本語",
        "search_label": "Search sounds",
        "search_placeholder": "Search by app, sound name, event, or path…",
        "all_sources": "All sources",
        "all_events": "All event types",
        "results": "measurements",
        "sounds": "sound occurrences",
        "unique_assets": "unique audio assets",
        "sources": "current sources",
        "measured_sources": "measured sources",
        "unavailable_sources": "not collected",
        "collection_notes": "Collection coverage",
        "collection_notes_intro": (
            "Configured sources that could not be measured without installing software are "
            "retained as explicit gaps."
        ),
        "updated": "Snapshot observed",
        "table_sound": "Sound",
        "table_source": "Source",
        "table_event": "Event",
        "table_duration": "Duration",
        "table_lufs_i": "Integrated",
        "table_lufs_m": "Max momentary",
        "table_true_peak": "True peak",
        "table_rms": "RMS",
        "details": "Details",
        "methodology": "Methodology",
        "download_csv": "Download CSV",
        "download_json": "Browse JSON",
        "disclaimer": (
            "These are measurements of bundled source files, not acoustic playback levels. "
            "Actual level relationships depend on OS, app, player, and output-device settings."
        ),
        "no_results": "No measurements match the current filters.",
        "js_hint": "Search and filters require JavaScript. All rows remain readable below.",
        "back": "Back to all measurements",
        "identity": "Identity and provenance",
        "metrics": "Level measurements",
        "spectrum": "Frequency characteristics",
        "occurrences": "Current source occurrences",
        "technical": "Technical metadata",
        "definitions": "Definitions and limitations",
        "not_available": "N/A",
        "value": "Value",
        "metric": "Metric",
        "relative_path": "Relative path",
        "hash": "SHA-256",
        "analyzed": "Analyzed",
        "official_source": "Official source",
        "acquisition": "Acquisition",
        "distribution": "Distribution package",
        "distribution_hash": "Package SHA-256",
        "source_observed": "Source observed",
        "view_data": "View canonical JSON",
        "footer": "Measurement data: CC BY 4.0 · Code: MIT · Original sounds are not included.",
    },
    "ja": {
        "title": "通知音測定データベース",
        "subtitle": "現行OS・アプリのイベント音について、音量と周波数特性を同一条件で測定",
        "skip": "本文へスキップ",
        "language": "English",
        "search_label": "通知音を検索",
        "search_placeholder": "アプリ、音源名、イベント、パスで検索…",
        "all_sources": "すべての取得元",
        "all_events": "すべてのイベント種別",
        "results": "件の測定",
        "sounds": "件の音源参照",
        "unique_assets": "件の固有音源",
        "sources": "件の現行取得元",
        "measured_sources": "件の測定済み取得元",
        "unavailable_sources": "件の未収集",
        "collection_notes": "収集状況",
        "collection_notes_intro": (
            "インストールせずに測定できなかった対象は、欠落を隠さず未収集として"
            "記録しています。"
        ),
        "updated": "スナップショット確認日時",
        "table_sound": "音源",
        "table_source": "取得元",
        "table_event": "イベント",
        "table_duration": "長さ",
        "table_lufs_i": "Integrated",
        "table_lufs_m": "最大Momentary",
        "table_true_peak": "True Peak",
        "table_rms": "RMS",
        "details": "詳細",
        "methodology": "測定方法",
        "download_csv": "CSVをダウンロード",
        "download_json": "JSONを見る",
        "disclaimer": (
            "掲載値は同梱音源ファイルの測定値であり、実際の再生音圧ではありません。"
            "相対的な再生レベルはOS、アプリ、プレイヤー、出力機器の設定で変化します。"
        ),
        "no_results": "現在の条件に一致する測定値はありません。",
        "js_hint": "検索と絞り込みにはJavaScriptが必要です。全データは下の表から読めます。",
        "back": "測定一覧へ戻る",
        "identity": "識別情報と来歴",
        "metrics": "音量測定値",
        "spectrum": "周波数特性",
        "occurrences": "現行取得元での参照",
        "technical": "技術メタデータ",
        "definitions": "定義と制約",
        "not_available": "測定不能",
        "value": "値",
        "metric": "指標",
        "relative_path": "相対パス",
        "hash": "SHA-256",
        "analyzed": "測定日時",
        "official_source": "公式配布元",
        "acquisition": "取得方法",
        "distribution": "配布パッケージ",
        "distribution_hash": "配布物 SHA-256",
        "source_observed": "取得元確認日時",
        "view_data": "正本JSONを見る",
        "footer": "測定データ: CC BY 4.0 · コード: MIT · 元の通知音は収録していません。",
    },
}

EVENT_NAMES = {
    "message": {"en": "Message", "ja": "メッセージ"},
    "incoming_call": {"en": "Incoming call", "ja": "着信"},
    "call_state": {"en": "Call state", "ja": "通話状態"},
    "error": {"en": "Error", "ja": "エラー"},
    "completion": {"en": "Completion", "ja": "完了"},
    "ui_feedback": {"en": "UI feedback", "ja": "UIフィードバック"},
    "system_alert": {"en": "System alert", "ja": "システム警告"},
    "unknown": {"en": "Unclassified", "ja": "未分類"},
}


def _format_number(value, unit: str, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f} {unit}".strip()


def _site_url(path: str) -> str | None:
    base = os.environ.get("SITE_URL", "").rstrip("/")
    return f"{base}/{path.lstrip('/')}" if base else None


def _alternate_urls(english_path: str, japanese_path: str) -> dict[str, str | None]:
    return {"en": _site_url(english_path), "ja": _site_url(japanese_path)}


def _environment(repository: Path) -> Environment:
    environment = Environment(
        loader=FileSystemLoader(repository / "templates"),
        autoescape=select_autoescape(("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["metric"] = _format_number
    return environment


def _language_paths(language: str) -> dict[str, str]:
    if language == "ja":
        return {
            "home": "../index.html",
            "methodology": "../methodology.html",
            "language": "../index.html",
            "asset_prefix": "sounds/",
            "root_prefix": "../",
        }
    return {
        "home": "index.html",
        "methodology": "methodology.html",
        "language": "ja/index.html",
        "asset_prefix": "sounds/",
        "root_prefix": "",
    }


def _detail_paths(language: str) -> dict[str, str]:
    if language == "ja":
        return {
            "home": "../index.html",
            "methodology": "../methodology.html",
            "language": "../../sounds/{sha}.html",
            "root_prefix": "../../",
        }
    return {
        "home": "../index.html",
        "methodology": "../methodology.html",
        "language": "../ja/sounds/{sha}.html",
        "root_prefix": "../",
    }


def _render(path: Path, template, **context) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template.render(**context), encoding="utf-8")


def build_site(repository: Path, output: Path | None = None) -> Path:
    errors = validate_repository(repository)
    if errors:
        raise ValueError("Cannot build invalid data:\n" + "\n".join(errors))

    destination = (output or repository / "site").resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for generated in ("assets", "data", "ja", "sounds"):
        target = destination / generated
        if target.exists():
            shutil.rmtree(target)
    for generated in ("index.html", "methodology.html"):
        (destination / generated).unlink(missing_ok=True)

    write_csv(repository)
    shutil.copytree(repository / "data", destination / "data")
    shutil.copytree(repository / "web/static", destination / "assets")
    (destination / ".nojekyll").write_text("", encoding="utf-8")

    sources = {
        path.stem: read_json(path) for path in sorted((repository / "data/sources").glob("*.json"))
    }
    assets = {
        path.stem: read_json(path) for path in sorted((repository / "data/assets").glob("*.json"))
    }
    rows = records(repository)
    rows.sort(key=lambda row: (row["source_name_en"].casefold(), row["sound_name"].casefold()))
    observed = max((source["observed_at"] for source in sources.values()), default="—")
    event_counts = Counter(row["event_type"] for row in rows)
    source_counts = Counter(row["source_id"] for row in rows)
    measured_sources = {
        source_id: source
        for source_id, source in sources.items()
        if source["collection"]["status"] == "measured"
    }
    unavailable_sources = {
        source_id: source
        for source_id, source in sources.items()
        if source["collection"]["status"] == "unavailable"
    }

    occurrences: dict[str, list[dict]] = defaultdict(list)
    for source in sources.values():
        for sound in source["sounds"]:
            occurrences[sound["asset_sha256"]].append(
                {
                    **sound,
                    "source_id": source["source_id"],
                    "source_names": source["names"],
                    "source_version": source["application"]["version"],
                    "official_url": source["acquisition"]["official_url"],
                    "acquisition": source["acquisition"],
                    "observed_at": source["observed_at"],
                }
            )

    catalog = {
        "schema_version": "1.0.0",
        "observed_at": observed,
        "sources": [
            {
                "source_id": source["source_id"],
                "names": source["names"],
                "vendor": source["vendor"],
                "application": source["application"],
                "platform": source["platform"],
                "observed_at": source["observed_at"],
                "collection": source["collection"],
                "acquisition": source["acquisition"],
                "sound_count": len(source["sounds"]),
                "measurement_failures": source["measurement_failures"],
            }
            for source in sources.values()
        ],
        "rows": rows,
    }
    write_json(destination / "data/catalog.json", catalog)

    environment = _environment(repository)
    index_template = environment.get_template("index.html")
    detail_template = environment.get_template("detail.html")
    methodology_template = environment.get_template("methodology.html")

    for language in LANGUAGES:
        language_dir = destination / ("ja" if language == "ja" else "")
        paths = _language_paths(language)
        _render(
            language_dir / "index.html",
            index_template,
            lang=language,
            text=TEXT[language],
            event_names=EVENT_NAMES,
            rows=rows,
            sources=sources,
            measured_sources=measured_sources,
            unavailable_sources=unavailable_sources,
            source_counts=source_counts,
            event_counts=event_counts,
            observed_at=observed,
            paths=paths,
            canonical=_site_url("ja/" if language == "ja" else ""),
            alternates=_alternate_urls("", "ja/"),
        )
        _render(
            language_dir / "methodology.html",
            methodology_template,
            lang=language,
            text=TEXT[language],
            paths=paths,
            canonical=_site_url("ja/methodology.html" if language == "ja" else "methodology.html"),
            alternates=_alternate_urls("methodology.html", "ja/methodology.html"),
        )
        for digest, asset in assets.items():
            detail_paths = _detail_paths(language)
            detail_paths["language"] = detail_paths["language"].format(sha=digest)
            canonical_path = (
                f"ja/sounds/{digest}.html" if language == "ja" else f"sounds/{digest}.html"
            )
            _render(
                language_dir / "sounds" / f"{digest}.html",
                detail_template,
                lang=language,
                text=TEXT[language],
                event_names=EVENT_NAMES,
                asset=asset,
                occurrences=occurrences[digest],
                paths=detail_paths,
                canonical=_site_url(canonical_path),
                alternates=_alternate_urls(
                    f"sounds/{digest}.html", f"ja/sounds/{digest}.html"
                ),
            )
    return destination
