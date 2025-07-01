from flask import Blueprint, request, jsonify, Response, url_for
from inventory.models import Inventory
from inventory import db
from flask_jwt_extended import jwt_required

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/', methods=['POST'])
@jwt_required()
def create_inventory_location():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    # Validando os campos obrigatórios
    name = data.get("name")
    address = data.get("address")

    if not name or not address:
        missing_fields = []
        if not name: missing_fields.append('name')
        if not address: missing_fields.append('address')
        return jsonify({
            "msg": "Insufficient or invalid data provided.",
            "details": {field: f"{field.capitalize()} is required." for field in missing_fields}
        }), 422

    new_location = Inventory(
        name=name,
        address=address
    )

    try:
        db.session.add(new_location)
        db.session.commit()
        db.session.refresh(new_location)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save inventory location to database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    location_uri = url_for('inventory.get_inventory_location_by_id', location_id=new_location.id, _external=True)

    return jsonify(new_location.to_dict()), 201, {'Location': location_uri}


@inventory_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_inventory_locations(): 
    try:
        locations = Inventory.query.all()
        locations_dict = [location.to_dict() for location in locations]
        return jsonify(locations_dict), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500

@inventory_bp.route('/<int:location_id>', methods=['GET'])
@jwt_required()
def get_inventory_location_by_id(location_id: int):
    try:
        location = db.session.get(Inventory, location_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching inventory location", "details_dev": str(e)}), 500

    if location:
        return jsonify(location.to_dict()), 200
    else:
        return jsonify({"msg": "Inventory location not found"}), 404


@inventory_bp.route('/<int:location_id>', methods=['PUT'])
@jwt_required()
def update_inventory_location_by_id(location_id: int):
    try:
        location = db.session.get(Inventory, location_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching inventory location for update", "details_dev": str(e)}), 500

    if not location:
        return jsonify({"msg": "Inventory location not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    name = data.get("name")
    address = data.get("address")

    if 'name' in data and not name:
        return jsonify({"msg": "Invalid data for update.", "details": {"name": "Name cannot be empty if provided."}}), 422
    if 'address' in data and not address:
        return jsonify({"msg": "Invalid data for update.", "details": {"address": "Address cannot be empty if provided."}}), 422

    location.name = data.get('name', location.name)
    location.address = data.get('address', location.address)

    location_data_dict = location.to_dict()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update inventory location in database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return jsonify(location_data_dict), 200


@inventory_bp.route('/<int:location_id>', methods=['DELETE'])
@jwt_required()
def delete_inventory_location_by_id(location_id: int):
    try:
        location = db.session.get(Inventory, location_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching inventory location for deletion", "details_dev": str(e)}), 500
    
    if not location:
        return jsonify({"msg": "Inventory location not found"}), 404
    
    try:
        db.session.delete(location)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete inventory location from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return Response(status=204)