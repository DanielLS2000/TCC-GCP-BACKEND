from flask import Blueprint, request, jsonify, Response, url_for
from app.models import Product, Category
from app import db
from flask_jwt_extended import jwt_required

product_bp = Blueprint('products', __name__)


@product_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    data = request.get_json()

    if not data:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    name = data.get("name")
    buy_price = data.get("buy_price")

    if not name or buy_price is None: # Checar se buy_price foi fornecido
        missing_fields = []
        if not name: missing_fields.append('name')
        if buy_price is None: missing_fields.append('buy_price')
        return jsonify({
            "msg": "Insufficient or invalid data provided.",
            "details": {field: f"{field.capitalize()} is required." for field in missing_fields}
        }), 422

    category_id = data.get('category_id')
    if category_id is not None:
        category = db.session.get(Category, category_id)
        if not category:
            return jsonify({"msg": "Category not found"}), 404

    new_product = Product(
        name=name,
        buy_price=buy_price,
        desc=data.get('desc'),
        sell_price=data.get('sell_price'),
        category_id=category_id,
        category_details=data.get('category_details'),
        product_image=data.get('product_image')
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        db.session.refresh(new_product)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save product to database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    location_uri = url_for('products.get_product_by_id', product_id=new_product.id, _external=True)

    return jsonify(new_product.to_dict()), 201, {'Location': location_uri}


@product_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_products():
    try:
        products = Product.query.all()
        products_dict = [product.to_dict() for product in products]
        return jsonify(products_dict), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product_by_id(product_id: int):
    try:
        product = db.session.get(Product, product_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching product", "details_dev": str(e)}), 500

    if product:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({"msg": "Product not found"}), 404


@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product_by_id(product_id: int):
    try:
        product = db.session.get(Product, product_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching product for update", "details_dev": str(e)}), 500

    if not product:
        return jsonify({"msg": "Product not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    name = data.get("name")
    buy_price = data.get("buy_price")

    if 'name' in data and not name:
        return jsonify({"msg": "Invalid data for update.", "details": {"name": "Name cannot be empty if provided."}}), 422
    if 'buy_price' in data and buy_price is None:
        return jsonify({"msg": "Invalid data for update.", "details": {"buy_price": "Buy price cannot be null if provided."}}), 422

    category_id = data.get('category_id')
    if category_id is not None:
        category = db.session.get(Category, category_id)
        if not category:
            return jsonify({"msg": "Category not found"}), 404
    
    # Atualizando os campos do produto
    product.name = data.get('name', product.name)
    product.buy_price = data.get('buy_price', product.buy_price)
    product.desc = data.get('desc', product.desc)
    product.sell_price = data.get('sell_price', product.sell_price)
    if "category_id" in data:
        product.category_id = category_id
    product.category_details = data.get('category_details', product.category_details)
    product.product_image = data.get('product_image', product.product_image)

    try:
        db.session.commit()
        product_data_dict = product.to_dict()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update product in database", "details_dev": str(e)}), 500
    finally:
        db.session.close()
    
    return jsonify(product_data_dict), 200


@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product_by_id(product_id: int):
    try:
        product = db.session.get(Product, product_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching product for deletion", "details_dev": str(e)}), 500

    if not product:
        return jsonify({"msg": "Product not found"}), 404
    
    try:
        db.session.delete(product)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete product from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return Response(status=204)


@product_bp.route('/search', methods=['GET'])
@jwt_required()
def search_products_by_name(): 
    search_term = request.args.get('name')

    if not search_term:
        return jsonify({"msg": "Search term 'name' is required"}), 400
    
    try:
        products = Product.query.filter(Product.name.ilike(f'%{search_term}%')).all()
        return jsonify([product.to_dict() for product in products]), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred during product search", "details_dev": str(e)}), 500