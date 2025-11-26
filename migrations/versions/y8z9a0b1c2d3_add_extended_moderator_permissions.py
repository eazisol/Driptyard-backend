"""add extended moderator permissions

Revision ID: y8z9a0b1c2d3
Revises: x7y8z9a0b1c2
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'y8z9a0b1c2d3'
down_revision: Union[str, None] = 'x7y8z9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new permission columns to moderator_permissions table
    op.add_column('moderator_permissions', sa.Column('can_see_dashboard', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('moderator_permissions', sa.Column('can_see_users', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('moderator_permissions', sa.Column('can_manage_users', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('moderator_permissions', sa.Column('can_see_listings', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('moderator_permissions', sa.Column('can_manage_listings', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('moderator_permissions', sa.Column('can_see_spotlight_history', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('moderator_permissions', sa.Column('can_see_flagged_content', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('moderator_permissions', sa.Column('can_manage_flagged_content', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove new permission columns
    op.drop_column('moderator_permissions', 'can_manage_flagged_content')
    op.drop_column('moderator_permissions', 'can_see_flagged_content')
    op.drop_column('moderator_permissions', 'can_see_spotlight_history')
    op.drop_column('moderator_permissions', 'can_manage_listings')
    op.drop_column('moderator_permissions', 'can_see_listings')
    op.drop_column('moderator_permissions', 'can_manage_users')
    op.drop_column('moderator_permissions', 'can_see_users')
    op.drop_column('moderator_permissions', 'can_see_dashboard')

