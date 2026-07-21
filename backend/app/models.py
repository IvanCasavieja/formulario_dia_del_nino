import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SubmissionStatus(str, enum.Enum):
    PENDING_UPLOAD = "pending_upload"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"  # technical failure (corrupt file, worker crash) - not a moderation verdict
    EXPIRED = "expired"  # pending_upload abandoned, never confirmed within the TTL window


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent / guardian
    parent_first_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_last_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_cedula: Mapped[str] = mapped_column(String, nullable=False, index=True)
    parent_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    parent_phone: Mapped[str] = mapped_column(String, nullable=False)

    # Child
    child_full_name: Mapped[str] = mapped_column(String, nullable=False)
    child_cedula: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)

    # Video
    video_key: Mapped[str] = mapped_column(String, nullable=False)
    video_content_type: Mapped[str] = mapped_column(String, nullable=False)
    video_declared_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    video_declared_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_actual_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    video_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        nullable=False,
        default=SubmissionStatus.PENDING_UPLOAD,
    )
    moderation_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    admin_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    terms_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    terms_version: Mapped[str] = mapped_column(String, nullable=False)

    ip_address: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Best-effort sync to a Salesforce Marketing Cloud Data Extension, fired once when
    # the upload is confirmed (see routers/submissions.py + worker/salesforce_tasks.py).
    # Never blocks the submission flow - these two fields are purely for admin visibility
    # into whether it worked.
    salesforce_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    salesforce_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
