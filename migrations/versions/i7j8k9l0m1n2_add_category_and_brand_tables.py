"""add_category_and_brand_tables

Revision ID: i7j8k9l0m1n2
Revises: d656ee02f2ce
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'i7j8k9l0m1n2'
down_revision: Union[str, None] = 'd656ee02f2ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create genders table
    op.create_table('genders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier'),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_genders_id'), 'genders', ['id'], unique=False)
    op.create_index(op.f('ix_genders_name'), 'genders', ['name'], unique=True)

    # Create main_categories table
    op.create_table('main_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_main_categories_id'), 'main_categories', ['id'], unique=False)
    op.create_index(op.f('ix_main_categories_name'), 'main_categories', ['name'], unique=True)

    # Create category_types table
    op.create_table('category_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['parent_id'], ['main_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_category_types_id'), 'category_types', ['id'], unique=False)
    op.create_index(op.f('ix_category_types_name'), 'category_types', ['name'], unique=False)
    op.create_index(op.f('ix_category_types_parent_id'), 'category_types', ['parent_id'], unique=False)

    # Create sub_categories table
    op.create_table('sub_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gender_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['gender_id'], ['genders.id'], ),
        sa.ForeignKeyConstraint(['type_id'], ['category_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sub_categories_id'), 'sub_categories', ['id'], unique=False)
    op.create_index(op.f('ix_sub_categories_name'), 'sub_categories', ['name'], unique=False)
    op.create_index(op.f('ix_sub_categories_type_id'), 'sub_categories', ['type_id'], unique=False)
    op.create_index(op.f('ix_sub_categories_gender_id'), 'sub_categories', ['gender_id'], unique=False)

    # Create brands table
    op.create_table('brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brands_id'), 'brands', ['id'], unique=False)
    op.create_index(op.f('ix_brands_name'), 'brands', ['name'], unique=True)
    op.create_index(op.f('ix_brands_active'), 'brands', ['active'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_brands_active'), table_name='brands')
    op.drop_index(op.f('ix_brands_name'), table_name='brands')
    op.drop_index(op.f('ix_brands_id'), table_name='brands')
    op.drop_table('brands')
    
    op.drop_index(op.f('ix_sub_categories_gender_id'), table_name='sub_categories')
    op.drop_index(op.f('ix_sub_categories_type_id'), table_name='sub_categories')
    op.drop_index(op.f('ix_sub_categories_name'), table_name='sub_categories')
    op.drop_index(op.f('ix_sub_categories_id'), table_name='sub_categories')
    op.drop_table('sub_categories')
    
    op.drop_index(op.f('ix_category_types_parent_id'), table_name='category_types')
    op.drop_index(op.f('ix_category_types_name'), table_name='category_types')
    op.drop_index(op.f('ix_category_types_id'), table_name='category_types')
    op.drop_table('category_types')
    
    op.drop_index(op.f('ix_main_categories_name'), table_name='main_categories')
    op.drop_index(op.f('ix_main_categories_id'), table_name='main_categories')
    op.drop_table('main_categories')
    
    op.drop_index(op.f('ix_genders_name'), table_name='genders')
    op.drop_index(op.f('ix_genders_id'), table_name='genders')
    op.drop_table('genders')

