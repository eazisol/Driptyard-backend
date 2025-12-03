"""add_is_suspended_suspended_at_last_login_to_users

Revision ID: 0c66d313034d
Revises: z9a0b1c2d3e4
Create Date: 2025-12-03 17:15:57.461826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c66d313034d'
down_revision: Union[str, None] = 'z9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_suspended column to users table
    op.add_column('users', sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add suspended_at column to users table
    op.add_column('users', sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add last_login column to users table
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    
    # Create index for is_suspended for performance
    op.create_index('idx_users_suspended', 'users', ['is_suspended'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_users_suspended', table_name='users')
    
    # Remove columns
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'suspended_at')
    op.drop_column('users', 'is_suspended')
