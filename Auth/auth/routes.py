from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from auth.models import User
from auth import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    # Consultar no banco de dados
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 401

    # Verificar senha
    if not user.check_password(password):
        return jsonify({"msg": "Invalid password"}), 401
    
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
    user = User.query.filter_by(email=current_user).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    user_data = {
        'email': current_user
    }
    return jsonify(user_data), 200

# Register
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    user = User.query.filter_by(email=email).first()
    
    if user is not None:
        return jsonify({"msg": "User already exists"}), 400
    
    # Registrando usuario
    new_user = User(
        username=username,
        email=email,
        role=role,
    )

    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to connect to Database"}), 500
    db.session.close()
    # Criando tokens
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    return jsonify(
        access_token=access_token,
        refresh_token=refresh_token,
        user=new_user.to_dict()
    ), 201
