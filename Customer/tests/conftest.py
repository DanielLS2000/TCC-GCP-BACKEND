import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Agora as importações devem funcionar
import pytest
from flask_jwt_extended import create_access_token
from app import create_app as customer_create_app, db as customer_db_instance
from app.models import Customer as CustomerModel_Class

@pytest.fixture(scope='session')
def test_app_instance():
    """
    Creates a Flask app instance for the test session.
    Configures the app for testing, including an in-memory SQLite database
    and a test JWT secret key.
    """
    # Configurações específicas para o ambiente de teste
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Usar banco de dados SQLite em memória
        "JWT_SECRET_KEY": "test-jwt-secret-key-customer", # Chave JWT para testes
        "SERVER_NAME": "localhost.test", # Necessário para url_for com _external=True
        # "WTF_CSRF_ENABLED": False, # Descomente se você usa Flask-WTF e quer desabilitar CSRF para testes
    }
    
    # Passa as configurações de override para a função create_app
    app = customer_create_app(config_overrides=test_config)
    
    yield app

@pytest.fixture(scope='function')
def test_client_instance(test_app_instance):
    """
    Provides a test client for the Flask app.
    Ensures a clean database state (schema and data) for each test function.
    """
    with test_app_instance.test_client() as client:
        with test_app_instance.app_context():
            # Ensure database is pristine for each test.
            # The reset_db in create_app sets up the initial schema.
            # For function-level isolation with an in-memory DB shared across a session-scoped app,
            # we explicitly drop and recreate tables.
            customer_db_instance.drop_all()
            customer_db_instance.create_all()
        yield client
        # No explicit teardown needed for client here; app_context handles itself.
        # In-memory SQLite is ephemeral.

@pytest.fixture(scope='function')
def jwt_access_token(test_app_instance):
    """Generates a JWT access token for a dummy authenticated user."""
    with test_app_instance.app_context():
        # The identity can be any string relevant to your user model/JWT setup
        token = create_access_token(identity="test_customer_user@example.com")
    return token

@pytest.fixture(scope='function')
def authorized_headers(jwt_access_token):
    """Provides a dictionary of headers including a JWT for authenticated requests."""
    return {
        "Authorization": f"Bearer {jwt_access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

@pytest.fixture(scope='function')
def pre_existing_customer_data(test_app_instance, test_client_instance):
    """
    Fixture to create and commit a customer to the DB.
    Returns a dictionary with the customer's data.
    """
    customer_payload = {
        "name": "Initial Test Customer",
        "email": "initial.customer@example.com",
        "phone": "0000000000",
        "address": "0 Initial Test St, Testville"
    }
    with test_app_instance.app_context():
        customer = CustomerModel_Class(**customer_payload)
        customer_db_instance.session.add(customer)
        customer_db_instance.session.commit()
        # Colete os dados necessários enquanto a sessão está ativa e o objeto populado
        data_to_return = {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address
        }
    return data_to_return # Retorna um dicionário