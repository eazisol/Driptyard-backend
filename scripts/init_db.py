"""
Database initialization script.

This script initializes the database with tables and optionally seeds
it with initial data for development and testing.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, create_tables
from app.core.config import settings


def init_database():
    """
    Initialize the database by creating all tables.
    """
    print("Initializing database...")
    
    try:
        # Create all tables
        create_tables()
        print("✅ Database tables created successfully")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)


def seed_database():
    """
    Seed the database with initial data.
    """
    print("Seeding database with initial data...")
    
    # TODO: Implement database seeding
    # This will be implemented when models are ready
    # Examples of what to seed:
    # - Admin user
    # - Sample categories
    # - Sample products (if needed)
    
    print("✅ Database seeded successfully")


def reset_database():
    """
    Reset the database by dropping and recreating all tables.
    """
    print("Resetting database...")
    
    try:
        from app.core.database import drop_tables
        drop_tables()
        print("✅ Database tables dropped")
        
        create_tables()
        print("✅ Database tables recreated")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)


def check_database_connection():
    """
    Check if database connection is working.
    """
    print("Checking database connection...")
    
    try:
        # Test database connection
        with SessionLocal() as session:
            session.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def main():
    """
    Main function to run database initialization.
    """
    print("🚀 Starting database initialization...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Check database connection
    if not check_database_connection():
        print("❌ Cannot connect to database. Please check your DATABASE_URL in .env file")
        sys.exit(1)
    
    # Initialize database
    init_database()
    
    # Ask if user wants to seed database
    seed_choice = input("Do you want to seed the database with initial data? (y/N): ").lower()
    if seed_choice in ['y', 'yes']:
        seed_database()
    
    print("🎉 Database initialization completed successfully!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset database (drop and recreate all tables)"
    )
    parser.add_argument(
        "--seed", 
        action="store_true", 
        help="Seed database with initial data"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check database connection only"
    )
    
    args = parser.parse_args()
    
    if args.check:
        check_database_connection()
    elif args.reset:
        reset_database()
    elif args.seed:
        seed_database()
    else:
        main()
