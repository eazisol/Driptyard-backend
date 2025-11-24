"""create spotlights table

Revision ID: s1t2u3v4w5x6
Revises: r7s8t9u0v1w2
Create Date: 2025-11-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 's1t2u3v4w5x6'
down_revision: Union[str, None] = 'r7s8t9u0v1w2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create spotlights table
    op.create_table(
        'spotlights',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('applied_by', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['applied_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )
    
    # Create indexes
    op.create_index('ix_spotlights_id', 'spotlights', ['id'], unique=False)
    op.create_index('ix_spotlights_product_id', 'spotlights', ['product_id'], unique=True)
    op.create_index('ix_spotlights_end_time', 'spotlights', ['end_time'], unique=False)
    op.create_index('ix_spotlights_status', 'spotlights', ['status'], unique=False)
    op.create_index('idx_spotlight_status_end_time', 'spotlights', ['status', 'end_time'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_spotlight_status_end_time', table_name='spotlights')
    op.drop_index('ix_spotlights_status', table_name='spotlights')
    op.drop_index('ix_spotlights_end_time', table_name='spotlights')
    op.drop_index('ix_spotlights_product_id', table_name='spotlights')
    op.drop_index('ix_spotlights_id', table_name='spotlights')
    
    # Drop table
    op.drop_table('spotlights')

