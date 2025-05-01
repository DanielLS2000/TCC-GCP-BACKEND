from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

# Mock database de usuários
USERS = {
    "admin@gmail.com": {
        "password": "admin",
        "roles": ["admin", "user"]
    }
}

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = USERS.get(email)
    if user and user['password'] == password:
        access_token = create_access_token(identity={"email": email, "roles": user["roles"]})
        refresh_token = create_refresh_token(identity={"email": email})
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    return jsonify({"msg": "Invalid credentials"}), 401

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

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
