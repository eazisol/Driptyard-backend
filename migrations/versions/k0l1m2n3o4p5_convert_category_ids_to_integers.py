"""convert_category_ids_to_integers

Revision ID: k0l1m2n3o4p5
Revises: j9k0l1m2n3o4
Create Date: 2025-01-20 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'k0l1m2n3o4p5'
down_revision: Union[str, None] = 'j9k0l1m2n3o4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Drop all foreign key constraints that reference category tables
    op.drop_constraint('fk_products_category_id', 'products', type_='foreignkey')
    op.drop_constraint('fk_products_gender_id', 'products', type_='foreignkey')
    op.drop_constraint('fk_products_product_type_id', 'products', type_='foreignkey')
    op.drop_constraint('fk_products_sub_category_id', 'products', type_='foreignkey')
    op.drop_constraint('fk_products_designer_id', 'products', type_='foreignkey')
    
    # Drop foreign keys in category_types and sub_categories
    op.drop_constraint('category_types_parent_id_fkey', 'category_types', type_='foreignkey')
    op.drop_constraint('sub_categories_type_id_fkey', 'sub_categories', type_='foreignkey')
    op.drop_constraint('sub_categories_gender_id_fkey', 'sub_categories', type_='foreignkey')
    
    # Step 2: Create temporary integer columns for all category tables
    # Main categories
    op.add_column('main_categories', sa.Column('new_id', sa.Integer(), nullable=True))
    op.execute("""
        CREATE SEQUENCE main_categories_new_id_seq;
        ALTER TABLE main_categories ALTER COLUMN new_id SET DEFAULT nextval('main_categories_new_id_seq');
    """)
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM main_categories
        )
        UPDATE main_categories
        SET new_id = numbered.rn
        FROM numbered
        WHERE main_categories.id = numbered.id;
    """)
    op.alter_column('main_categories', 'new_id', nullable=False)
    op.execute("SELECT setval('main_categories_new_id_seq', (SELECT MAX(new_id) FROM main_categories));")
    
    # Genders
    op.add_column('genders', sa.Column('new_id', sa.Integer(), nullable=True))
    op.execute("""
        CREATE SEQUENCE genders_new_id_seq;
        ALTER TABLE genders ALTER COLUMN new_id SET DEFAULT nextval('genders_new_id_seq');
    """)
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM genders
        )
        UPDATE genders
        SET new_id = numbered.rn
        FROM numbered
        WHERE genders.id = numbered.id;
    """)
    op.alter_column('genders', 'new_id', nullable=False)
    op.execute("SELECT setval('genders_new_id_seq', (SELECT MAX(new_id) FROM genders));")
    
    # Category types
    op.add_column('category_types', sa.Column('new_id', sa.Integer(), nullable=True))
    op.add_column('category_types', sa.Column('new_parent_id', sa.Integer(), nullable=True))
    op.execute("""
        CREATE SEQUENCE category_types_new_id_seq;
        ALTER TABLE category_types ALTER COLUMN new_id SET DEFAULT nextval('category_types_new_id_seq');
    """)
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM category_types
        )
        UPDATE category_types
        SET new_id = numbered.rn
        FROM numbered
        WHERE category_types.id = numbered.id;
    """)
    op.execute("""
        UPDATE category_types
        SET new_parent_id = main_categories.new_id
        FROM main_categories
        WHERE category_types.parent_id = main_categories.id;
    """)
    op.alter_column('category_types', 'new_id', nullable=False)
    op.alter_column('category_types', 'new_parent_id', nullable=False)
    op.execute("SELECT setval('category_types_new_id_seq', (SELECT MAX(new_id) FROM category_types));")
    
    # Sub categories
    op.add_column('sub_categories', sa.Column('new_id', sa.Integer(), nullable=True))
    op.add_column('sub_categories', sa.Column('new_type_id', sa.Integer(), nullable=True))
    op.add_column('sub_categories', sa.Column('new_gender_id', sa.Integer(), nullable=True))
    op.execute("""
        CREATE SEQUENCE sub_categories_new_id_seq;
        ALTER TABLE sub_categories ALTER COLUMN new_id SET DEFAULT nextval('sub_categories_new_id_seq');
    """)
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM sub_categories
        )
        UPDATE sub_categories
        SET new_id = numbered.rn
        FROM numbered
        WHERE sub_categories.id = numbered.id;
    """)
    op.execute("""
        UPDATE sub_categories
        SET new_type_id = category_types.new_id
        FROM category_types
        WHERE sub_categories.type_id = category_types.id;
    """)
    op.execute("""
        UPDATE sub_categories
        SET new_gender_id = genders.new_id
        FROM genders
        WHERE sub_categories.gender_id = genders.id;
    """)
    op.alter_column('sub_categories', 'new_id', nullable=False)
    op.alter_column('sub_categories', 'new_type_id', nullable=False)
    op.execute("SELECT setval('sub_categories_new_id_seq', (SELECT MAX(new_id) FROM sub_categories));")
    
    # Brands
    op.add_column('brands', sa.Column('new_id', sa.Integer(), nullable=True))
    op.execute("""
        CREATE SEQUENCE brands_new_id_seq;
        ALTER TABLE brands ALTER COLUMN new_id SET DEFAULT nextval('brands_new_id_seq');
    """)
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM brands
        )
        UPDATE brands
        SET new_id = numbered.rn
        FROM numbered
        WHERE brands.id = numbered.id;
    """)
    op.alter_column('brands', 'new_id', nullable=False)
    op.execute("SELECT setval('brands_new_id_seq', (SELECT MAX(new_id) FROM brands));")
    
    # Step 3: Update products table with new integer IDs
    op.add_column('products', sa.Column('new_category_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('new_gender_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('new_product_type_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('new_sub_category_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('new_designer_id', sa.Integer(), nullable=True))
    
    op.execute("""
        UPDATE products
        SET new_category_id = main_categories.new_id
        FROM main_categories
        WHERE products.category_id = main_categories.id;
    """)
    op.execute("""
        UPDATE products
        SET new_gender_id = genders.new_id
        FROM genders
        WHERE products.gender_id = genders.id;
    """)
    op.execute("""
        UPDATE products
        SET new_product_type_id = category_types.new_id
        FROM category_types
        WHERE products.product_type_id = category_types.id;
    """)
    op.execute("""
        UPDATE products
        SET new_sub_category_id = sub_categories.new_id
        FROM sub_categories
        WHERE products.sub_category_id = sub_categories.id;
    """)
    op.execute("""
        UPDATE products
        SET new_designer_id = brands.new_id
        FROM brands
        WHERE products.designer_id = brands.id;
    """)
    
    # Step 4: Drop old UUID columns and rename new columns using raw SQL
    # Main categories
    op.execute("ALTER TABLE main_categories DROP COLUMN id CASCADE")
    op.execute("ALTER TABLE main_categories RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE main_categories ADD PRIMARY KEY (id)")
    op.execute("ALTER SEQUENCE main_categories_new_id_seq RENAME TO main_categories_id_seq")
    op.execute("ALTER TABLE main_categories ALTER COLUMN id SET DEFAULT nextval('main_categories_id_seq')")
    
    # Genders
    op.execute("ALTER TABLE genders DROP COLUMN id CASCADE")
    op.execute("ALTER TABLE genders RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE genders ADD PRIMARY KEY (id)")
    op.execute("ALTER SEQUENCE genders_new_id_seq RENAME TO genders_id_seq")
    op.execute("ALTER TABLE genders ALTER COLUMN id SET DEFAULT nextval('genders_id_seq')")
    
    # Category types
    op.execute("ALTER TABLE category_types DROP COLUMN id CASCADE")
    op.execute("ALTER TABLE category_types DROP COLUMN parent_id CASCADE")
    op.execute("ALTER TABLE category_types RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE category_types RENAME COLUMN new_parent_id TO parent_id")
    op.execute("ALTER TABLE category_types ADD PRIMARY KEY (id)")
    op.execute("ALTER SEQUENCE category_types_new_id_seq RENAME TO category_types_id_seq")
    op.execute("ALTER TABLE category_types ALTER COLUMN id SET DEFAULT nextval('category_types_id_seq')")
    
    # Sub categories
    op.execute("ALTER TABLE sub_categories DROP COLUMN id CASCADE")
    op.execute("ALTER TABLE sub_categories DROP COLUMN type_id CASCADE")
    op.execute("ALTER TABLE sub_categories DROP COLUMN gender_id CASCADE")
    op.execute("ALTER TABLE sub_categories RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE sub_categories RENAME COLUMN new_type_id TO type_id")
    op.execute("ALTER TABLE sub_categories RENAME COLUMN new_gender_id TO gender_id")
    op.execute("ALTER TABLE sub_categories ADD PRIMARY KEY (id)")
    op.execute("ALTER SEQUENCE sub_categories_new_id_seq RENAME TO sub_categories_id_seq")
    op.execute("ALTER TABLE sub_categories ALTER COLUMN id SET DEFAULT nextval('sub_categories_id_seq')")
    
    # Brands
    op.execute("ALTER TABLE brands DROP COLUMN id CASCADE")
    op.execute("ALTER TABLE brands RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE brands ADD PRIMARY KEY (id)")
    op.execute("ALTER SEQUENCE brands_new_id_seq RENAME TO brands_id_seq")
    op.execute("ALTER TABLE brands ALTER COLUMN id SET DEFAULT nextval('brands_id_seq')")
    
    # Products
    op.execute("ALTER TABLE products DROP COLUMN category_id")
    op.execute("ALTER TABLE products DROP COLUMN gender_id")
    op.execute("ALTER TABLE products DROP COLUMN product_type_id")
    op.execute("ALTER TABLE products DROP COLUMN sub_category_id")
    op.execute("ALTER TABLE products DROP COLUMN designer_id")
    op.execute("ALTER TABLE products RENAME COLUMN new_category_id TO category_id")
    op.execute("ALTER TABLE products RENAME COLUMN new_gender_id TO gender_id")
    op.execute("ALTER TABLE products RENAME COLUMN new_product_type_id TO product_type_id")
    op.execute("ALTER TABLE products RENAME COLUMN new_sub_category_id TO sub_category_id")
    op.execute("ALTER TABLE products RENAME COLUMN new_designer_id TO designer_id")
    
    # Step 5: Recreate foreign key constraints
    op.create_foreign_key('fk_products_category_id', 'products', 'main_categories', ['category_id'], ['id'])
    op.create_foreign_key('fk_products_gender_id', 'products', 'genders', ['gender_id'], ['id'])
    op.create_foreign_key('fk_products_product_type_id', 'products', 'category_types', ['product_type_id'], ['id'])
    op.create_foreign_key('fk_products_sub_category_id', 'products', 'sub_categories', ['sub_category_id'], ['id'])
    op.create_foreign_key('fk_products_designer_id', 'products', 'brands', ['designer_id'], ['id'])
    op.create_foreign_key('category_types_parent_id_fkey', 'category_types', 'main_categories', ['parent_id'], ['id'])
    op.create_foreign_key('sub_categories_type_id_fkey', 'sub_categories', 'category_types', ['type_id'], ['id'])
    op.create_foreign_key('sub_categories_gender_id_fkey', 'sub_categories', 'genders', ['gender_id'], ['id'])


def downgrade() -> None:
    # This is a complex downgrade - would need to restore UUIDs
    # For now, we'll just note that downgrade is not fully supported
    # In production, you'd want to backup UUIDs before migration
    raise NotImplementedError("Downgrade from integer IDs to UUIDs is not supported. Restore from backup if needed.")

