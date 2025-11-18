"""convert_orders_to_integer_ids

Revision ID: p5q6r7s8t9u0
Revises: o4p5q6r7s8t9
Create Date: 2025-01-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p5q6r7s8t9u0'
down_revision: Union[str, None] = 'o4p5q6r7s8t9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All operations wrapped in table existence check
    op.execute("""
        DO $$ 
        DECLARE
            constraint_name TEXT;
            index_name TEXT;
        BEGIN
            -- Check if orders table exists first
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                RETURN;
            END IF;
            
            -- Note: new_buyer_id and new_seller_id were already created in the users migration
            -- Step 1: Drop foreign key constraints on orders.buyer_id and seller_id
            SELECT conname INTO constraint_name
            FROM pg_constraint 
            WHERE conname LIKE '%buyer_id%'
            AND conrelid = 'orders'::regclass
            LIMIT 1;
            
            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE orders DROP CONSTRAINT %I', constraint_name);
            END IF;
            
            SELECT conname INTO constraint_name
            FROM pg_constraint 
            WHERE conname LIKE '%seller_id%'
            AND conrelid = 'orders'::regclass
            LIMIT 1;
            
            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE orders DROP CONSTRAINT %I', constraint_name);
            END IF;
            
            -- Step 2: Drop indexes on orders.buyer_id and seller_id
            SELECT indexname INTO index_name
            FROM pg_indexes 
            WHERE tablename = 'orders' 
            AND indexname LIKE '%buyer_id%'
            LIMIT 1;
            
            IF index_name IS NOT NULL THEN
                EXECUTE format('DROP INDEX %I', index_name);
            END IF;
            
            SELECT indexname INTO index_name
            FROM pg_indexes 
            WHERE tablename = 'orders' 
            AND indexname LIKE '%seller_id%'
            LIMIT 1;
            
            IF index_name IS NOT NULL THEN
                EXECUTE format('DROP INDEX %I', index_name);
            END IF;
            
            -- Step 3: Create temporary integer column for orders.id
            ALTER TABLE orders ADD COLUMN new_id INTEGER;
            
            -- Step 4: Populate new_id with sequential integers based on created_at
            WITH numbered_orders AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as row_num
                FROM orders
            )
            UPDATE orders
            SET new_id = numbered_orders.row_num
            FROM numbered_orders
            WHERE orders.id = numbered_orders.id;
            
            -- Step 5: Create sequence for orders
            CREATE SEQUENCE orders_new_id_seq;
            ALTER SEQUENCE orders_new_id_seq OWNED BY orders.new_id;
            ALTER TABLE orders ALTER COLUMN new_id SET DEFAULT nextval('orders_new_id_seq');
            ALTER TABLE orders ALTER COLUMN new_id SET NOT NULL;
    
            
            -- Step 6: Drop old UUID columns
            ALTER TABLE orders DROP COLUMN buyer_id CASCADE;
            ALTER TABLE orders DROP COLUMN seller_id CASCADE;
            ALTER TABLE orders DROP COLUMN id CASCADE;
            
            -- Step 7: Rename new columns
            ALTER TABLE orders RENAME COLUMN new_id TO id;
            ALTER TABLE orders RENAME COLUMN new_buyer_id TO buyer_id;
            ALTER TABLE orders RENAME COLUMN new_seller_id TO seller_id;
            
            -- Step 8: Recreate primary key and sequence for orders
            ALTER TABLE orders ADD PRIMARY KEY (id);
            ALTER SEQUENCE orders_new_id_seq RENAME TO orders_id_seq;
            ALTER TABLE orders ALTER COLUMN id SET DEFAULT nextval('orders_id_seq');
            
            -- Step 9: Recreate indexes and foreign keys
            CREATE INDEX IF NOT EXISTS ix_orders_buyer_id ON orders (buyer_id);
            CREATE INDEX IF NOT EXISTS ix_orders_seller_id ON orders (seller_id);
            ALTER TABLE orders ADD CONSTRAINT fk_orders_buyer_id 
                FOREIGN KEY (buyer_id) REFERENCES users(id);
            ALTER TABLE orders ADD CONSTRAINT fk_orders_seller_id 
                FOREIGN KEY (seller_id) REFERENCES users(id);
        END $$;
    """)


def downgrade() -> None:
    # Reverse the process - convert back to UUIDs
    raise NotImplementedError("Downgrade from integer IDs to UUIDs requires manual data migration")


