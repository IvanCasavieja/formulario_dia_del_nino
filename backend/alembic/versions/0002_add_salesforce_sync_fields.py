"""add salesforce sync tracking fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-21

"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("salesforce_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("submissions", sa.Column("salesforce_sync_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("submissions", "salesforce_sync_error")
    op.drop_column("submissions", "salesforce_synced_at")
