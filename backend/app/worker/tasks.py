import logging
import tempfile
from pathlib import Path

from app import r2
from app.config import get_settings
from app.models import SubmissionStatus
from app.salesforce import SalesforceSyncError, upsert_row
from app.services import video_validation

settings = get_settings()
logger = logging.getLogger(__name__)


def process_submission_video(video_key: str, child_cedula: str) -> None:
    """Runs after confirm_upload, in-process via FastAPI's BackgroundTasks (see the
    TEMP note in routers/submissions.py - no separate worker service on the free
    tier). Re-validates the real uploaded file and records the outcome as the only
    place this data lives: Salesforce, keyed by Cedula_Nino (the DE's primary key -
    same field confirm_upload already wrote the row under)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = Path(tmp_dir) / "video"

        try:
            r2.download_to_temp_file(video_key, video_path)
        except Exception:
            logger.exception("process_submission_video: failed to download %s from R2", video_key)
            _try_upsert_status(child_cedula, SubmissionStatus.FAILED.value, "r2_download_failed")
            return

        validation = video_validation.validate_video(video_path)
        if not validation.valid:
            _try_upsert_status(
                child_cedula,
                settings.SERVER_VALIDATION_FAILURE_STATUS,
                f"server_side_validation:{validation.reason}",
            )
            return

        _try_upsert_status(child_cedula, SubmissionStatus.NEEDS_REVIEW.value, "passed_server_side_validation")


def _try_upsert_status(child_cedula: str, new_status: str, moderation_result: str) -> None:
    try:
        upsert_row({"Cedula_Nino": child_cedula, "Status": new_status, "ModerationResult": moderation_result})
    except SalesforceSyncError:
        # Best-effort: the row already exists (confirm_upload wrote it as "uploaded")
        # so there's no submission to "lose" here, just a stale status until the next
        # manual re-run - log it so it's visible, but don't raise (this already runs
        # detached from the original HTTP request via BackgroundTasks).
        logger.exception(
            "process_submission_video: failed to record status=%s for child_cedula=%s", new_status, child_cedula
        )
