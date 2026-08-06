from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import src.infra.postgres.types


revision: str = 'c0e8b499fd2c'
down_revision: Union[str, Sequence[str], None] = '348ec2094e23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tbl_symbols',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=55), nullable=False),
    sa.Column('code', sa.String(length=55), nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('currency', sa.String(length=16), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['tbl_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_tbl_symbols_asset_id'), 'tbl_symbols', ['asset_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tbl_symbols_asset_id'), table_name='tbl_symbols')
    op.drop_table('tbl_symbols')
