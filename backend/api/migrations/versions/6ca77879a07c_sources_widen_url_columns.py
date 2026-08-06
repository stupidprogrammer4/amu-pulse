from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import src.infra.postgres.types


revision: str = '6ca77879a07c'
down_revision: Union[str, Sequence[str], None] = '4a38e58a7011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('tbl_sources', 'website_url',
               existing_type=sa.VARCHAR(length=55),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.alter_column('tbl_sources', 'icon_url',
               existing_type=sa.VARCHAR(length=55),
               type_=sa.String(length=255),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('tbl_sources', 'icon_url',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=55),
               existing_nullable=False)
    op.alter_column('tbl_sources', 'website_url',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=55),
               existing_nullable=False)
