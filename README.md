# Driptyard Backend - Simple FastAPI Project

A beginner-friendly FastAPI backend for the Driptyard C2C e-commerce platform.

## 🚀 Quick Start (For Beginners)

### Option 1: Automatic Setup (Recommended)
```bash
# 1. Clone and navigate to the project
git clone <repository-url>
cd Driptyard_Backend

# 2. Run the automatic setup script
python start.py
```

### Option 2: Manual Setup
```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
python setup_env.py

# 4. Update .env file with your database details

# 5. Run migrations
alembic upgrade head

# 6. Start the server
uvicorn app.main:app --reload
```

## 📚 What You'll Learn

This project demonstrates:
- ✅ **FastAPI basics** - Modern Python web framework
- ✅ **Authentication** - JWT tokens, password hashing
- ✅ **Database** - SQLAlchemy ORM, PostgreSQL
- ✅ **API Design** - RESTful endpoints, request/response models
- ✅ **Security** - Password validation, CORS, input validation

## 🛠️ Tech Stack

- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Database
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **JWT** - Authentication tokens

## 📖 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🔐 Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/register` | Register new user |
| POST | `/api/v1/login` | Login user |
| POST | `/api/v1/logout` | Logout user |
| GET | `/api/v1/me` | Get current user profile |
| POST | `/api/v1/refresh` | Refresh access token |
| POST | `/api/v1/verify-email` | Verify email with code |
| POST | `/api/v1/resend-verification` | Resend verification code |

## 🗄️ Database Setup

1. **Install PostgreSQL** on your system
2. **Create a database** named `Driptyard`
3. **Update DATABASE_URL** in `.env` file:
   ```
   DATABASE_URL="postgres://username:password@localhost:5432/Driptyard"
   ```
4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

## 📁 Project Structure

```
Driptyard_Backend/
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── database.py      # Database configuration
│   ├── models.py        # Database models (User, etc.)
│   ├── schemas.py       # Request/response models
│   ├── auth.py          # Authentication logic
│   └── routes/
│       └── auth.py      # Authentication endpoints
├── migrations/          # Database migration files
├── scripts/            # Database utility scripts
├── requirements.txt     # Python dependencies
├── start.py            # Quick start script
└── setup_env.py        # Environment setup script
```

## 🔧 Configuration

The `.env` file contains all configuration:

```env
# Database
DATABASE_URL="postgres://user:pass@localhost:5432/Driptyard"

# Security
SECRET_KEY="your-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (for verification)
SMTP_HOST="smtp.gmail.com"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
```

## 🧪 Testing the API

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123",
    "username": "testuser",
    "phone": "+1234567890",
    "country_code": "US"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

### 3. Get User Profile (with token)
```bash
curl -X GET "http://localhost:8000/api/v1/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection Error**
   - Check if PostgreSQL is running
   - Verify DATABASE_URL in .env file
   - Ensure database exists

2. **Import Errors**
   - Make sure virtual environment is activated
   - Run `pip install -r requirements.txt`

3. **Migration Errors**
   - Check database connection
   - Run `alembic upgrade head`

## 📚 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/14/tutorial/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.