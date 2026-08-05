"""add admins table

Revision ID: 8703876a8a55
Revises: aaae3614a91e
Create Date: 2026-08-05 15:41:05.600252

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import src.infra.postgres.types

# revision identifiers, used by Alembic.
revision: str = "8703876a8a55"
down_revision: Union[str, Sequence[str], None] = "aaae3614a91e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # autogenerate also proposed dropping tbl_users, tbl_roles,
    # tbl_login_logs and tbl_refresh_tokens, which are leftovers in a
    # developer volume rather than anything this chain created. Dropping
    # them is a decision of its own, so this revision only adds the table.
    op.create_table(
        "tbl_admins",
        sa.Column(
            "created_at",
            src.infra.postgres.types._TZDateTime(),
            server_default="NOW()",
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            src.infra.postgres.types._TZDateTime(),
            server_default="NOW()",
            nullable=False,
        ),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=55), nullable=False),
        sa.Column("hashed_password", sa.String(length=100), nullable=False),
        sa.Column("is_super_admin", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("tbl_admins")
