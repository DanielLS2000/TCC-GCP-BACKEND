from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

# Mock database de usuários
USERS = {
    "admin@gmail.com": {
        "password": "admin"
    }
}

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = USERS.get(email)
    if not user or user['password'] != password:
        return jsonify({"msg": "Bad email or password"}), 401
    
    # Criando tokens
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

@auth_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify():
    current_user = get_jwt_identity()
    return jsonify(user=current_user), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Add Token blacklist
    return jsonify({"msg": "Successfully logged out"}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user = get_jwt_identity()
    user = USERS.get(current_user)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    user_data = {
        'email': current_user
    }
    return jsonify(user_data), 200
