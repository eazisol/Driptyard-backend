#!/usr/bin/env python3
"""Quick script to verify database connection and check registered users."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import settings, engine
from sqlalchemy import text

print("=" * 70)
print("DATABASE VERIFICATION")
print("=" * 70)

print(f"\n1. Database URL: {settings.DATABASE_URL[:50]}...")

try:
    with engine.connect() as conn:
        # Get database info
        result = conn.execute(text("SELECT current_database(), inet_server_addr(), inet_server_port();"))
        db_info = result.fetchone()
        
        print(f"2. Database: {db_info[0]}")
        print(f"3. Host: {db_info[1] or 'localhost'}")
        print(f"4. Port: {db_info[2] or 'N/A'}")
        
        # Check if it's AWS RDS
        if db_info[1] and "rds.amazonaws.com" not in settings.DATABASE_URL:
            if db_info[1] != "localhost" and not db_info[1].startswith("127."):
                print(f"\n✅ Connected to REMOTE database (likely AWS RDS)")
        elif "rds.amazonaws.com" in settings.DATABASE_URL:
            print(f"\n✅ Connected to AWS RDS database")
        else:
            print(f"\n⚠️  Connected to LOCALHOST database")
        
        # Count registration data
        result = conn.execute(text("SELECT COUNT(*) FROM registration_data;"))
        reg_count = result.scalar()
        print(f"\n5. Pending registrations: {reg_count}")
        
        # Count verified users
        result = conn.execute(text("SELECT COUNT(*) FROM users;"))
        user_count = result.scalar()
        print(f"6. Verified users: {user_count}")
        
        if reg_count > 0:
            print(f"\n📧 {reg_count} user(s) pending email verification")
            result = conn.execute(text("SELECT email FROM registration_data ORDER BY id DESC LIMIT 3;"))
            for row in result:
                print(f"   - {row[0]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)

