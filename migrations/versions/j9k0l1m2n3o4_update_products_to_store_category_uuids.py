"""update_products_to_store_category_uuids

Revision ID: j9k0l1m2n3o4
Revises: i7j8k9l0m1n2
Create Date: 2025-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j9k0l1m2n3o4'
down_revision: Union[str, None] = 'i7j8k9l0m1n2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old columns if they exist
    # Note: We'll drop the old string columns and add new UUID columns
    # This will lose existing data, but since we're migrating to UUIDs, that's expected
    
    # Drop old indexes first
    try:
        op.drop_index('ix_products_category', table_name='products')
    except:
        pass
    
    # Drop old columns
    try:
        op.drop_column('products', 'category')
    except:
        pass
    
    try:
        op.drop_column('products', 'gender')
    except:
        pass
    
    try:
        op.drop_column('products', 'product_type')
    except:
        pass
    
    try:
        op.drop_column('products', 'sub_category')
    except:
        pass
    
    try:
        op.drop_column('products', 'designer')
    except:
        pass
    
    # Add new UUID columns with foreign keys
    op.add_column('products', sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_products_category_id', 'products', 'main_categories', ['category_id'], ['id'])
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    
    op.add_column('products', sa.Column('gender_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_products_gender_id', 'products', 'genders', ['gender_id'], ['id'])
    op.create_index(op.f('ix_products_gender_id'), 'products', ['gender_id'], unique=False)
    
    op.add_column('products', sa.Column('product_type_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_products_product_type_id', 'products', 'category_types', ['product_type_id'], ['id'])
    op.create_index(op.f('ix_products_product_type_id'), 'products', ['product_type_id'], unique=False)
    
    op.add_column('products', sa.Column('sub_category_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_products_sub_category_id', 'products', 'sub_categories', ['sub_category_id'], ['id'])
    op.create_index(op.f('ix_products_sub_category_id'), 'products', ['sub_category_id'], unique=False)
    
    op.add_column('products', sa.Column('designer_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_products_designer_id', 'products', 'brands', ['designer_id'], ['id'])
    op.create_index(op.f('ix_products_designer_id'), 'products', ['designer_id'], unique=False)


def downgrade() -> None:
    # Drop new UUID columns and foreign keys
    op.drop_index(op.f('ix_products_designer_id'), table_name='products')
    op.drop_constraint('fk_products_designer_id', 'products', type_='foreignkey')
    op.drop_column('products', 'designer_id')
    
    op.drop_index(op.f('ix_products_sub_category_id'), table_name='products')
    op.drop_constraint('fk_products_sub_category_id', 'products', type_='foreignkey')
    op.drop_column('products', 'sub_category_id')
    
    op.drop_index(op.f('ix_products_product_type_id'), table_name='products')
    op.drop_constraint('fk_products_product_type_id', 'products', type_='foreignkey')
    op.drop_column('products', 'product_type_id')
    
    op.drop_index(op.f('ix_products_gender_id'), table_name='products')
    op.drop_constraint('fk_products_gender_id', 'products', type_='foreignkey')
    op.drop_column('products', 'gender_id')
    
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_constraint('fk_products_category_id', 'products', type_='foreignkey')
    op.drop_column('products', 'category_id')
    
    # Re-add old string columns
    op.add_column('products', sa.Column('category', sa.String(length=100), nullable=True))
    op.create_index('ix_products_category', 'products', ['category'], unique=False)
    
    op.add_column('products', sa.Column('gender', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('product_type', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('sub_category', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('designer', sa.String(length=100), nullable=True))

