from flask import Blueprint, request, jsonify, Response
from app.models import SaleOrder, SaleItem
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

sale_orders_bp = Blueprint('saleorders', __name__)

#CRUD
@sale_orders_bp.route('/sales', methods=["GET"])
#@jwt_required()
def get_orders() -> tuple[Response, int]:
    try:
        orders = SaleOrder.query.all()
        orders_dict = [order.to_dict() for order in orders]

        for order in orders_dict:
            order['items'] = [item.to_dict() for item in SaleItem.query.filter_by(sale_order_id=order['id']).all()]

        return jsonify(orders_dict), 200
    except Exception as e:
        return jsonify({"error": "Failed to connect to Database"}), 500

@sale_orders_bp.route('/sales', methods=["POST"])
#@jwt_required()
def create_order():
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando os dados necessarios
    ## Cliente e funcionario devem existir
    client_id = data.get("client_id")
    employee_id = data.get("employee_id")
    if client_id is None or employee_id is None:
        return jsonify({"error": "Client ID and Employee ID are required"}), 400
    
    ## Verificando se os produtos existem
    items = data.get("items")
    if items is None or not isinstance(items, list) or len(items) == 0:
        return jsonify({"error": "Items are required"}), 400
    
    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "Invalid item format"}), 400
        if 'product_id' not in item or 'quantity' not in item or 'price' not in item:
            return jsonify({"error": "Product ID, quantity and price are required for each item"}), 400
    ### Verificar se o produto existe no banco de dados

    # Criado o pedido de venda
    new_order = SaleOrder(
        client_id=client_id,
        employee_id=employee_id,
        date=data.get('date'),
        payment_method=data.get('payment_method'),
        status=data.get('status')
    )

    # Adicionando o pedido de venda ao banco de dados
    try:
        db.session.add(new_order)
        db.session.commit()
        db.session.refresh(new_order)
    except Exception as e:
        return jsonify({"error": "Failed to connect to Database to create the order"}), 500

    # Criando os itens do pedido
    saleItems = []
    for item in items:
        sale_item = SaleItem(
            sale_order_id=new_order.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            price=item['price'],
            discount=item.get('discount', 0.0)
        )
        saleItems.append(sale_item)

    # Adicionado os itens ao banco de dados
    try:
        for sale_item in saleItems:
            db.session.add(sale_item)
        db.session.commit()
        db.session.refresh(sale_item)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to connect to Database to add the items"}), 500
    
    return jsonify(new_order.to_dict()), 201

@sale_orders_bp.route('/sales/<int:order_id>', methods=["GET"])
#@jwt_required()
def detail_order(order_id):
    try:
        order = SaleOrder.query.filter_by(id=order_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500
    
    if order:
        return jsonify(order.to_dict()), 200
    else:
        return jsonify({"error": "Order not found"}), 404

@sale_orders_bp.route('/sales/<int:order_id>', methods=["PUT"])
#@jwt_required()
def update_order(order_id):
    try:
        order = SaleOrder.query.filter_by(id=order_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500

    if order:
        data = request.get_json()
        # Verificando o pacote recebido
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON format"}), 400

       # Atualizando os dados do pedido de venda
        order.client_id = data.get("client_id", order.client_id)
        order.employee_id = data.get("employee_id", order.employee_id)
        order.date = data.get("date", order.date)
        order.payment_method = data.get("payment_method", order.payment_method)
        order.status = data.get("status", order.status)

        # Atualizando os itens do pedido de venda
        ## TODO: Implementar a atualização dos itens do pedido de venda

        db.session.commit()

        return jsonify(order.to_dict()), 200
    else:
        return jsonify({"error": "Order not found"}), 404

@sale_orders_bp.route('/sales/<int:order_id>', methods=["DELETE"])
#@jwt_required()
def remove_order(order_id):
    try:
        order = SaleOrder.query.filter_by(id=order_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500
    
    if order:
        # Deltando em cascata
        items = SaleItem.query.filter_by(sale_order_id=order.id).all()
        for item in items:
            db.session.delete(item)

        db.session.delete(order)
        db.session.commit()
        return jsonify({"message": "Order deleted"}), 200
    else:
        return jsonify({"error": "Order not found"}), 404