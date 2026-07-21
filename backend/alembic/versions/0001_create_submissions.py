"""create submissions table

Revision ID: 0001
Revises:
Create Date: 2026-07-21

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

submission_status_enum = postgresql.ENUM(
    "pending_upload",
    "uploaded",
    "processing",
    "needs_review",
    "approved",
    "rejected",
    "failed",
    "expired",
    name="submission_status",
)


def upgrade() -> None:
    submission_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_first_name", sa.String(), nullable=False),
        sa.Column("parent_last_name", sa.String(), nullable=False),
        sa.Column("parent_cedula", sa.String(), nullable=False),
        sa.Column("parent_email", sa.String(), nullable=False),
        sa.Column("parent_phone", sa.String(), nullable=False),
        sa.Column("child_full_name", sa.String(), nullable=False),
        sa.Column("child_cedula", sa.String(), nullable=False),
        sa.Column("video_key", sa.String(), nullable=False),
        sa.Column("video_content_type", sa.String(), nullable=False),
        sa.Column("video_declared_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("video_declared_duration_seconds", sa.Float(), nullable=True),
        sa.Column("video_actual_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("video_duration_seconds", sa.Float(), nullable=True),
        sa.Column("status", submission_status_enum, nullable=False, server_default="pending_upload"),
        sa.Column("moderation_result", postgresql.JSONB(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("admin_reviewed_by", sa.String(), nullable=True),
        sa.Column("admin_decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terms_accepted", sa.Boolean(), nullable=False),
        sa.Column("terms_version", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_submissions_parent_cedula", "submissions", ["parent_cedula"])
    op.create_index("ix_submissions_parent_email", "submissions", ["parent_email"])
    op.create_index("ix_submissions_child_cedula", "submissions", ["child_cedula"], unique=True)
    op.create_index("ix_submissions_status", "submissions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_submissions_status", table_name="submissions")
    op.drop_index("ix_submissions_child_cedula", table_name="submissions")
    op.drop_index("ix_submissions_parent_email", table_name="submissions")
    op.drop_index("ix_submissions_parent_cedula", table_name="submissions")
    op.drop_table("submissions")
    submission_status_enum.drop(op.get_bind(), checkfirst=True)
