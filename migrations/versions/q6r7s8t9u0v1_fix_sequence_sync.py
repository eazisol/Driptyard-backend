"""fix_sequence_sync

Revision ID: q6r7s8t9u0v1
Revises: p5q6r7s8t9u0
Create Date: 2025-01-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'q6r7s8t9u0v1'
down_revision: Union[str, None] = 'p5q6r7s8t9u0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix sequence sync for tables converted from UUID to Integer.
    
    After converting tables from UUID to Integer IDs, the sequences
    need to be synchronized with the actual maximum ID values in the tables.
    This ensures new inserts won't violate primary key constraints.
    """
    
    # Fix sequences for all tables that were converted
    tables_to_fix = ['email_verifications', 'registration_data', 'password_reset_tokens', 'users']
    
    for table in tables_to_fix:
        sequence_name = f"{table}_id_seq"
        
        # Check if sequence exists before trying to fix it
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_sequences WHERE sequencename = '{sequence_name}'
                ) THEN
                    -- Set sequence to max(id) + 1, or 1 if table is empty
                    PERFORM setval(
                        '{sequence_name}',
                        COALESCE((SELECT MAX(id) FROM {table}), 0) + 1,
                        false
                    );
                END IF;
            END $$;
        """)


def downgrade() -> None:
    # No downgrade needed - this is just fixing sequence values
    pass

