import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth import create_app as _create_app_original # Renamed to avoid conflict
from auth import db as _db_instance # Global db instance from auth package
from auth.models import User

@pytest.fixture(scope='function')
def app_fixture():
    """
    Creates and configures a new app instance for each test function.
    Each test will run with a clean database.
    """
    original_db_uri = os.environ.get("DATABASE_URL")
    original_secret_key = os.environ.get("SECRET_KEY")
    original_jwt_secret_key = os.environ.get("JWT_SECRET_KEY")

    test_db_uri = "sqlite:///:memory:"

    # Create the Flask app using the factory from your auth package

    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": test_db_uri, # Ensure app uses the test DB URI
        "JWT_ACCESS_TOKEN_EXPIRES": 300,  # 5 minutes for easier testing
        "JWT_REFRESH_TOKEN_EXPIRES": 600, # 10 minutes for easier testing
    }

    flask_app = _create_app_original(config_overrides=test_config)

    yield flask_app


@pytest.fixture
def client(app_fixture):
    """A test client for the app."""
    return app_fixture.test_client()


@pytest.fixture
def db(app_fixture):
    """
    Provides the database instance, ensuring it's used within app context.
    Relies on app_fixture to handle setup and teardown.
    """
    with app_fixture.app_context():
        yield _db_instance


@pytest.fixture
def new_user_payload():
    """Returns a sample payload for creating a new user."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPassword123",
        "role": "user"
    }

@pytest.fixture
def created_user(db, new_user_payload):
    """
    Fixture to create a user directly in the DB and return the instance.
    """
    user = User(
        username=new_user_payload["username"],
        email=new_user_payload["email"],
        role=new_user_payload.get("role", "user")
    )
    user.set_password(new_user_payload["password"]) # Uses the model's password setting method
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def registered_user_with_tokens(client, db, new_user_payload):
    """
    Registers a user via API and returns the user object and tokens.
    Useful for tests that require an authenticated user.
    """
    payload_copy = new_user_payload.copy()
    payload_copy["email"] = "registered@example.com" # Ensure unique email
    payload_copy["username"] = "registereduser" # Ensure unique username

    response = client.post('/api/auth/register', json=payload_copy) #
    assert response.status_code == 201
    json_data = response.get_json()

    user_instance = db.session.query(User).filter_by(email=payload_copy["email"]).first()
    return {
        "user": user_instance,
        "access_token": json_data["access_token"],
        "refresh_token": json_data["refresh_token"]
    }