import pytest

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db as _db
from flask_jwt_extended import create_access_token

@pytest.fixture()
def app():
    """Create and configure a new app instance for each test."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-super-secret-jwt-key",
        "JWT_ACCESS_TOKEN_EXPIRES": 300,  # 5 minutes for easier testing
        "JWT_REFRESH_TOKEN_EXPIRES": 600, # 10 minutes for easier testing
    }

    app_instance = create_app(test_config)

    return app_instance

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture()
def db(app):
    """Session-wide test database."""
    with app.app_context():
        yield _db

@pytest.fixture()
def auth_headers(app):
    """Generate JWT authentication headers."""
    with app.app_context():
        # Create a token for a dummy user
        access_token = create_access_token(identity="test_user@example.com")
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture()
def sample_employee_data():
    """Provides sample data for creating an employee."""
    return {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "0987654321",
        "address": "456 Oak St",
        "role": "Manager",
        "salary": 75000.0,
        "status": "Active"
    }