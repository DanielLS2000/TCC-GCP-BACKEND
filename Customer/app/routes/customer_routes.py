from flask import Blueprint, request, jsonify, Response, url_for
from app.models import Customer
from app import db
from flask_jwt_extended import jwt_required 

customer_bp = Blueprint('customer', __name__)

# CRUD

@customer_bp.route('/', methods=["GET"])
@jwt_required()
def get_customers() -> tuple[Response, int]:
    try:
        customers = Customer.query.all()
        customers_dict = [customer.to_dict() for customer in customers]
        return jsonify(customers_dict), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500

@customer_bp.route('/', methods=["POST"])
@jwt_required()
def create_customer():
    data = request.get_json()

    if not data:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    # Validando os campos obrigatórios
    required_fields = ['name', 'email', 'phone', 'address']
    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        # Dados inválidos ou insuficientes
        return jsonify({
            "msg": "Insufficient or invalid data provided.",
            "details": {field: f"{field.capitalize()} is required." for field in missing_fields}
        }), 422

    new_customer = Customer(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address')
    )

    try:
        db.session.add(new_customer)
        db.session.commit()
        db.session.refresh(new_customer)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save customer to database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    location_uri = url_for('customer.get_customer_by_id', customer_id=new_customer.id, _external=True)
    
    return jsonify(new_customer.to_dict()), 201, {'Location': location_uri}


@customer_bp.route('/<int:customer_id>', methods=["GET"])
@jwt_required()
def get_customer_by_id(customer_id: int):
    try:
        customer = db.session.get(Customer, customer_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching customer", "details_dev": str(e)}), 500
    
    if customer:
        return jsonify(customer.to_dict()), 200
    else:
        return jsonify({"msg": "Customer not found"}), 404

@customer_bp.route('/<int:customer_id>', methods=["PUT"])
@jwt_required()
def update_customer(customer_id: int):
    try:
        customer = db.session.get(Customer, customer_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching customer for update", "details_dev": str(e)}), 500

    if not customer:
        return jsonify({"msg": "Customer not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400
    
    # Verificando se os campos obrigatórios estão presentes
    if 'name' in data and not data.get('name'):
        return jsonify({
            "msg": "Invalid data for update.",
            "details": {"name": "Name cannot be empty."}
        }), 422

    # Atualizando os dados do cliente
    customer.name = data.get('name', customer.name)
    customer.email = data.get('email', customer.email)
    customer.phone = data.get('phone', customer.phone)
    customer.address = data.get('address', customer.address)

    customer_data_dict = customer.to_dict()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update customer in database", "details_dev": str(e)}), 500
    finally:
        db.session.close()
        
    return jsonify(customer_data_dict), 200


@customer_bp.route('/<int:customer_id>', methods=["DELETE"])
@jwt_required()
def delete_customer(customer_id: int):
    try:
        customer = db.session.get(Customer, customer_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching customer for deletion", "details_dev": str(e)}), 500
    
    if not customer:
        return jsonify({"msg": "Customer not found"}), 404

    try:
        db.session.delete(customer)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete customer from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()
        
    return Response(status=204)