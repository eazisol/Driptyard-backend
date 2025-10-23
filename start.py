#!/usr/bin/env python3
"""
Simple startup script for the FastAPI application.
This script helps beginners get started quickly.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_virtual_environment():
    """Check if virtual environment is activated."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Virtual environment is activated")
        return True
    else:
        print("WARNING: Virtual environment not detected")
        print("Consider creating a virtual environment:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   source venv/bin/activate  # Linux/Mac")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Setup environment file."""
    if not os.path.exists('.env'):
        print("Creating .env file...")
        try:
            subprocess.run([sys.executable, "setup_env.py"], check=True)
        except subprocess.CalledProcessError:
            print("Failed to create .env file")
            sys.exit(1)
    else:
        print(".env file already exists")

def check_database_connection():
    """Check database connection."""
    print("Checking database connection...")
    try:
        from app.database import settings
        print(f"Database URL: {settings.DATABASE_URL}")
        print("Database configuration loaded")
    except Exception as e:
        print(f"Database configuration error: {e}")
        print("Please check your DATABASE_URL in .env file")
        return False
    return True

def run_migrations():
    """Run database migrations."""
    print("Running database migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Database migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e}")
        print("Make sure your database is running and accessible")
        return False
    except FileNotFoundError:
        print("Alembic not found. Make sure it's installed.")
        return False
    return True

def start_server():
    """Start the FastAPI server."""
    print("Starting FastAPI server...")
    print("API Documentation will be available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Failed to start server: {e}")

def main():
    """Main startup function."""
    print("Welcome to Driptyard Backend!")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Check virtual environment
    venv_active = check_virtual_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Setup environment
    setup_environment()
    
    # Check database connection
    if not check_database_connection():
        print("\nPlease fix database configuration and try again")
        return
    
    # Run migrations
    if not run_migrations():
        print("\nPlease fix database issues and try again")
        return
    
    print("\nSetup completed successfully!")
    print("=" * 50)
    
    # Ask if user wants to start server
    start_choice = input("Do you want to start the server now? (Y/n): ").lower()
    if start_choice in ['', 'y', 'yes']:
        start_server()
    else:
        print("To start the server manually, run: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()