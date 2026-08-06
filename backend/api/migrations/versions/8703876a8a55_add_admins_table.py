
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import src.infra.postgres.types

revision: str = "8703876a8a55"
down_revision: Union[str, Sequence[str], None] = "aaae3614a91e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.drop_table("tbl_admins")
