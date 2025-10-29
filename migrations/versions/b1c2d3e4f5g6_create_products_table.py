"""Create products table

Revision ID: b1c2d3e4f5g6
Revises: a2b3c4d5e6f7
Create Date: 2025-10-29 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create products table with all fields
    op.create_table('products',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_sold', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('stock_status', sa.String(length=50), nullable=False, server_default='In Stock'),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('shipping_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('delivery_days', sa.String(length=50), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('rating', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('specifications', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('key_features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('return_policy', sa.String(length=255), nullable=True, server_default='30-day return policy'),
        sa.Column('warranty_info', sa.String(length=255), nullable=True),
        sa.Column('packaging_info', sa.String(length=255), nullable=True, server_default='Secure packaging for safe delivery'),
        sa.Column('condition_badge', sa.String(length=50), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, comment='Unique identifier'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_owner_id'), 'products', ['owner_id'], unique=False)
    op.create_index(op.f('ix_products_is_featured'), 'products', ['is_featured'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_products_sku'), table_name='products')
    op.drop_index(op.f('ix_products_is_featured'), table_name='products')
    op.drop_index(op.f('ix_products_owner_id'), table_name='products')
    op.drop_index(op.f('ix_products_category'), table_name='products')
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    
    # Drop table
    op.drop_table('products')

