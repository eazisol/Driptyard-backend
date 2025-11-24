"""add spotlight_end_time to products

Revision ID: u9v0w1x2y3z4
Revises: t7u8v9w0x1y2
Create Date: 2025-11-24 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'u9v0w1x2y3z4'
down_revision: Union[str, None] = 't7u8v9w0x1y2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add spotlight_end_time column to products table
    op.add_column('products', sa.Column('spotlight_end_time', sa.DateTime(timezone=True), nullable=True))
    
    # Create index on spotlight_end_time for efficient queries
    op.create_index('ix_products_spotlight_end_time', 'products', ['spotlight_end_time'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_products_spotlight_end_time', table_name='products')
    
    # Drop column
    op.drop_column('products', 'spotlight_end_time')

