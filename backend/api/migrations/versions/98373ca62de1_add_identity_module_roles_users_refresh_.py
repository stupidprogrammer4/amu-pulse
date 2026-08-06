from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import src.infra.postgres.types
from sqlalchemy.dialects import postgresql

revision: str = '98373ca62de1'
down_revision: Union[str, Sequence[str], None] = 'c0e8b499fd2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tbl_roles',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=55), nullable=False),
    sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('tbl_users',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('mobile', sa.String(length=11), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('role_id', sa.BigInteger(), nullable=False),
    sa.Column('last_login_at', src.infra.postgres.types._TZDateTime(), nullable=True),
    sa.Column('last_login_ip', sa.String(length=45), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
    sa.Column('locked_until', src.infra.postgres.types._TZDateTime(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['tbl_roles.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('mobile')
    )
    op.create_index(op.f('ix_tbl_users_role_id'), 'tbl_users', ['role_id'], unique=False)
    op.create_table('tbl_login_logs',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=True),
    sa.Column('mobile', sa.String(length=11), nullable=False),
    sa.Column('ip', sa.String(length=45), nullable=True),
    sa.Column('device', sa.String(length=255), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['tbl_users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tbl_login_logs_user_id'), 'tbl_login_logs', ['user_id'], unique=False)
    op.create_table('tbl_refresh_tokens',
    sa.Column('created_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('updated_at', src.infra.postgres.types._TZDateTime(), server_default='NOW()', nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', src.infra.postgres.types._TZDateTime(), nullable=False),
    sa.Column('revoked_at', src.infra.postgres.types._TZDateTime(), nullable=True),
    sa.Column('device', sa.String(length=255), nullable=True),
    sa.Column('ip', sa.String(length=45), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['tbl_users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_tbl_refresh_tokens_user_id'), 'tbl_refresh_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tbl_refresh_tokens_user_id'), table_name='tbl_refresh_tokens')
    op.drop_table('tbl_refresh_tokens')
    op.drop_index(op.f('ix_tbl_login_logs_user_id'), table_name='tbl_login_logs')
    op.drop_table('tbl_login_logs')
    op.drop_index(op.f('ix_tbl_users_role_id'), table_name='tbl_users')
    op.drop_table('tbl_users')
    op.drop_table('tbl_roles')
