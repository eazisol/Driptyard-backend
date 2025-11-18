"""rename_parent_id_to_main_category_id

Revision ID: l1m2n3o4p5q6
Revises: 569e34d7d4af
Create Date: 2025-01-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'l1m2n3o4p5q6'
down_revision: Union[str, None] = '569e34d7d4af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the foreign key constraint first using raw SQL (handles if it doesn't exist)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'category_types_parent_id_fkey'
            ) THEN
                ALTER TABLE category_types DROP CONSTRAINT category_types_parent_id_fkey;
            END IF;
        END $$;
    """)
    
    # Drop the index on parent_id if it exists using raw SQL
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'category_types' 
                AND indexname = 'ix_category_types_parent_id'
            ) THEN
                DROP INDEX ix_category_types_parent_id;
            END IF;
        END $$;
    """)
    
    # Rename the column
    op.execute("ALTER TABLE category_types RENAME COLUMN parent_id TO main_category_id")
    
    # Recreate the index with new name
    op.create_index(op.f('ix_category_types_main_category_id'), 'category_types', ['main_category_id'], unique=False)
    
    # Recreate the foreign key constraint with new column name
    op.create_foreign_key('category_types_main_category_id_fkey', 'category_types', 'main_categories', ['main_category_id'], ['id'])


def downgrade() -> None:
    # Drop the foreign key constraint
    op.drop_constraint('category_types_main_category_id_fkey', 'category_types', type_='foreignkey')
    
    # Drop the index
    op.drop_index('ix_category_types_main_category_id', table_name='category_types')
    
    # Rename back to parent_id
    op.execute("ALTER TABLE category_types RENAME COLUMN main_category_id TO parent_id")
    
    # Recreate the index
    op.create_index(op.f('ix_category_types_parent_id'), 'category_types', ['parent_id'], unique=False)
    
    # Recreate the foreign key constraint
    op.create_foreign_key('category_types_parent_id_fkey', 'category_types', 'main_categories', ['parent_id'], ['id'])

