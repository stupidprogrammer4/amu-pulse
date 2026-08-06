from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import src.infra.postgres.types


revision: str = 'aaae3614a91e'
down_revision: Union[str, Sequence[str], None] = '1a518f62c3ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tbl_candles',
    sa.Column('timeframe', sa.String(length=8), nullable=False),
    sa.Column('open', sa.BigInteger(), nullable=False),
    sa.Column('high', sa.BigInteger(), nullable=False),
    sa.Column('low', sa.BigInteger(), nullable=False),
    sa.Column('close', sa.BigInteger(), nullable=False),
    sa.Column('st_ts', sa.BigInteger(), nullable=False),
    sa.Column('en_ts', sa.BigInteger(), nullable=False),
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['tbl_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asset_id', 'timeframe', 'st_ts')
    )
    op.create_index(op.f('ix_tbl_candles_asset_id'), 'tbl_candles', ['asset_id'], unique=False)
    op.create_table('tbl_source_candles',
    sa.Column('timeframe', sa.String(length=8), nullable=False),
    sa.Column('open', sa.BigInteger(), nullable=False),
    sa.Column('high', sa.BigInteger(), nullable=False),
    sa.Column('low', sa.BigInteger(), nullable=False),
    sa.Column('close', sa.BigInteger(), nullable=False),
    sa.Column('st_ts', sa.BigInteger(), nullable=False),
    sa.Column('en_ts', sa.BigInteger(), nullable=False),
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('symbol_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['tbl_sources.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['symbol_id'], ['tbl_symbols.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol_id', 'source_id', 'timeframe', 'st_ts')
    )
    op.create_index(op.f('ix_tbl_source_candles_source_id'), 'tbl_source_candles', ['source_id'], unique=False)
    op.create_index(op.f('ix_tbl_source_candles_symbol_id'), 'tbl_source_candles', ['symbol_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tbl_source_candles_symbol_id'), table_name='tbl_source_candles')
    op.drop_index(op.f('ix_tbl_source_candles_source_id'), table_name='tbl_source_candles')
    op.drop_table('tbl_source_candles')
    op.drop_index(op.f('ix_tbl_candles_asset_id'), table_name='tbl_candles')
    op.drop_table('tbl_candles')
