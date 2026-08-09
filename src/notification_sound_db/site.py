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
DEFAULT_SITE_URL = "https://notification-sound-db.semnil.com"

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
        "sort_by": "Sort by",
        "sort_hint": "Select to toggle ascending or descending order.",
        "table_scroll_region": "Scrollable measurement table",
        "table_scroll_hint": "More columns",
        "table_scroll_left": "Scroll table left",
        "table_scroll_right": "Scroll table right",
        "details": "Details",
        "methodology": "Methodology",
        "download_csv": "Download CSV",
        "download_json": "Browse JSON",
        "disclaimer": (
            "These are measurements of bundled source files, not acoustic playback levels. "
            "Actual level relationships depend on OS, app, player, and output-device settings."
        ),
        "no_results": "No measurements match the current filters.",
        "js_hint": (
            "Search, filters, and sorting require JavaScript. All rows remain readable below."
        ),
        "back": "Back to all measurements",
        "identity": "Identity and provenance",
        "metrics": "Level measurements",
        "level_over_time": "Level over time",
        "level_chart_title": "Short-window RMS level over time",
        "level_chart_description": (
            "Each point is the channel-combined RMS of a non-overlapping frame. "
            "Values below −80 dBFS are pinned to the chart floor for display; the canonical "
            "JSON retains measured values, and digital silence remains null."
        ),
        "level_chart_empty": "No finite RMS values are available for this source.",
        "chart_points": "points",
        "active_threshold": "Active threshold",
        "time_axis": "Time (seconds)",
        "spectrum": "Frequency characteristics",
        "spectrum_chart_title": "Third-octave band energy",
        "spectrum_chart_description": (
            "Frequency is shown on the horizontal axis and band energy on the vertical axis. "
            "Values below −120 dBFS are pinned to the chart floor for display."
        ),
        "frequency_axis": "Frequency (Hz)",
        "energy_axis": "Band energy (dBFS)",
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
        "report_issue": "Report an issue",
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
        "sort_by": "並べ替え:",
        "sort_hint": "選択するたびに昇順と降順を切り替えます。",
        "table_scroll_region": "スクロール可能な測定表",
        "table_scroll_hint": "左右の列を表示",
        "table_scroll_left": "表を左へスクロール",
        "table_scroll_right": "表を右へスクロール",
        "details": "詳細",
        "methodology": "測定方法",
        "download_csv": "CSVをダウンロード",
        "download_json": "JSONを見る",
        "disclaimer": (
            "掲載値は同梱音源ファイルの測定値であり、実際の再生音圧ではありません。"
            "相対的な再生レベルはOS、アプリ、プレイヤー、出力機器の設定で変化します。"
        ),
        "no_results": "現在の条件に一致する測定値はありません。",
        "js_hint": (
            "検索、絞り込み、並べ替えにはJavaScriptが必要です。"
            "全データは下の表から読めます。"
        ),
        "back": "測定一覧へ戻る",
        "identity": "識別情報と来歴",
        "metrics": "音量測定値",
        "level_over_time": "音量レベルの推移",
        "level_chart_title": "短時間 RMS レベルの時間推移",
        "level_chart_description": (
            "各点は重複しないフレームについて全チャンネルを合成した RMS です。"
            "−80 dBFS 未満は表示上のみグラフ下端に固定し、正本JSONには測定値を保持します。"
            "デジタル無音は null のままです。"
        ),
        "level_chart_empty": "有限の RMS 値がないため、推移線を表示できません。",
        "chart_points": "点",
        "active_threshold": "有音判定閾値",
        "time_axis": "時間（秒）",
        "spectrum": "周波数特性",
        "spectrum_chart_title": "1/3オクターブ帯域エネルギー",
        "spectrum_chart_description": (
            "横軸は周波数、縦軸は帯域エネルギーです。"
            "−120 dBFS 未満は表示上のみグラフ下端に固定しています。"
        ),
        "frequency_axis": "周波数（Hz）",
        "energy_axis": "帯域エネルギー（dBFS）",
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
        "report_issue": "問題を報告",
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


def _site_url(path: str) -> str:
    base = os.environ.get("SITE_URL", DEFAULT_SITE_URL).rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _alternate_urls(english_path: str, japanese_path: str) -> dict[str, str]:
    return {"en": _site_url(english_path), "ja": _site_url(japanese_path)}


def _level_chart(asset: dict) -> dict:
    """Map a canonical RMS envelope to responsive SVG coordinates."""
    width = 900.0
    height = 280.0
    left = 62.0
    right = 18.0
    top = 18.0
    bottom = 42.0
    plot_width = width - left - right
    plot_height = height - top - bottom
    chart_floor = -80.0
    duration = asset["audio"]["duration_seconds"]
    envelope = asset["levels"]["rms_envelope"]

    def x_position(seconds: float) -> float:
        return left + min(max(seconds / duration, 0.0), 1.0) * plot_width

    def y_position(dbfs: float) -> float:
        displayed = min(0.0, max(chart_floor, dbfs))
        return top + (0.0 - displayed) / (0.0 - chart_floor) * plot_height

    segments: list[str] = []
    dots: list[dict[str, float]] = []
    current: list[tuple[float, float]] = []

    def finish_segment() -> None:
        if len(current) == 1:
            dots.append({"x": current[0][0], "y": current[0][1]})
        elif current:
            segments.append(
                " ".join(
                    f"{'M' if index == 0 else 'L'} {x:.2f} {y:.2f}"
                    for index, (x, y) in enumerate(current)
                )
            )
        current.clear()

    for point in envelope["points"]:
        value = point["rms_dbfs"]
        if value is None:
            finish_segment()
            continue
        current.append((x_position(point["time_seconds"]), y_position(value)))
    finish_segment()

    threshold = asset["levels"]["active_segment"]["threshold_dbfs"]
    threshold_y = y_position(threshold) if threshold is not None else None
    if duration < 1:
        tick_digits = 3
    elif duration < 10:
        tick_digits = 2
    else:
        tick_digits = 1
    return {
        "view_box": f"0 0 {width:.0f} {height:.0f}",
        "left": left,
        "right": width - right,
        "top": top,
        "bottom": height - bottom,
        "segments": segments,
        "dots": dots,
        "has_values": bool(segments or dots),
        "threshold_y": threshold_y,
        "threshold_dbfs": threshold,
        "frame_milliseconds": envelope["frame_duration_seconds"] * 1000.0,
        "point_count": len(envelope["points"]),
        "y_ticks": [
            {"label": f"{value}", "y": y_position(float(value))}
            for value in (0, -20, -40, -60, -80)
        ],
        "x_ticks": [
            {
                "label": f"{duration * fraction:.{tick_digits}f}",
                "x": x_position(duration * fraction),
            }
            for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)
        ],
    }


def _spectrum_chart(asset: dict) -> dict:
    """Map third-octave measurements to a conventional spectrum display."""
    width = 900.0
    height = 330.0
    left = 62.0
    right = 18.0
    top = 18.0
    bottom = 58.0
    plot_width = width - left - right
    plot_height = height - top - bottom
    chart_floor = -120.0
    source_bands = asset["spectrum"]["third_octave_band_energy_dbfs"]
    band_step = plot_width / max(len(source_bands), 1)
    bar_width = band_step * 0.68

    def y_position(dbfs: float) -> float:
        displayed = min(0.0, max(chart_floor, dbfs))
        return top + (0.0 - displayed) / (0.0 - chart_floor) * plot_height

    def frequency_label(frequency: float) -> str:
        if frequency >= 1000:
            return f"{frequency / 1000:g}k"
        return f"{frequency:g}"

    bands = []
    for index, source_band in enumerate(source_bands):
        center_x = left + (index + 0.5) * band_step
        value = source_band["energy_dbfs"]
        value_y = y_position(value) if value is not None else y_position(chart_floor)
        bands.append(
            {
                "center_hz": source_band["center_hz"],
                "energy_dbfs": value,
                "x": round(center_x - bar_width / 2.0, 2),
                "y": round(value_y, 2),
                "width": round(bar_width, 2),
                "height": round(y_position(chart_floor) - value_y, 2),
            }
        )

    return {
        "view_box": f"0 0 {width:.0f} {height:.0f}",
        "left": left,
        "right": width - right,
        "top": top,
        "bottom": height - bottom,
        "bands": bands,
        "has_values": any(band["energy_dbfs"] is not None for band in bands),
        "y_ticks": [
            {"label": f"{value}", "y": round(y_position(float(value)), 2)}
            for value in (0, -20, -40, -60, -80, -100, -120)
        ],
        "x_ticks": [
            {
                "label": frequency_label(source_band["center_hz"]),
                "x": round(left + (index + 0.5) * band_step, 2),
            }
            for index, source_band in enumerate(source_bands)
            if index % 3 == 1
        ],
    }


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
    for generated in ("favicon.svg", "index.html", "methodology.html", "robots.txt", "sitemap.xml"):
        (destination / generated).unlink(missing_ok=True)

    write_csv(repository)
    shutil.copytree(repository / "data", destination / "data")
    shutil.copytree(repository / "web/static", destination / "assets")
    shutil.copy2(repository / "web/static/favicon.svg", destination / "favicon.svg")
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
    sitemap_template = environment.get_template("sitemap.xml")

    sitemap_pairs = [
        {"en": _site_url(""), "ja": _site_url("ja/")},
        {
            "en": _site_url("methodology.html"),
            "ja": _site_url("ja/methodology.html"),
        },
        *[
            {
                "en": _site_url(f"sounds/{digest}.html"),
                "ja": _site_url(f"ja/sounds/{digest}.html"),
            }
            for digest in assets
        ],
    ]
    _render(destination / "sitemap.xml", sitemap_template, pairs=sitemap_pairs)
    (destination / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {_site_url('sitemap.xml')}\n",
        encoding="utf-8",
    )

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
            paths={
                **paths,
                "language": (
                    "../methodology.html" if language == "ja" else "ja/methodology.html"
                ),
            },
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
                level_chart=_level_chart(asset),
                spectrum_chart=_spectrum_chart(asset),
                occurrences=occurrences[digest],
                paths=detail_paths,
                canonical=_site_url(canonical_path),
                alternates=_alternate_urls(
                    f"sounds/{digest}.html", f"ja/sounds/{digest}.html"
                ),
            )
    return destination
