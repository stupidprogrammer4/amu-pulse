from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import src.infra.postgres.types


revision: str = 'f47cc75d3405'
down_revision: Union[str, Sequence[str], None] = '98373ca62de1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tbl_assets',
        sa.Column(
            'primary_color',
            sa.String(length=55),
            nullable=False,
            server_default='#c8a44b',
        ),
    )
    op.add_column(
        'tbl_symbols',
        sa.Column(
            'primary_color',
            sa.String(length=55),
            nullable=False,
            server_default='#c8a44b',
        ),
    )
    op.alter_column('tbl_assets', 'primary_color', server_default=None)
    op.alter_column('tbl_symbols', 'primary_color', server_default=None)


def downgrade() -> None:
    op.drop_column('tbl_symbols', 'primary_color')
    op.drop_column('tbl_assets', 'primary_color')
