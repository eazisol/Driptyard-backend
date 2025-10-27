#!/usr/bin/env python3
"""Show all registration data from AWS RDS."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import settings, engine
from sqlalchemy import text
from datetime import datetime

print("\n" + "=" * 70)
print("AWS RDS REGISTRATION DATA")
print("=" * 70)

try:
    with engine.connect() as conn:
        # Verify connection
        result = conn.execute(text("SELECT inet_server_addr();"))
        host = result.scalar()
        print(f"\n✅ Connected to: {host}")
        
        # Get all registration data
        result = conn.execute(text("""
            SELECT id, email, username, phone, country_code, created_at 
            FROM registration_data 
            ORDER BY created_at DESC;
        """))
        
        registrations = result.fetchall()
        
        if registrations:
            print(f"\n📊 Total Pending Registrations: {len(registrations)}\n")
            for reg in registrations:
                print(f"  ID: {reg[0]}")
                print(f"  📧 Email: {reg[1]}")
                print(f"  👤 Username: {reg[2]}")
                print(f"  📞 Phone: {reg[3]}")
                print(f"  🌍 Country: {reg[4]}")
                print(f"  📅 Created: {reg[5]}")
                print(f"  {'-' * 66}")
        else:
            print("\n📭 No pending registrations found")
        
        # Get verified users
        result = conn.execute(text("""
            SELECT COUNT(*) FROM users;
        """))
        user_count = result.scalar()
        print(f"\n✅ Verified Users: {user_count}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)

