"""add is_moderator to users

Revision ID: w6x7y8z9a0b1
Revises: v5w6x7y8z9a0
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'w6x7y8z9a0b1'
down_revision: Union[str, None] = 'v5w6x7y8z9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_moderator column to users table
    op.add_column('users', sa.Column('is_moderator', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_moderator column from users table
    op.drop_column('users', 'is_moderator')

