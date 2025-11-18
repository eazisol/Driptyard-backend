"""convert_users_to_integer_ids

Revision ID: n3o4p5q6r7s8
Revises: m2n3o4p5q6r7
Create Date: 2025-01-20 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'n3o4p5q6r7s8'
down_revision: Union[str, None] = 'm2n3o4p5q6r7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create temporary integer column for users.id
    op.execute("ALTER TABLE users ADD COLUMN new_id INTEGER")
    
    # Step 2: Populate new_id with sequential integers based on created_at
    op.execute("""
        WITH numbered_users AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as row_num
            FROM users
        )
        UPDATE users
        SET new_id = numbered_users.row_num
        FROM numbered_users
        WHERE users.id = numbered_users.id
    """)
    
    # Step 3: Create sequence for users
    op.execute("CREATE SEQUENCE users_new_id_seq")
    op.execute("ALTER SEQUENCE users_new_id_seq OWNED BY users.new_id")
    op.execute("ALTER TABLE users ALTER COLUMN new_id SET DEFAULT nextval('users_new_id_seq')")
    op.execute("ALTER TABLE users ALTER COLUMN new_id SET NOT NULL")
    
    # Step 4: Create temporary integer columns for foreign keys referencing users
    op.execute("ALTER TABLE products ADD COLUMN new_owner_id INTEGER")
    
    # Check if orders table exists before modifying it
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                ALTER TABLE orders ADD COLUMN new_buyer_id INTEGER;
                ALTER TABLE orders ADD COLUMN new_seller_id INTEGER;
            END IF;
        END $$;
    """)
    
    # Step 5: Map products.owner_id from UUID to integer
    op.execute("""
        UPDATE products
        SET new_owner_id = users.new_id
        FROM users
        WHERE products.owner_id = users.id
    """)
    
    # Step 5b: Map orders.buyer_id and seller_id from UUID to integer (if orders table exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) THEN
                UPDATE orders
                SET new_buyer_id = users.new_id
                FROM users
                WHERE orders.buyer_id::uuid = users.id;
                
                UPDATE orders
                SET new_seller_id = users.new_id
                FROM users
                WHERE orders.seller_id::uuid = users.id;
            END IF;
        END $$;
    """)
    
    # Step 6: Drop foreign key constraints on products.owner_id
    op.execute("""
        DO $$ 
        DECLARE
            constraint_name TEXT;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint 
            WHERE conname LIKE '%owner_id%'
            AND conrelid = 'products'::regclass
            LIMIT 1;
            
            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE products DROP CONSTRAINT %I', constraint_name);
            END IF;
        END $$;
    """)
    
    # Step 7: Drop indexes on products.owner_id
    op.execute("""
        DO $$ 
        DECLARE
            index_name TEXT;
        BEGIN
            SELECT indexname INTO index_name
            FROM pg_indexes 
            WHERE tablename = 'products' 
            AND indexname LIKE '%owner_id%'
            LIMIT 1;
            
            IF index_name IS NOT NULL THEN
                EXECUTE format('DROP INDEX %I', index_name);
            END IF;
        END $$;
    """)
    
    # Step 8: Drop old UUID columns (but keep orders columns for now - they'll be handled in orders migration)
    op.execute("ALTER TABLE products DROP COLUMN owner_id CASCADE")
    op.execute("ALTER TABLE users DROP COLUMN id CASCADE")
    
    # Step 9: Rename new columns
    op.execute("ALTER TABLE users RENAME COLUMN new_id TO id")
    op.execute("ALTER TABLE products RENAME COLUMN new_owner_id TO owner_id")
    
    # Step 10: Recreate primary key and sequence for users
    op.execute("ALTER TABLE users ADD PRIMARY KEY (id)")
    op.execute("ALTER SEQUENCE users_new_id_seq RENAME TO users_id_seq")
    op.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq')")
    
    # Step 11: Recreate index and foreign key for products.owner_id
    op.create_index(op.f('ix_products_owner_id'), 'products', ['owner_id'], unique=False)
    op.create_foreign_key('fk_products_owner_id', 'products', 'users', ['owner_id'], ['id'])
    
    # Note: orders.buyer_id and seller_id will be handled in the orders migration
    
    # Step 12: Update other user-related tables (email_verifications, registration_data, password_reset_tokens)
    # These don't have foreign keys to users, so we just need to convert their IDs
    for table in ['email_verifications', 'registration_data', 'password_reset_tokens']:
        op.execute(f"ALTER TABLE {table} ADD COLUMN new_id INTEGER")
        op.execute(f"""
            WITH numbered_rows AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as row_num
                FROM {table}
            )
            UPDATE {table}
            SET new_id = numbered_rows.row_num
            FROM numbered_rows
            WHERE {table}.id = numbered_rows.id
        """)
        op.execute(f"CREATE SEQUENCE {table}_new_id_seq")
        op.execute(f"ALTER SEQUENCE {table}_new_id_seq OWNED BY {table}.new_id")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN new_id SET DEFAULT nextval('{table}_new_id_seq')")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN new_id SET NOT NULL")
        op.execute(f"ALTER TABLE {table} DROP COLUMN id CASCADE")
        op.execute(f"ALTER TABLE {table} RENAME COLUMN new_id TO id")
        op.execute(f"ALTER TABLE {table} ADD PRIMARY KEY (id)")
        op.execute(f"ALTER SEQUENCE {table}_new_id_seq RENAME TO {table}_id_seq")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{table}_id_seq')")


def downgrade() -> None:
    # Reverse the process - convert back to UUIDs
    # Note: This is complex and may lose data if UUIDs weren't preserved
    # For now, we'll just raise an error indicating manual intervention is needed
    raise NotImplementedError("Downgrade from integer IDs to UUIDs requires manual data migration")


