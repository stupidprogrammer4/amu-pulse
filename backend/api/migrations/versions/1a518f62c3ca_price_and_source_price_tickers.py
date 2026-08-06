from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import src.infra.postgres.types


revision: str = '1a518f62c3ca'
down_revision: Union[str, Sequence[str], None] = 'f47cc75d3405'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tbl_price_tickers',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('price', sa.BigInteger(), nullable=False),
    sa.Column('timestamp', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['tbl_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tbl_price_tickers_asset_id'), 'tbl_price_tickers', ['asset_id'], unique=False)
    op.create_table('tbl_source_price_tickers',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('symbol_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.Column('price', sa.BigInteger(), nullable=False),
    sa.Column('timestamp', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['tbl_sources.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['symbol_id'], ['tbl_symbols.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tbl_source_price_tickers_source_id'), 'tbl_source_price_tickers', ['source_id'], unique=False)
    op.create_index(op.f('ix_tbl_source_price_tickers_symbol_id'), 'tbl_source_price_tickers', ['symbol_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tbl_source_price_tickers_symbol_id'), table_name='tbl_source_price_tickers')
    op.drop_index(op.f('ix_tbl_source_price_tickers_source_id'), table_name='tbl_source_price_tickers')
    op.drop_table('tbl_source_price_tickers')
    op.drop_index(op.f('ix_tbl_price_tickers_asset_id'), table_name='tbl_price_tickers')
    op.drop_table('tbl_price_tickers')
