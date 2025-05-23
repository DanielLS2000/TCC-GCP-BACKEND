from flask import Blueprint, request, jsonify
from app.models import Product, Category
from app import db

product_bp = Blueprint('products', __name__)

@product_bp.route('/', methods=['POST'])
def create_product():
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400
    
    # Verificando se a categoria existe caso fornecida
    category_id = data.get('category_id')
    if category_id is not None and not Category.query.filter_by(id=category_id).first():
        return jsonify({"error": "Category not found"}), 404
    
    # Verificando os dados necessarios
    name = data.get("name")
    buy_price=data.get('buy_price')
    if name is not None and buy_price is not None:

        new_product = Product(
            name=data.get('name'),
            buy_price=data.get('buy_price'),
            desc=data.get('desc'),  
            sell_price=data.get('sell_price'),
            category_id=category_id,  
            category_details=data.get('category_details'),  
            product_image=data.get('product_image')
        )


        db.session.add(new_product)
        db.session.commit()
        db.session.refresh(new_product)
        
        return jsonify(data), 201
    else:
        return jsonify({"error": "Insuficient data"}), 406


@product_bp.route('/', methods=['GET'])
def get_products():
    products = Product.query.all()
    products_dict = [product.to_dict() for product in products]

    return jsonify(products_dict)

@product_bp.route('/<int:product_id>/read', methods=['GET'])
def get_product(product_id):
    product = Product.query.filter_by(id=product_id).first()
    
    if product:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({"error": "Product not found"}), 404

@product_bp.route('/<int:product_id>/update', methods=['PUT'])
def update_product(product_id):
    product = Product.query.filter_by(id=product_id).first()
    
    # Verificando se o produto existe 
    if not product:
        return jsonify({"message": "Produto não encontrado"}), 404
    
    # Verificando o pacote recebido
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando se a categoria existe caso fornecida
    category_id = data.get('category_id')
    if category_id is not None and not Category.query.filter_by(id=category_id).first():
        return jsonify({"error": "Category not found"}), 404
    
    # Verificando os dados necessarios 
    name = data.get("name")
    buy_price=data.get('buy_price')
    if name is not None and buy_price is not None:
        product.name=name
        product.buy_price=buy_price
        product.desc=data.get('desc')
        product.sell_price=data.get('sell_price')
        product.category_id=category_id
        product.category_details=data.get('category_details')
        product.product_image=data.get('product_image')
        
        db.session.commit()

        return jsonify(200)
    else:
        return jsonify({"error": "Insuficient data"}), 406

@product_bp.route('/<int:product_id>/delete', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.filter_by(id=product_id).first()
    
    if not product:
        return jsonify({"message": "Produto não encontrado"}), 404
    
    db.session.delete(product)
    
    db.session.commit()

    return jsonify(200)

@product_bp.route('/search', methods=['GET'])
def search_product():
    search_term = request.args.get('name', '')
    
    if not search_term:
        return jsonify({"message": "Termo de pesquisa é necessário"}), 400
    
    products = Product.query.filter(Product.name.ilike(f'%{search_term}%')).all()
    return jsonify([product.to_dict() for product in products])