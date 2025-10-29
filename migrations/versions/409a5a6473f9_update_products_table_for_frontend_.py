"""update_products_table_for_frontend_payload

Revision ID: 409a5a6473f9
Revises: b1c2d3e4f5g6
Create Date: 2025-10-29 16:30:51.590753

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '409a5a6473f9'
down_revision: Union[str, None] = 'b1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns for frontend payload
    op.add_column('products', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('deal_method', sa.String(length=20), nullable=False, server_default='delivery'))
    op.add_column('products', sa.Column('meetup_date', sa.String(length=10), nullable=True))
    op.add_column('products', sa.Column('meetup_location', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('meetup_time', sa.String(length=5), nullable=True))
    
    # Copy data from name to title
    op.execute("UPDATE products SET title = name WHERE title IS NULL")
    
    # Make title not nullable
    op.alter_column('products', 'title', nullable=False)
    
    # Create new indexes
    op.create_index(op.f('ix_products_title'), 'products', ['title'], unique=False)
    op.create_index(op.f('ix_products_deal_method'), 'products', ['deal_method'], unique=False)
    
    # Drop old name column and its index
    op.drop_index('ix_products_name', table_name='products')
    op.drop_column('products', 'name')


def downgrade() -> None:
    # Add back name column
    op.add_column('products', sa.Column('name', sa.String(length=255), nullable=True))
    
    # Copy data from title to name
    op.execute("UPDATE products SET name = title WHERE name IS NULL")
    
    # Make name not nullable
    op.alter_column('products', 'name', nullable=False)
    
    # Create old index
    op.create_index('ix_products_name', 'products', ['name'], unique=False)
    
    # Drop new columns and indexes
    op.drop_index(op.f('ix_products_deal_method'), table_name='products')
    op.drop_index(op.f('ix_products_title'), table_name='products')
    op.drop_column('products', 'meetup_time')
    op.drop_column('products', 'meetup_location')
    op.drop_column('products', 'meetup_date')
    op.drop_column('products', 'deal_method')
    op.drop_column('products', 'title')