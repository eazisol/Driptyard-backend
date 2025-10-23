"""
Test configuration and fixtures.

This module contains pytest configuration, fixtures, and test utilities
used across all test modules.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# Test database URL (in-memory SQLite for testing)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    
    Yields:
        Session: Database session
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with database dependency override.
    
    Args:
        db_session: Database session fixture
        
    Yields:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """
    Sample user data for testing.
    
    Returns:
        dict: Test user data
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "confirm_password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890"
    }


@pytest.fixture
def test_product_data():
    """
    Sample product data for testing.
    
    Returns:
        dict: Test product data
    """
    return {
        "name": "Test Product",
        "description": "A test product for testing purposes",
        "price": 99.99,
        "category": "Electronics",
        "condition": "new",
        "location": "Test City, Test State",
        "images": ["https://example.com/image1.jpg"],
        "tags": ["test", "electronics"],
        "is_negotiable": True,
        "is_available": True
    }


@pytest.fixture
def auth_headers(client, test_user_data):
    """
    Get authentication headers for authenticated requests.
    
    Args:
        client: Test client
        test_user_data: Test user data
        
    Returns:
        dict: Authentication headers
    """
    # TODO: Implement when authentication is ready
    # This will register a user and return auth headers
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_uuid():
    """
    Sample UUID for testing.
    
    Returns:
        str: Sample UUID string
    """
    return "123e4567-e89b-12d3-a456-426614174000"


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_user_data(**kwargs):
        """Create user test data with optional overrides."""
        default_data = {
            "email": "user@example.com",
            "username": "username",
            "password": "password123",
            "confirm_password": "password123",
            "first_name": "First",
            "last_name": "Last",
            "phone": "+1234567890"
        }
        return {**default_data, **kwargs}
    
    @staticmethod
    def create_product_data(**kwargs):
        """Create product test data with optional overrides."""
        default_data = {
            "name": "Product Name",
            "description": "Product description",
            "price": 50.00,
            "category": "Category",
            "condition": "new",
            "location": "Location",
            "images": [],
            "tags": [],
            "is_negotiable": True,
            "is_available": True
        }
        return {**default_data, **kwargs}
    
    @staticmethod
    def create_order_data(**kwargs):
        """Create order test data with optional overrides."""
        default_data = {
            "product_id": "123e4567-e89b-12d3-a456-426614174000",
            "quantity": 1,
            "total_amount": 50.00,
            "shipping_address": "123 Test St, Test City, Test State 12345",
            "notes": "Test order"
        }
        return {**default_data, **kwargs}


# Pytest configuration
pytest_plugins = []

# Test markers
pytest.mark.slow = pytest.mark.slow
pytest.mark.integration = pytest.mark.integration
