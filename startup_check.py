#!/usr/bin/env python3
"""
Startup diagnostic to verify database connection.
This runs before starting the FastAPI server.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import settings, engine
from sqlalchemy import text

print("\n" + "=" * 70)
print("🚀 DRIPTYARD BACKEND STARTUP")
print("=" * 70)

# Show DATABASE_URL
db_url = settings.DATABASE_URL
print(f"\n📋 Configuration:")
print(f"   DATABASE_URL: {db_url[:80]}...")

# Determine database type
if "localhost" in db_url or "127.0.0.1" in db_url:
    print(f"\n⚠️  WARNING: Using LOCALHOST database!")
    print(f"   This is NOT your production AWS RDS database.")
    print(f"   If you want to use AWS RDS, update your .env file.")
elif "rds.amazonaws.com" in db_url:
    print(f"\n✅ Using AWS RDS database")
else:
    print(f"\n📊 Using remote database")

# Test connection
print(f"\n🔌 Testing database connection...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), inet_server_addr(), inet_server_port();"))
        db_info = result.fetchone()
        
        print(f"   ✅ Connected successfully!")
        print(f"   Database: {db_info[0]}")
        print(f"   Host: {db_info[1] or 'localhost'}")
        print(f"   Port: {db_info[2] or 'N/A'}")
        
        # Show table counts
        result = conn.execute(text("SELECT COUNT(*) FROM registration_data;"))
        reg_count = result.scalar()
        result = conn.execute(text("SELECT COUNT(*) FROM users;"))
        user_count = result.scalar()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Pending registrations: {reg_count}")
        print(f"   Verified users: {user_count}")
        
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ Startup check complete! Starting FastAPI server...")
print("=" * 70 + "\n")

