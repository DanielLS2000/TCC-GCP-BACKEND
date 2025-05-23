from flask import Blueprint, request, jsonify
from app.models import Inventory
from app import db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/', methods=['POST'])
def create_inventory():
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando dados necessarios
    name = data.get("name")
    address = data.get("address")
    if name is not None and address is not None:
        new_inventory = Inventory(
            name=name,
            adress=address
        )

        db.session.add(new_inventory)
        db.session.commit()
        db.session.refresh(new_inventory)
        
        return jsonify(data), 201
    else:
        return jsonify({"error": "Insuficient data"}), 406

@inventory_bp.route('/', methods=['GET'])
def read_inventory():
    categories = Inventory.query.all()
    categories_dict = [inventory.to_dict() for inventory in categories]

    return jsonify(categories_dict), 200

@inventory_bp.route('/<int:inventory_id>/update', methods=['PUT'])
def update_inventory(inventory_id):
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando se o inventario existe
    inventory = Inventory.query.filter_by(id=inventory_id).first()
    if not inventory:
        return jsonify({"message": "Inventario não encontrado"}), 404

    name = data.get("name")
    address = data.get("address")
    if name is not None and address is not None:
        inventory.name=name
        inventory.address=address

        db.session.commit()
        
        return jsonify(data), 200
    else:
        return jsonify({"error": "Insuficient data"}), 406

@inventory_bp.route('/<int:inventory_id>/delete', methods=['DELETE'])
def delete_inventory(inventory_id):
    inventory = Inventory.query.filter_by(id=inventory_id).first()
    
    if not inventory:
        return jsonify({"message": "Inventario não encontrado"}), 404
    
    db.session.delete(inventory)
    
    db.session.commit()

    return jsonify(200)