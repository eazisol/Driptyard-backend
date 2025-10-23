# Driptyard Backend

A FastAPI-based backend for a C2C (Consumer-to-Consumer) e-commerce platform.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **JWT Authentication**: Secure token-based authentication
- **Modular Architecture**: Clean separation of concerns with scalable structure
- **API Versioning**: Versioned API endpoints for future compatibility
- **Comprehensive Testing**: Built-in testing structure with pytest

## Project Structure

```
Driptyard_Backend/
├── app/
│   ├── core/           # Configuration, database, security
│   ├── api/v1/         # Versioned API endpoints
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic validation schemas
│   ├── services/       # Business logic layer
│   ├── utils/          # Helper functions
│   └── tests/          # Test suite
├── migrations/         # Database migrations (Alembic)
├── static/            # Static files
├── scripts/           # Utility scripts
└── docs/              # Documentation
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Driptyard_Backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### 4. Environment Configuration

```bash
# Copy the sample environment file
cp sample.env.txt .env

# Edit .env with your actual values
# Make sure to set your DATABASE_URL and SECRET_KEY
```

### 5. Database Setup

```bash
# Install PostgreSQL and create a database
# Update DATABASE_URL in .env file

# Initialize Alembic (when ready)
alembic init migrations

# Create your first migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 6. Run the Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Development

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `DELETE /api/v1/users/me` - Delete current user

### Products
- `GET /api/v1/products/` - List products
- `POST /api/v1/products/` - Create product
- `GET /api/v1/products/{id}` - Get product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

### Orders
- `GET /api/v1/orders/` - List orders
- `POST /api/v1/orders/` - Create order
- `GET /api/v1/orders/{id}` - Get order
- `PUT /api/v1/orders/{id}` - Update order

### Payments
- `POST /api/v1/payments/` - Process payment
- `GET /api/v1/payments/{id}` - Get payment status

### Chat
- `GET /api/v1/chat/conversations/` - List conversations
- `POST /api/v1/chat/messages/` - Send message
- `GET /api/v1/chat/messages/{conversation_id}` - Get messages

## Future Features

- Real-time chat with WebSockets
- Payment gateway integration
- File upload for product images
- Email notifications
- Advanced search and filtering
- Recommendation system
- Analytics and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.
