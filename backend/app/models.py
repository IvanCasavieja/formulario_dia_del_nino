import enum


class SubmissionStatus(str, enum.Enum):
    PENDING_UPLOAD = "pending_upload"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"  # technical failure (corrupt file, download/probe crash) - not a moderation verdict
    EXPIRED = "expired"  # pending_upload abandoned, never confirmed within the TTL window
