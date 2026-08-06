from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import src.infra.postgres.types


revision: str = '348ec2094e23'
down_revision: Union[str, Sequence[str], None] = 'adfdb40ce6d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tbl_asset_switches',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('switch', sa.String(length=55), nullable=False),
    sa.Column('priority', sa.SmallInteger(), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['tbl_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asset_id', 'switch')
    )
    op.create_index(op.f('ix_tbl_asset_switches_asset_id'), 'tbl_asset_switches', ['asset_id'], unique=False)
    op.drop_column('tbl_asset_configs', 'switch')


def downgrade() -> None:
    op.add_column('tbl_asset_configs', sa.Column('switch', sa.VARCHAR(length=55), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_tbl_asset_switches_asset_id'), table_name='tbl_asset_switches')
    op.drop_table('tbl_asset_switches')
