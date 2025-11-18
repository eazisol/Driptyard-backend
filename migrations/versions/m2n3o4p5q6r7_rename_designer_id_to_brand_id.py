"""rename_designer_id_to_brand_id

Revision ID: m2n3o4p5q6r7
Revises: l1m2n3o4p5q6
Create Date: 2025-01-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'm2n3o4p5q6r7'
down_revision: Union[str, None] = 'l1m2n3o4p5q6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the foreign key constraint first using raw SQL (handles if it doesn't exist)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'fk_products_designer_id'
            ) THEN
                ALTER TABLE products DROP CONSTRAINT fk_products_designer_id;
            END IF;
        END $$;
    """)
    
    # Drop the index on designer_id if it exists using raw SQL
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'products' 
                AND indexname = 'ix_products_designer_id'
            ) THEN
                DROP INDEX ix_products_designer_id;
            END IF;
        END $$;
    """)
    
    # Rename the column
    op.execute("ALTER TABLE products RENAME COLUMN designer_id TO brand_id")
    
    # Recreate the index with new name
    op.create_index(op.f('ix_products_brand_id'), 'products', ['brand_id'], unique=False)
    
    # Recreate the foreign key constraint with new column name
    op.create_foreign_key('fk_products_brand_id', 'products', 'brands', ['brand_id'], ['id'])


def downgrade() -> None:
    # Drop the foreign key constraint
    op.drop_constraint('fk_products_brand_id', 'products', type_='foreignkey')
    
    # Drop the index
    op.drop_index('ix_products_brand_id', table_name='products')
    
    # Rename back to designer_id
    op.execute("ALTER TABLE products RENAME COLUMN brand_id TO designer_id")
    
    # Recreate the index
    op.create_index(op.f('ix_products_designer_id'), 'products', ['designer_id'], unique=False)
    
    # Recreate the foreign key constraint
    op.create_foreign_key('fk_products_designer_id', 'products', 'brands', ['designer_id'], ['id'])

