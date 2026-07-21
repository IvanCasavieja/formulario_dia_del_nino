"""Loads /shared/validationConstants.json — the single source of truth for
validation limits that the frontend also imports directly, so the two never drift apart."""
import json
import os
from pathlib import Path

# backend/app/shared_constants.py -> 3 parents up is the repo root in local dev
# (Formulario/shared/...); in the Docker image (WORKDIR /app, backend/ copied to /app)
# the same 3-parents-up resolution lands on "/", matching the separate `COPY shared/
# /shared/` step in the Dockerfile. SHARED_CONSTANTS_PATH is an escape hatch for any
# other layout.
_CANDIDATE_PATHS = [
    Path(p) for p in [os.environ.get("SHARED_CONSTANTS_PATH")] if p
] + [
    Path(__file__).resolve().parent.parent.parent / "shared" / "validationConstants.json",
]


def _load() -> dict:
    for path in _CANDIDATE_PATHS:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(
        f"validationConstants.json not found in any of: {[str(p) for p in _CANDIDATE_PATHS]}"
    )


CONSTANTS = _load()

MAX_VIDEO_DURATION_SECONDS: float = CONSTANTS["MAX_VIDEO_DURATION_SECONDS"]
MAX_VIDEO_DURATION_TOLERANCE_SECONDS: float = CONSTANTS["MAX_VIDEO_DURATION_TOLERANCE_SECONDS"]
MAX_VIDEO_SIZE_BYTES: int = CONSTANTS["MAX_VIDEO_SIZE_BYTES"]
ALLOWED_VIDEO_MIME_TYPES: list[str] = CONSTANTS["ALLOWED_VIDEO_MIME_TYPES"]
ALLOWED_VIDEO_EXTENSIONS: list[str] = CONSTANTS["ALLOWED_VIDEO_EXTENSIONS"]
PARENT_CEDULA_MIN_DIGITS: int = CONSTANTS["PARENT_CEDULA_MIN_DIGITS"]
PARENT_CEDULA_MAX_DIGITS: int = CONSTANTS["PARENT_CEDULA_MAX_DIGITS"]
CHILD_CEDULA_MIN_DIGITS: int = CONSTANTS["CHILD_CEDULA_MIN_DIGITS"]
CHILD_CEDULA_MAX_DIGITS: int = CONSTANTS["CHILD_CEDULA_MAX_DIGITS"]
PHONE_MIN_DIGITS: int = CONSTANTS["PHONE_MIN_DIGITS"]
PHONE_MAX_DIGITS: int = CONSTANTS["PHONE_MAX_DIGITS"]

MIME_TYPE_TO_EXTENSION: dict[str, str] = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}
