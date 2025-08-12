"""Initial migration

Revision ID: 9474ebb3e67b
Revises:
Create Date: 2025-08-12 20:38:02.938394

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9474ebb3e67b"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop existing tables if they exist
    op.execute("DROP TABLE IF EXISTS activities")
    op.execute("DROP TABLE IF EXISTS brand_states")

    # Create tables
    op.create_table(
        "brand_states",
        sa.Column("brand_id", sa.String(), nullable=False),
        sa.Column("browser_profile_id", sa.String(), nullable=False),
        sa.Column("is_connected", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.PrimaryKeyConstraint("brand_id"),
    )

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("brand_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("activities")
    op.drop_table("brand_states")
