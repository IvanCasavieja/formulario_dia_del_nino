import logging
import tempfile
import uuid
from pathlib import Path

from app import r2
from app.config import get_settings
from app.db import SessionLocal
from app.models import Submission, SubmissionStatus
from app.rekognition import detect_moderation_labels
from app.services import frame_extraction, moderation_rules, video_validation

settings = get_settings()
logger = logging.getLogger(__name__)

# Statuses a job is allowed to run/re-run from. UPLOADED is the normal starting point;
# PROCESSING is included so an RQ retry (which finds the flag already flipped by the
# first, failed attempt) doesn't get skipped by the "already handled" guard below.
_RUNNABLE_STATUSES = (SubmissionStatus.UPLOADED, SubmissionStatus.PROCESSING)


def process_submission_video(submission_id: str) -> None:
    db = SessionLocal()
    try:
        submission = db.get(Submission, uuid.UUID(submission_id))
        if submission is None:
            logger.warning("process_submission_video: submission %s not found", submission_id)
            return
        if submission.status not in _RUNNABLE_STATUSES:
            logger.info(
                "process_submission_video: submission %s status is %s - skipping (already processed)",
                submission_id,
                submission.status,
            )
            return

        submission.status = SubmissionStatus.PROCESSING
        db.commit()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            video_path = tmp_path / "video"
            r2.download_to_temp_file(submission.video_key, video_path)

            validation = video_validation.validate_video(video_path)
            if not validation.valid:
                _finalize(
                    db,
                    submission,
                    status=SubmissionStatus(settings.SERVER_VALIDATION_FAILURE_STATUS),
                    moderation_result={
                        "stage": "server_side_validation",
                        "reason": validation.reason,
                        "duration_seconds": validation.duration_seconds,
                        "size_bytes": validation.size_bytes,
                        "format_name": validation.format_name,
                    },
                )
                return

            submission.video_duration_seconds = validation.duration_seconds
            submission.video_actual_size_bytes = validation.size_bytes

            frames_dir = tmp_path / "frames"
            frame_paths = frame_extraction.extract_frames(video_path, validation.duration_seconds, frames_dir)

            per_frame_labels = [detect_moderation_labels(p.read_bytes()) for p in frame_paths]
            aggregated = moderation_rules.aggregate_labels(per_frame_labels)
            decision = moderation_rules.decide(aggregated)

            _finalize(
                db,
                submission,
                status=SubmissionStatus(decision.status),
                moderation_result={
                    "stage": "rekognition",
                    "reason": decision.reason,
                    "frame_count": len(frame_paths),
                    "triggered_labels": decision.triggered_labels,
                    "thresholds": {
                        "reject_confidence": settings.MODERATION_REJECT_CONFIDENCE,
                        "review_confidence": settings.MODERATION_REVIEW_CONFIDENCE,
                        "reject_categories": settings.moderation_reject_categories_list,
                    },
                },
            )
    finally:
        db.close()


def _finalize(db, submission: Submission, status: SubmissionStatus, moderation_result: dict) -> None:
    submission.status = status
    submission.moderation_result = moderation_result
    db.commit()


def on_submission_failure(job, connection, type, value, traceback) -> None:
    """RQ on_failure callback, invoked once retries are exhausted. Without this, a
    submission that keeps hitting transient errors (R2/Rekognition throttling, etc.)
    would stay stuck at PROCESSING forever with no way for admins to notice."""
    submission_id = job.args[0]
    db = SessionLocal()
    try:
        submission = db.get(Submission, uuid.UUID(submission_id))
        if submission and submission.status in _RUNNABLE_STATUSES:
            submission.status = SubmissionStatus.FAILED
            submission.moderation_result = {
                "stage": "worker_exception",
                "reason": "exhausted_retries",
                "error": str(value),
            }
            db.commit()
    finally:
        db.close()
