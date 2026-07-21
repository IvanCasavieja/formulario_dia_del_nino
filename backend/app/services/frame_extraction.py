import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Spread across the middle of the clip, avoiding the very first/last instant where
# loading screens or black frames are common.
_TIMESTAMP_FRACTIONS = [0.10, 0.30, 0.50, 0.70, 0.90]


def extract_frames(video_path: Path, duration_seconds: float, out_dir: Path) -> list[Path]:
    """Extracts one frame per timestamp fraction via ffmpeg.

    One ffmpeg invocation per timestamp rather than a single complex filtergraph -
    simpler to reason about and debug, and fine at this volume.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []

    for i, fraction in enumerate(_TIMESTAMP_FRACTIONS):
        timestamp = max(duration_seconds * fraction, 0.0)
        out_path = out_dir / f"frame_{i}.jpg"
        try:
            completed = subprocess.run(
                [
                    "ffmpeg",
                    "-ss", f"{timestamp:.3f}",
                    "-i", str(video_path),
                    "-frames:v", "1",
                    "-q:v", "2",
                    "-y",
                    str(out_path),
                ],
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            logger.warning("ffmpeg frame extraction failed at %.2fs: %s", timestamp, e)
            continue

        if completed.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
            frame_paths.append(out_path)
        else:
            logger.warning(
                "ffmpeg frame extraction at %.2fs exited %s: %s",
                timestamp,
                completed.returncode,
                completed.stderr.decode(errors="replace") if completed.stderr else "",
            )

    return frame_paths
