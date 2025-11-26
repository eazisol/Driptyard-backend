"""create moderator_permissions table

Revision ID: x7y8z9a0b1c2
Revises: w6x7y8z9a0b1
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'x7y8z9a0b1c2'
down_revision: Union[str, None] = 'w6x7y8z9a0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create moderator_permissions table
    op.create_table(
        'moderator_permissions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('can_spotlight', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_remove_spotlight', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_moderator_permissions_id'), 'moderator_permissions', ['id'], unique=False)
    op.create_index(op.f('ix_moderator_permissions_user_id'), 'moderator_permissions', ['user_id'], unique=True)
    op.create_index('idx_moderator_permissions_user', 'moderator_permissions', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop moderator_permissions table
    op.drop_index('idx_moderator_permissions_user', table_name='moderator_permissions')
    op.drop_index(op.f('ix_moderator_permissions_user_id'), table_name='moderator_permissions')
    op.drop_index(op.f('ix_moderator_permissions_id'), table_name='moderator_permissions')
    op.drop_table('moderator_permissions')

