"""Marks abandoned pending_upload submissions as EXPIRED. Run periodically as a Render
cron job (`python -m app.worker.cleanup`) - simpler than adding rq-scheduler for a
single once-an-hour task."""
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.db import SessionLocal
from app.models import Submission, SubmissionStatus

settings = get_settings()


def cleanup_stale_pending_uploads() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.PENDING_UPLOAD_EXPIRY_SECONDS)
    db = SessionLocal()
    try:
        stale = (
            db.query(Submission)
            .filter(Submission.status == SubmissionStatus.PENDING_UPLOAD)
            .filter(Submission.created_at < cutoff)
            .all()
        )
        for submission in stale:
            submission.status = SubmissionStatus.EXPIRED
        db.commit()
        return len(stale)
    finally:
        db.close()


if __name__ == "__main__":
    count = cleanup_stale_pending_uploads()
    print(f"Marked {count} stale pending_upload submission(s) as expired")
