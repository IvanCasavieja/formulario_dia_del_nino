"""Server-side re-validation of the uploaded video, using the real downloaded file.

This is the actual enforcement of the duration/size/format limits. The client-side check
(reading video.duration before upload) is UX only - a presigned PUT cannot enforce a max
size at the signature level, and nothing stops a client from lying about content-type or
duration. Nothing here is trusted from the client except as an audit trail.
"""
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app import shared_constants as sc

_ALLOWED_FORMAT_NAMES = {
    "mov,mp4,m4a,3gp,3g2,mj2",  # mp4 / mov family
    "matroska,webm",  # webm
}


class VideoValidationError(Exception):
    """ffprobe itself failed to run, timed out, or returned unparsable output."""


@dataclass
class ValidationResult:
    valid: bool
    reason: str | None
    duration_seconds: float | None
    size_bytes: int | None
    format_name: str | None


def _probe(path: Path) -> dict:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_type:format=duration,size,format_name",
                "-of", "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise VideoValidationError(f"ffprobe failed to execute: {e}") from e

    if completed.returncode != 0:
        raise VideoValidationError(f"ffprobe exited {completed.returncode}: {completed.stderr}")

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as e:
        raise VideoValidationError(f"ffprobe returned unparsable output: {e}") from e


def validate_video(path: Path) -> ValidationResult:
    try:
        data = _probe(path)
    except VideoValidationError:
        return ValidationResult(
            valid=False,
            reason="invalid_or_corrupt_video",
            duration_seconds=None,
            size_bytes=None,
            format_name=None,
        )

    streams = data.get("streams") or []
    format_info = data.get("format") or {}

    has_video_stream = any(s.get("codec_type") == "video" for s in streams)
    if not has_video_stream:
        return ValidationResult(
            valid=False,
            reason="invalid_or_corrupt_video",
            duration_seconds=None,
            size_bytes=None,
            format_name=None,
        )

    try:
        duration_seconds = float(format_info["duration"])
        size_bytes = int(format_info["size"])
        format_name = format_info["format_name"]
    except (KeyError, TypeError, ValueError):
        return ValidationResult(
            valid=False,
            reason="invalid_or_corrupt_video",
            duration_seconds=None,
            size_bytes=None,
            format_name=None,
        )

    if duration_seconds > sc.MAX_VIDEO_DURATION_SECONDS + sc.MAX_VIDEO_DURATION_TOLERANCE_SECONDS:
        return ValidationResult(
            valid=False,
            reason="video_too_long",
            duration_seconds=duration_seconds,
            size_bytes=size_bytes,
            format_name=format_name,
        )

    if size_bytes > sc.MAX_VIDEO_SIZE_BYTES:
        return ValidationResult(
            valid=False,
            reason="video_too_large",
            duration_seconds=duration_seconds,
            size_bytes=size_bytes,
            format_name=format_name,
        )

    if format_name not in _ALLOWED_FORMAT_NAMES:
        return ValidationResult(
            valid=False,
            reason="invalid_format",
            duration_seconds=duration_seconds,
            size_bytes=size_bytes,
            format_name=format_name,
        )

    return ValidationResult(
        valid=True,
        reason=None,
        duration_seconds=duration_seconds,
        size_bytes=size_bytes,
        format_name=format_name,
    )
