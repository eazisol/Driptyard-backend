#!/usr/bin/env python3
"""
Fix sequence synchronization for tables converted from UUID to Integer IDs.

This script fixes the issue where PostgreSQL sequences are out of sync with
actual data after migration, causing "duplicate key value violates unique constraint" errors.

Usage:
    python scripts/fix_sequence_sync.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.database import settings

def fix_sequence_sync():
    """Fix sequence synchronization for converted tables."""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    tables_to_fix = [
        'email_verifications',
        'registration_data',
        'password_reset_tokens',
        'users',
        'products',
        'orders'
    ]
    
    print("Fixing sequence synchronization...")
    print("=" * 60)
    
    with engine.begin() as conn:
        for table in tables_to_fix:
            sequence_name = f"{table}_id_seq"
            
            # Check if sequence exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_sequences 
                    WHERE sequencename = :sequence_name
                )
            """)
            
            result = conn.execute(check_query, {"sequence_name": sequence_name})
            sequence_exists = result.scalar()
            
            if not sequence_exists:
                print(f"[WARNING] Sequence '{sequence_name}' does not exist for table '{table}' - skipping")
                continue
            
            # Get current max ID
            max_id_query = text(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
            result = conn.execute(max_id_query)
            max_id = result.scalar()
            
            # Get current sequence value
            seq_value_query = text(f"SELECT last_value FROM {sequence_name}")
            result = conn.execute(seq_value_query)
            current_seq_value = result.scalar()
            
            # Set sequence to max_id + 1
            new_seq_value = max_id + 1
            setval_query = text(f"SELECT setval(:sequence_name, :new_value, false)")
            conn.execute(setval_query, {
                "sequence_name": sequence_name,
                "new_value": new_seq_value
            })
            
            if new_seq_value > current_seq_value:
                print(f"[FIXED] '{table}': Sequence updated from {current_seq_value} to {new_seq_value} (max_id={max_id})")
            else:
                print(f"[OK] '{table}': Sequence already correct at {new_seq_value} (max_id={max_id})")
    
    print("=" * 60)
    print("[SUCCESS] Sequence synchronization complete!")

if __name__ == "__main__":
    try:
        fix_sequence_sync()
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

