from flask import Blueprint, request, jsonify, Response, url_for
from app.models import Stock, Product, Inventory
from app import db
from flask_jwt_extended import jwt_required

stock_bp = Blueprint('stock', __name__)


@stock_bp.route('/', methods=['POST'])
@jwt_required()
def create_stock_item():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    product_id = data.get("product_id")
    inventory_location_id = data.get("inventory_location_id")
    quantity = data.get("quantity") # Swagger define quantity como integer

    required_fields_map = {
        "product_id": product_id,
        "inventory_location_id": inventory_location_id,
        "quantity": quantity
    }
    missing_fields = [key for key, value in required_fields_map.items() if value is None]

    if missing_fields:
        return jsonify({
            "msg": "Insufficient or invalid data provided.",
            "details": {field: f"{field.replace('_', ' ').capitalize()} is required." for field in missing_fields}
        }), 422

    # Verificar se o produto e o local de inventário existem
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    inventory_location = db.session.get(Inventory, inventory_location_id)
    if not inventory_location:
        return jsonify({"msg": "Inventory location not found"}), 404
    
    new_stock_item = Stock(
        product_id=product_id,
        inventory_location_id=inventory_location_id,
        quantity=quantity
    )

    try:
        db.session.add(new_stock_item)
        db.session.commit()
        db.session.refresh(new_stock_item)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save stock item to database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    location_uri = url_for('stock.get_stock_item_by_id', stock_item_id=new_stock_item.id, _external=True)

    return jsonify(new_stock_item.to_dict()), 201, {'Location': location_uri}


@stock_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_stock_items():
    try:
        stock_items = Stock.query.all()
        stock_items_dict = [item.to_dict() for item in stock_items]
        return jsonify(stock_items_dict), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500

@stock_bp.route('/<int:stock_item_id>', methods=['GET'])
@jwt_required()
def get_stock_item_by_id(stock_item_id: int):
    try:
        stock_item = db.session.get(Stock, stock_item_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching stock item", "details_dev": str(e)}), 500

    if stock_item:
        return jsonify(stock_item.to_dict()), 200
    else:
        return jsonify({"msg": "Stock item not found"}), 404


@stock_bp.route('/<int:stock_item_id>', methods=['PUT'])
@jwt_required()
def update_stock_item_by_id(stock_item_id: int):
    try:
        stock_item = db.session.get(Stock, stock_item_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching stock item for update", "details_dev": str(e)}), 500

    if not stock_item:
        return jsonify({"msg": "Stock item not found"}), 404

    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    product_id = data.get("product_id")
    inventory_location_id = data.get("inventory_location_id")
    quantity = data.get("quantity")

    # Validar se os campos fornecidos para atualização são válidos
    if 'quantity' in data and (quantity is None or not isinstance(quantity, int) or quantity < 0):
         return jsonify({"msg": "Invalid data for update.", "details": {"quantity": "Quantity must be a non-negative integer if provided."}}), 422

    if product_id is not None:
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"msg": "Product not found for update"}), 404
        stock_item.product_id = product_id
    
    if inventory_location_id is not None:
        inventory_location = db.session.get(Inventory, inventory_location_id)
        if not inventory_location:
            return jsonify({"msg": "Inventory location not found for update"}), 404
        stock_item.inventory_location_id = inventory_location_id

    if 'quantity' in data:
        stock_item.quantity = quantity
    

    try:
        db.session.commit()
        stock_data_dict = stock_item.to_dict()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update stock item in database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return jsonify(stock_data_dict), 200


@stock_bp.route('/<int:stock_item_id>', methods=['DELETE'])
@jwt_required()
def delete_stock_item_by_id(stock_item_id: int):
    try:
        stock_item = db.session.get(Stock, stock_item_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching stock item for deletion", "details_dev": str(e)}), 500
    
    if not stock_item:
        return jsonify({"msg": "Stock item not found"}), 404
    
    try:
        db.session.delete(stock_item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete stock item from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return Response(status=204)