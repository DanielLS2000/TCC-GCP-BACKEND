from flask import Blueprint, request, jsonify, Response
from app.models import Customer
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

customer_bp = Blueprint('customer', __name__)

#CRUD
@customer_bp.route('/clients', methods=["GET"])
@jwt_required()
def get_customers() -> tuple[Response, int]:
    try:
        customers = Customer.query.all()
        customers_dict = [customer.to_dict() for customer in customers]

        return jsonify(customers), 200
    except Exception as e:
        return jsonify({"error": "Failed to connect to Database"}), 500

@customer_bp.route('/clients', methods=["POST"])
@jwt_required()
def create_customer():
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando os dados necessarios
    name = data.get("name")
    if name is not None:
        new_employee = Customer(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address')
        )

        try:
            db.session.add(new_employee)
            db.session.commit()
            db.session.refresh(new_employee)
        except Exception as e:
            return jsonify({"error": "Failed to connect to Database"}), 500

        return jsonify(data), 201
    else:
        return jsonify({"error": "Insuficient data"}), 406

@customer_bp.route('/clients/<int:client_id>', methods=["GET"])
@jwt_required()
def detail_customer(client_id):
    try:
        customer = Customer.query.filter_by(id=client_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500
    if customer:
        return jsonify(customer.to_dict()), 200
    else:
        return jsonify({"error": "Employee not found"}), 404

@customer_bp.route('/clients/<int:client_id>', methods=["PUT"])
@jwt_required()
def update_employee(client_id):
    try:
        customer = Customer.query.filter_by(id=client_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500

    if customer:
        data = request.get_json()
        # Verificando o pacote recebido
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON format"}), 400

        # Atualizando os dados do funcionário
        customer.name = data.get('name', customer.name)
        customer.email = data.get('email', customer.email)
        customer.phone = data.get('phone', customer.phone)
        customer.address = data.get('address', customer.address)

        db.session.commit()

        return jsonify(customer.to_dict()), 200
    else:
        return jsonify({"error": "Employee not found"}), 404

@customer_bp.route('/clients/<int:client_id>', methods=["DELETE"])
@jwt_required()
def remove_employee(client_id):
    try:
        customer = Customer.query.filter_by(id=client_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500
    
    if customer:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": "Customer deleted"}), 200
    else:
        return jsonify({"error": "Customer not found"}), 404