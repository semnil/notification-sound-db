"""Safe wrappers around FFmpeg command-line tools."""

from __future__ import annotations

import json
import subprocess
from functools import cache
from pathlib import Path


class MediaToolError(RuntimeError):
    """Raised when ffmpeg or ffprobe cannot process an input."""


def run_process(command: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(command, check=True, capture_output=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise MediaToolError(f"Required executable was not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaToolError(f"Command timed out after {timeout}s: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace")[-2000:]
        raise MediaToolError(f"{command[0]} failed: {detail}") from exc


def probe(path: Path) -> dict:
    result = run_process(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(result.stdout)


@cache
def tool_version(executable: str) -> str:
    result = run_process([executable, "-version"], timeout=15)
    first_line = result.stdout.decode("utf-8", errors="replace").splitlines()[0]
    return first_line.strip()
