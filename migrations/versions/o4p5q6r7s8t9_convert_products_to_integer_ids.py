"""convert_products_to_integer_ids

Revision ID: o4p5q6r7s8t9
Revises: n3o4p5q6r7s8
Create Date: 2025-01-20 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'o4p5q6r7s8t9'
down_revision: Union[str, None] = 'n3o4p5q6r7s8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create temporary integer column for products.id
    op.execute("ALTER TABLE products ADD COLUMN new_id INTEGER")
    
    # Step 2: Populate new_id with sequential integers based on created_at
    op.execute("""
        WITH numbered_products AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as row_num
            FROM products
        )
        UPDATE products
        SET new_id = numbered_products.row_num
        FROM numbered_products
        WHERE products.id = numbered_products.id
    """)
    
    # Step 3: Create sequence for products
    op.execute("CREATE SEQUENCE products_new_id_seq")
    op.execute("ALTER SEQUENCE products_new_id_seq OWNED BY products.new_id")
    op.execute("ALTER TABLE products ALTER COLUMN new_id SET DEFAULT nextval('products_new_id_seq')")
    op.execute("ALTER TABLE products ALTER COLUMN new_id SET NOT NULL")
    
    # Step 4: Create temporary integer column for orders.product_id (if orders table exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                ALTER TABLE orders ADD COLUMN new_product_id INTEGER;
            END IF;
        END $$;
    """)
    
    # Step 5: Map orders.product_id from UUID to integer (if orders table exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                UPDATE orders
                SET new_product_id = products.new_id
                FROM products
                WHERE orders.product_id = products.id;
            END IF;
        END $$;
    """)
    
    # Step 6: Drop foreign key constraint on orders.product_id (if orders table exists)
    op.execute("""
        DO $$ 
        DECLARE
            constraint_name TEXT;
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                SELECT conname INTO constraint_name
                FROM pg_constraint 
                WHERE conname LIKE '%product_id%'
                AND conrelid = 'orders'::regclass
                LIMIT 1;
                
                IF constraint_name IS NOT NULL THEN
                    EXECUTE format('ALTER TABLE orders DROP CONSTRAINT %I', constraint_name);
                END IF;
            END IF;
        END $$;
    """)
    
    # Step 7: Drop index on orders.product_id (if orders table exists)
    op.execute("""
        DO $$ 
        DECLARE
            index_name TEXT;
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                SELECT indexname INTO index_name
                FROM pg_indexes 
                WHERE tablename = 'orders' 
                AND indexname LIKE '%product_id%'
                LIMIT 1;
                
                IF index_name IS NOT NULL THEN
                    EXECUTE format('DROP INDEX %I', index_name);
                END IF;
            END IF;
        END $$;
    """)
    
    # Step 8: Drop old UUID columns (if orders table exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                ALTER TABLE orders DROP COLUMN product_id CASCADE;
            END IF;
        END $$;
    """)
    op.execute("ALTER TABLE products DROP COLUMN id CASCADE")
    
    # Step 9: Rename new columns
    op.execute("ALTER TABLE products RENAME COLUMN new_id TO id")
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                ALTER TABLE orders RENAME COLUMN new_product_id TO product_id;
            END IF;
        END $$;
    """)
    
    # Step 10: Recreate primary key and sequence for products
    op.execute("ALTER TABLE products ADD PRIMARY KEY (id)")
    op.execute("ALTER SEQUENCE products_new_id_seq RENAME TO products_id_seq")
    op.execute("ALTER TABLE products ALTER COLUMN id SET DEFAULT nextval('products_id_seq')")
    
    # Step 11: Recreate index and foreign key for orders.product_id (if orders table exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_orders_product_id ON orders (product_id);
                ALTER TABLE orders ADD CONSTRAINT fk_orders_product_id 
                    FOREIGN KEY (product_id) REFERENCES products(id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Reverse the process - convert back to UUIDs
    raise NotImplementedError("Downgrade from integer IDs to UUIDs requires manual data migration")


