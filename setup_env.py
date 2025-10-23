#!/usr/bin/env python3
"""
Simple environment setup script.
Run this to create a .env file with default values.
"""

import os

def create_env_file():
    """Create .env file with default configuration."""
    
    env_content = """# Database Configuration
DATABASE_URL="postgresql://postgres:Pakistani%401@localhost:5433/Driptyard" 

# Security Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production-make-it-very-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
PROJECT_NAME=Driptyard Backend
VERSION=1.0.0
API_V1_STR=/api/v1

# CORS Configuration
ALLOWED_HOSTS=["*"]

# Email Configuration (for future use)
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=bilalsajidali@gmail.com
SMTP_PASSWORD=exnh nfie iytn jesd
EMAIL_FROM_NAME=Driptyard
EMAIL_FROM_ADDRESS=bilalsajidali@gmail.com
VERIFICATION_CODE_EXPIRY_MINUTES=15

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB in bytes
UPLOAD_DIR=static/uploads

# Redis Configuration (for future caching/sessions)
REDIS_URL=redis://localhost:6379/0
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(".env file created successfully!")
    print("Please update the DATABASE_URL and SECRET_KEY with your actual values.")

if __name__ == "__main__":
    create_env_file()
