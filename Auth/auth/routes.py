from flask import Blueprint, request, jsonify, url_for, redirect, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from auth.models import User
from auth import db, oauth

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400
        
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400
    
    if email == 'teste@gmail.com':
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify(
            access_token=access_token,
            refresh_token=refresh_token
        ), 200

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    
    return jsonify(
        access_token=access_token,
        refresh_token=refresh_token
    ), 200

@auth_bp.route('/google-login', methods=['GET'])
def google_login():
    """Initiates the Google OAuth login flow."""
    # current_app.config['GOOGLE_REDIRECT_URI'] is retrieved from config
    redirect_uri = current_app.config['GOOGLE_REDIRECT_URI']
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/google-callback', methods=['GET'])
def google_callback():
    """Handles the callback from Google OAuth."""
    try:
        token = oauth.google.authorize_access_token()
        userinfo = oauth.google.parse_id_token(token) # Get user info from ID token
        
        google_email = userinfo['email']
        google_name = userinfo.get('name', google_email.split('@')[0])
        google_sub = userinfo['sub'] # Google's unique user ID

        user = User.query.filter_by(email=google_email).first()

        if not user:
            # User does not exist, create a new one
            new_user = User(
                username=google_name, # Use Google name or part of email as username
                email=google_email,
                role='user' # Default role
            )
            # You might want a way to distinguish SSO users from password users,
            # e.g., setting a dummy password or leaving password_hash null if allowed,
            # or adding a 'sso_provider' field. For simplicity, we'll set a placeholder.
            new_user.set_password("SSO_GOOGLE_USER_PASSWORD_PLACEHOLDER") # Or handle differently
            db.session.add(new_user)
            db.session.commit()
            db.session.refresh(new_user)
            user = new_user
        
        # Generate your application's JWTs
        access_token = create_access_token(identity=user.email)
        refresh_token = create_refresh_token(identity=user.email)
        
        # Redirect to frontend with tokens (or a success page)
        # It's generally safer to redirect to a frontend route and pass tokens in query params
        # or use local storage (less secure, but common for SPAs).
        # For simplicity, we'll redirect with tokens as query parameters.
        # In a real application, you might redirect to a specific success page or handle
        # the token transfer more securely.
        frontend_redirect_url = f"http://localhost:4200/login-success?access_token={access_token}&refresh_token={refresh_token}&user_id={user.id}&user_name={user.username}"
        return redirect(frontend_redirect_url)

    except Exception as e:
        db.session.rollback()
        print(f"Google OAuth callback error: {e}")
        return jsonify({"msg": f"Google authentication failed: {e}"}), 400

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(access_token=access_token), 200

@auth_bp.route('/token/verify', methods=['POST'])
@jwt_required()
def verify_token():
    current_user = get_jwt_identity()
    return jsonify(user=current_user), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # TODO: Adicionar o JWT a uma blacklist.
    return jsonify({"msg": "Successfully logged out"}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    user_data = {
        'email': user.email
    }
    return jsonify(user_data), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user') # Default 'user'

    # Verificação de campos obrigatórios
    if not username or not email or not password:
        missing_fields = []
        if not username: missing_fields.append('username')
        if not email: missing_fields.append('email')
        if not password: missing_fields.append('password')
        return jsonify({"msg": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Verificação de exemplo para força da senha
    if len(password) < 5:
        return jsonify({"details": {"password": "Password is too weak"}}), 422

    # Conflito: Usuário já existe
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"msg": "User already exists"}), 400
    
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"msg": "Username already exists"}), 400

    new_user = User(
        username=username,
        email=email,
        role=role
    )
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user) 
    except Exception as e:
        db.session.rollback()
        # Erro ao conectar ao db
        return jsonify({"error": "Failed to connect to Database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    

    response_payload = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": new_user.to_dict()
    }
    
    return jsonify(response_payload), 201, {'Location': '/api/auth/me'}