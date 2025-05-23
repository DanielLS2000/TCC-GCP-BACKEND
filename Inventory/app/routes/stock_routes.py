from flask import Blueprint, request, jsonify
from app.models import Stock, Product, Inventory
from app import db

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/', methods=['POST'])
def create_stock():
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando se o produto e o inventario existem
    product_id=data.get("product_id")
    inventory_id=data.get("inventory_id")
    
    product = Product.query.filter_by(id=product_id).first()
    inventory = Inventory.query.filter_by(id=inventory_id).first()
    
    if not product:
        return jsonify({"message": "Produto não encontrado"}), 404
    if not inventory:
        return jsonify({"message": "Inventario não encontrado"}), 404
    
    # Verificando dados necessarios
    quantity=data.get("quantity")
    if quantity is not None:
        new_stock = Stock(
            product_id=product,
            inventory_id=inventory,
            quantity=quantity
        )

        db.session.add(new_stock)
        db.session.commit()
        db.session.refresh(new_stock)
        
        return jsonify(data), 201
    else:
        return jsonify({"error": "Insuficient data"}), 406

@stock_bp.route('/', methods=['GET'])
def read_stock():
    categories = Stock.query.all()
    categories_dict = [stock.to_dict() for stock in categories]

    return jsonify(categories_dict), 200

@stock_bp.route('/<int:stock_id>/update', methods=['PUT'])
def update_stock(stock_id):
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando se o estoque existe
    stock = Stock.query.filter_by(id=stock_id).first()

    # Verificando se o produto e o inventario existem
    product_id=data.get("product_id")
    inventory_id=data.get("inventory_id")
    
    product = Product.query.filter_by(id=product_id).first()
    inventory = Inventory.query.filter_by(id=inventory_id).first()
    
    if not product:
        return jsonify({"message": "Produto não encontrado"}), 404
    if not inventory:
        return jsonify({"message": "Inventario não encontrado"}), 404

    if not stock:
        return jsonify({"message": "Estoque não encontrado"}), 404

    quantity = data.get("quantity")

    if quantity is not None:
        stock.product_id=product_id,
        stock.inventory_id=inventory_id,
        stock.quantity=quantity

        db.session.commit()
        
        return jsonify(data), 200
    else:
        return jsonify({"error": "Insuficient data"}), 406

@stock_bp.route('/<int:stock_id>/delete', methods=['DELETE'])
def delete_stock(stock_id):
    stock = Stock.query.filter_by(id=stock_id).first()
    
    if not stock:
        return jsonify({"message": "Estoque não encontrado"}), 404
    
    db.session.delete(stock)
    
    db.session.commit()

    return jsonify(200)