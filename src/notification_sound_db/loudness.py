"""ITU-R BS.1770 / EBU Mode measurements via FFmpeg ebur128."""

from __future__ import annotations

import math
import re
from pathlib import Path

from notification_sound_db.process import MediaToolError, run_process

MOMENTARY_WINDOW_SECONDS = 0.4
SHORT_TERM_WINDOW_SECONDS = 3.0
TAIL_PADDING_SECONDS = 3.1

_NUMBER = r"-?(?:inf|nan|\d+(?:\.\d+)?)"
_FRAME_RE = re.compile(
    rf"t:\s*([\d.]+)\s+TARGET.*?M:\s*({_NUMBER})\s+S:\s*({_NUMBER})"
)


def _finite(value: str | None) -> float | None:
    if value is None:
        return None
    parsed = float(value)
    return round(parsed, 3) if math.isfinite(parsed) else None


def measure_loudness(path: Path, source_duration: float) -> dict:
    """Measure loudness while adding a silent tail for short-event meter settling."""
    filter_graph = (
        f"apad=pad_dur={TAIL_PADDING_SECONDS},"
        "ebur128=peak=true:framelog=verbose"
    )
    try:
        result = run_process(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-loglevel",
                "verbose",
                "-i",
                str(path),
                "-map",
                "0:a:0",
                "-af",
                filter_graph,
                "-f",
                "null",
                "-",
            ]
        )
    except MediaToolError:
        raise
    output = result.stderr.decode("utf-8", errors="replace")
    frames = _FRAME_RE.findall(output)
    momentary = [_finite(row[1]) for row in frames]
    short_term = [_finite(row[2]) for row in frames]
    momentary_values = [value for value in momentary if value is not None]
    short_term_values = [value for value in short_term if value is not None]

    summary_index = output.rfind("Summary:")
    if summary_index < 0:
        raise MediaToolError("FFmpeg ebur128 summary was not found")
    summary = output[summary_index:]
    integrated_match = re.search(rf"I:\s*({_NUMBER})\s*LUFS", summary)
    lra_match = re.search(rf"LRA:\s*({_NUMBER})\s*LU", summary)
    true_peak_match = re.search(rf"Peak:\s*({_NUMBER})\s*dBFS", summary)

    notes: list[str] = ["silent_tail_added_for_meter_settling"]
    if source_duration < MOMENTARY_WINDOW_SECONDS:
        notes.append("source_shorter_than_momentary_window")
    if source_duration < SHORT_TERM_WINDOW_SECONDS:
        notes.append("source_shorter_than_short_term_window")

    return {
        "standard": "ITU-R BS.1770-5 / EBU Mode",
        "integrated_lufs": _finite(integrated_match.group(1) if integrated_match else None),
        "maximum_momentary_lufs": max(momentary_values) if momentary_values else None,
        "maximum_short_term_lufs": (
            max(short_term_values)
            if short_term_values and source_duration >= SHORT_TERM_WINDOW_SECONDS
            else None
        ),
        "loudness_range_lu": (
            _finite(lra_match.group(1))
            if lra_match and source_duration >= SHORT_TERM_WINDOW_SECONDS
            else None
        ),
        "true_peak_dbtp": _finite(true_peak_match.group(1) if true_peak_match else None),
        "momentary_window_seconds": MOMENTARY_WINDOW_SECONDS,
        "short_term_window_seconds": SHORT_TERM_WINDOW_SECONDS,
        "tail_padding_seconds": TAIL_PADDING_SECONDS,
        "notes": notes,
    }
