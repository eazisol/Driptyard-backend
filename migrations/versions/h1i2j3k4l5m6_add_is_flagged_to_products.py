"""add is_flagged to products

Revision ID: h1i2j3k4l5m6
Revises: g7h8i9j0k1l2
Create Date: 2025-01-15 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_flagged column to products table
    op.add_column('products', sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create index for quick lookups
    op.create_index(op.f('ix_products_is_flagged'), 'products', ['is_flagged'], unique=False)
    
    # Drop server default to allow SQLAlchemy to manage defaults
    op.alter_column('products', 'is_flagged', server_default=None)


def downgrade() -> None:
    # Drop index and column
    op.drop_index(op.f('ix_products_is_flagged'), table_name='products')
    op.drop_column('products', 'is_flagged')

