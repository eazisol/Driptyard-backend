"""create spotlight history table

Revision ID: t7u8v9w0x1y2
Revises: s1t2u3v4w5x6
Create Date: 2025-11-24 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 't7u8v9w0x1y2'
down_revision: Union[str, None] = 's1t2u3v4w5x6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create spotlight_history table
    op.create_table(
        'spotlight_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('spotlight_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('applied_by', sa.Integer(), nullable=False),
        sa.Column('removed_by', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['applied_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['removed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['spotlight_id'], ['spotlights.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_spotlight_history_id', 'spotlight_history', ['id'], unique=False)
    op.create_index('ix_spotlight_history_product_id', 'spotlight_history', ['product_id'], unique=False)
    op.create_index('ix_spotlight_history_action', 'spotlight_history', ['action'], unique=False)
    op.create_index('idx_spotlight_history_created', 'spotlight_history', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_spotlight_history_created', table_name='spotlight_history')
    op.drop_index('ix_spotlight_history_action', table_name='spotlight_history')
    op.drop_index('ix_spotlight_history_product_id', table_name='spotlight_history')
    op.drop_index('ix_spotlight_history_id', table_name='spotlight_history')
    
    # Drop table
    op.drop_table('spotlight_history')

