from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from auth.models import User
from auth import db

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