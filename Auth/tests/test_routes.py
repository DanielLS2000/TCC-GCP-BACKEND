import pytest
from flask_jwt_extended import decode_token

# Helper function to get auth headers
def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

# --- Registration Tests ---
def test_register_success(client, new_user_payload):
    response = client.post('/api/auth/register', json=new_user_payload)
    json_data = response.get_json()

    assert response.status_code == 201
    assert 'access_token' in json_data
    assert 'refresh_token' in json_data
    assert 'user' in json_data
    assert json_data['user']['email'] == new_user_payload['email']
    assert json_data['user']['username'] == new_user_payload['username']
    assert response.headers['Location'] == '/api/auth/me'

def test_register_missing_fields(client, new_user_payload):
    incomplete_payload = new_user_payload.copy()
    del incomplete_payload['email']
    response = client.post('/api/auth/register', json=incomplete_payload)
    assert response.status_code == 400 # Based on route logic for missing fields
    assert "Missing required fields: email" in response.get_json()['msg']

def test_register_weak_password(client, new_user_payload):
    weak_password_payload = new_user_payload.copy()
    weak_password_payload['password'] = "123" # Password too short based on route logic
    response = client.post('/api/auth/register', json=weak_password_payload)
    assert response.status_code == 422
    assert "Password is too weak" in response.get_json()['details']['password']

def test_register_existing_email(client, new_user_payload, created_user):
    # created_user fixture already added a user with new_user_payload's email
    response = client.post('/api/auth/register', json=new_user_payload)
    assert response.status_code == 400
    assert response.get_json()['msg'] == "User already exists" # (checks email first)

def test_register_existing_username(client, new_user_payload, db):
    # Create a user with a different email but same username
    user_same_username = {
        "username": new_user_payload["username"],
        "email": "another@example.com",
        "password": "password123"
    }
    # Register first user, ensure it succeeds for the sake of this test setup
    first_register_response = client.post('/api/auth/register', json=user_same_username)
    assert first_register_response.status_code == 201


    payload_diff_email_same_username = new_user_payload.copy()
    # Use a new email to avoid conflict with the 'created_user' fixture if it used the same email
    payload_diff_email_same_username["email"] = "yetanother_unique_email@example.com"
    # Attempt to register with the same username as user_same_username
    response = client.post('/api/auth/register', json=payload_diff_email_same_username)
    assert response.status_code == 400
    assert response.get_json()['msg'] == "Username already exists"

def test_register_no_json_body(client):
    # Send data with a Content-Type that request.get_json() will not parse,
    # leading to data being None and triggering the custom 400 error.
    response = client.post('/api/auth/register', data="not json", content_type="text/plain")
    assert response.status_code == 400
    assert "Request body is missing or not JSON" in response.get_json()['msg']


# --- Login Tests ---
def test_login_success(client, created_user, new_user_payload):
    login_payload = {
        "email": new_user_payload['email'],
        "password": new_user_payload['password']
    }
    response = client.post('/api/auth/login', json=login_payload)
    json_data = response.get_json()

    assert response.status_code == 200
    assert 'access_token' in json_data
    assert 'refresh_token' in json_data

def test_login_invalid_email(client, new_user_payload):
    login_payload = {
        "email": "wrong@example.com",
        "password": new_user_payload['password']
    }
    response = client.post('/api/auth/login', json=login_payload)
    assert response.status_code == 401
    assert response.get_json()['msg'] == "Invalid credentials"

def test_login_incorrect_password(client, created_user, new_user_payload):
    login_payload = {
        "email": new_user_payload['email'],
        "password": "wrongpassword"
    }
    response = client.post('/api/auth/login', json=login_payload)
    assert response.status_code == 401
    assert response.get_json()['msg'] == "Invalid credentials"

def test_login_missing_fields(client):
    response = client.post('/api/auth/login', json={"email": "test@example.com"})
    assert response.status_code == 400
    assert response.get_json()['msg'] == "Missing email or password"

def test_login_no_json_body(client):
    # Send data with a Content-Type that request.get_json() will not parse
    response = client.post('/api/auth/login', data="not json", content_type="text/plain")
    assert response.status_code == 400
    assert "Request body is missing or not JSON" in response.get_json()['msg']


# --- Token Refresh Test ---
def test_refresh_token_success(client, registered_user_with_tokens):
    refresh_token = registered_user_with_tokens['refresh_token']
    response = client.post('/api/auth/refresh', headers=get_auth_headers(refresh_token))
    json_data = response.get_json()

    assert response.status_code == 200
    assert 'access_token' in json_data
    new_access_token_data = decode_token(json_data['access_token'])
    assert new_access_token_data['sub'] == registered_user_with_tokens['user'].email

def test_refresh_token_with_access_token_fails(client, registered_user_with_tokens):
    access_token = registered_user_with_tokens['access_token']
    response = client.post('/api/auth/refresh', headers=get_auth_headers(access_token))
    assert response.status_code == 422
    assert "Only refresh tokens are allowed" in response.get_json().get("msg", "")

def test_refresh_token_no_token(client):
    response = client.post('/api/auth/refresh')
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.get_json().get("msg", "")


# --- Token Verify Test ---
def test_verify_token_success(client, registered_user_with_tokens):
    access_token = registered_user_with_tokens['access_token']
    response = client.post('/api/auth/token/verify', headers=get_auth_headers(access_token))
    json_data = response.get_json()

    assert response.status_code == 200
    assert json_data['user'] == registered_user_with_tokens['user'].email

def test_verify_token_with_refresh_token_fails(client, registered_user_with_tokens):
    refresh_token = registered_user_with_tokens['refresh_token']
    response = client.post('/api/auth/token/verify', headers=get_auth_headers(refresh_token))
    assert response.status_code == 422
    # Corrected expected message from Flask-JWT-Extended
    assert "Only non-refresh tokens are allowed" in response.get_json().get("msg", "")


def test_verify_token_no_token(client):
    response = client.post('/api/auth/token/verify')
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.get_json().get("msg", "")


# --- Get Current User (/me) Tests ---
def test_get_me_success(client, registered_user_with_tokens):
    access_token = registered_user_with_tokens['access_token']
    response = client.get('/api/auth/me', headers=get_auth_headers(access_token))
    json_data = response.get_json()

    assert response.status_code == 200
    assert json_data['email'] == registered_user_with_tokens['user'].email

def test_get_me_no_token(client):
    response = client.get('/api/auth/me')
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.get_json().get("msg", "")


# --- Logout Test ---
def test_logout_success(client, registered_user_with_tokens):
    access_token = registered_user_with_tokens['access_token']
    response = client.post('/api/auth/logout', headers=get_auth_headers(access_token))
    assert response.status_code == 200
    assert response.get_json()['msg'] == "Successfully logged out"

def test_logout_no_token(client):
    response = client.post('/api/auth/logout')
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.get_json().get("msg", "")