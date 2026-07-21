import logging
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.db import SessionLocal
from app.models import Submission
from app.salesforce import insert_data_extension_row

settings = get_settings()
logger = logging.getLogger(__name__)


def _submission_to_de_fields(submission: Submission) -> dict:
    """Maps a Submission row to Data Extension column names. This is the one place to
    edit if the actual Data Extension's schema uses different field names - nothing
    else needs to change."""
    return {
        "SubmissionId": str(submission.id),
        "ParentFirstName": submission.parent_first_name,
        "ParentLastName": submission.parent_last_name,
        "ParentCedula": submission.parent_cedula,
        "ParentEmail": submission.parent_email,
        "ParentPhone": submission.parent_phone,
        "ChildFullName": submission.child_full_name,
        "ChildCedula": submission.child_cedula,
        "Status": submission.status.value,
        "SubmittedAt": submission.created_at.isoformat() if submission.created_at else None,
    }


def sync_submission_to_salesforce(submission_id: str) -> None:
    db = SessionLocal()
    try:
        submission = db.get(Submission, uuid.UUID(submission_id))
        if submission is None:
            logger.warning("sync_submission_to_salesforce: submission %s not found", submission_id)
            return
        if submission.salesforce_synced_at is not None:
            # Idempotency guard, same pattern as the moderation job: a retried/replayed
            # call is a clean no-op instead of inserting a duplicate row.
            logger.info("sync_submission_to_salesforce: submission %s already synced - skipping", submission_id)
            return

        fields = _submission_to_de_fields(submission)
        insert_data_extension_row(fields)

        submission.salesforce_synced_at = datetime.now(timezone.utc)
        submission.salesforce_sync_error = None
        db.commit()
    finally:
        db.close()


def on_salesforce_sync_failure(job, connection, type, value, traceback) -> None:
    """RQ on_failure callback, invoked once retries are exhausted. Records the error
    for the admin panel to surface - the raffle/moderation flow was never blocked by
    this in the first place, so there's nothing else to roll back."""
    submission_id = job.args[0]
    db = SessionLocal()
    try:
        submission = db.get(Submission, uuid.UUID(submission_id))
        if submission and submission.salesforce_synced_at is None:
            submission.salesforce_sync_error = str(value)
            db.commit()
    finally:
        db.close()
