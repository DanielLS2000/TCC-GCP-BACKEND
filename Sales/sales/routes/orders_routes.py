from flask import Blueprint, request, jsonify, Response, url_for
from datetime import datetime
from sales.models import SaleOrder, SaleItem
from sales import db
from flask_jwt_extended import jwt_required

sale_orders_bp = Blueprint('saleorders', __name__)


@sale_orders_bp.route('/', methods=["GET"])
@jwt_required()
def get_sales():
    try:
        orders = SaleOrder.query.all()
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            # Carregar itens para cada venda
            items = SaleItem.query.filter_by(sale_order_id=order.id).all()
            order_dict['items'] = [item.to_dict() for item in items]
            orders_data.append(order_dict)
        return jsonify(orders_data), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500

# Refazer função
@sale_orders_bp.route('/', methods=["POST"])
@jwt_required()
def create_sale():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    # Requer client_id, employee_id, items.
    client_id = data.get("client_id")
    employee_id = data.get("employee_id")
    items_payload = data.get("items")

    if client_id is None or employee_id is None:
        return jsonify({"msg": "Client ID and Employee ID are required"}), 422
    
    # TODO: VALIDAR client_id: Fazer chamada ao microsserviço de Customer para verificar se client_id existe.
    #       Se não existir, retornar: jsonify({"msg": "Client not found"}), 404 (ou 422 se preferir para input inválido)
    # TODO: VALIDAR employee_id: Fazer chamada ao microsserviço de Employee para verificar se employee_id existe.
    #       Se não existir, retornar: jsonify({"msg": "Employee not found"}), 404 (ou 422)

    if not items_payload or not isinstance(items_payload, list) or len(items_payload) < 1:
        return jsonify({"msg": "Items are required and must be a non-empty list"}), 422

    sale_items_to_create = []
    for item_data in items_payload:
        if not isinstance(item_data, dict):
            return jsonify({"msg": "Invalid item format in items list"}), 400
        
        product_id = item_data.get('product_id')
        quantity = item_data.get('quantity')
        price = item_data.get('price')

        if product_id is None or quantity is None or price is None:
            # Requer product_id, quantity, price
            return jsonify({"msg": "Product ID, quantity, and price are required for each item"}), 422
        
        if not isinstance(quantity, int) or quantity <= 0:
            return jsonify({"msg": "Item quantity must be a positive integer", "details": {"product_id": product_id}}), 422
        if not isinstance(price, (int, float)) or price < 0:
            return jsonify({"msg": "Item price must be a non-negative number", "details": {"product_id": product_id}}), 422
            
        # TODO: VALIDAR product_id: Fazer chamada ao microsserviço de Product para verificar se product_id existe E se há estoque suficiente.
        #       Se não existir, retornar: jsonify({"msg": f"Product with ID {product_id} not found or insufficient stock"}), 404 (ou 422)

        sale_items_to_create.append({
            "product_id": product_id,
            "quantity": quantity,
            "price": price,
            "discount": item_data.get('discount', 0.0)
        })

    new_sale = SaleOrder(
        client_id=client_id,
        employee_id=employee_id,
        date=data.get('date', datetime.now()),
        payment_method=data.get('payment_method'),
        status=data.get('status', 'PENDING')
    )

    try:
        db.session.add(new_sale)
        db.session.commit() 
        db.session.refresh(new_sale)

        for item_data_dict in sale_items_to_create:
            sale_item = SaleItem(
                sale_order_id=new_sale.id, 
                product_id=item_data_dict['product_id'],
                quantity=item_data_dict['quantity'],
                price=item_data_dict['price'],
                discount=item_data_dict['discount']
            )
            db.session.add(sale_item)
        db.session.commit() 
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save sale to database", "details_dev": str(e)}), 500
    finally:
        db.session.close()
    
    created_sale_dict = new_sale.to_dict()
    items_created = SaleItem.query.filter_by(sale_order_id=new_sale.id).all()
    created_sale_dict['items'] = [item.to_dict() for item in items_created]

    location_uri = url_for('saleorders.get_sale_by_id', sale_id=new_sale.id, _external=True)

    return jsonify(created_sale_dict), 201, {'Location': location_uri}

@sale_orders_bp.route('/<int:sale_id>', methods=["GET"])
@jwt_required()
def get_sale_by_id(sale_id: int):
    try:
        sale = db.session.get(SaleOrder, sale_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching sale", "details_dev": str(e)}), 500
    
    if sale:
        sale_dict = sale.to_dict()
        items = SaleItem.query.filter_by(sale_order_id=sale.id).all()
        sale_dict['items'] = [item.to_dict() for item in items]
        return jsonify(sale_dict), 200
    else:
        return jsonify({"msg": "Sale not found"}), 404

# Refazer função
@sale_orders_bp.route('/<int:sale_id>', methods=["PUT"])
@jwt_required()
def update_sale_by_id(sale_id: int):
    try:
        sale = db.session.get(SaleOrder, sale_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching sale for update", "details_dev": str(e)}), 500

    if not sale:
        return jsonify({"msg": "Sale not found"}), 404

    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    # Atualizando os campos da venda principal
    sale.client_id = data.get("client_id", sale.client_id)
    sale.employee_id = data.get("employee_id", sale.employee_id)
    sale.date = data.get("date", sale.date)
    sale.payment_method = data.get("payment_method", sale.payment_method)
    sale.status = data.get("status", sale.status)
    # TODO: Se client_id ou employee_id forem alterados, VALIDAR sua existência via comunicação entre serviços.

    items_payload = data.get("items")
    if items_payload is not None: 
        if not isinstance(items_payload, list): 
             return jsonify({"msg": "Items must be a list if provided"}), 422

        # Remover itens antigos e adicionar novos
        try:
            SaleItem.query.filter_by(sale_order_id=sale.id).delete() #
            sale_items_to_update = []
            for item_data in items_payload:
                if not isinstance(item_data, dict): #
                    return jsonify({"msg": "Invalid item format in items list"}), 400 #
                
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')
                price = item_data.get('price')

                if product_id is None or quantity is None or price is None: #
                    return jsonify({"msg": "Product ID, quantity, and price are required for each new item"}), 422 #

                if not isinstance(quantity, int) or quantity <= 0:
                    return jsonify({"msg": "Item quantity must be a positive integer", "details": {"product_id": product_id}}), 422
                if not isinstance(price, (int, float)) or price < 0:
                    return jsonify({"msg": "Item price must be a non-negative number", "details": {"product_id": product_id}}), 422
                
                # TODO: VALIDAR product_id: Fazer chamada ao microsserviço de Product.

                sale_items_to_update.append(SaleItem(
                    sale_order_id=sale.id,
                    product_id=product_id,
                    quantity=quantity,
                    price=price,
                    discount=item_data.get('discount', 0.0) #
                ))
            if sale_items_to_update:
                db.session.add_all(sale_items_to_update)
            
            db.session.commit()

            updated_sale_dict = sale.to_dict()
            current_items = SaleItem.query.filter_by(sale_order_id=sale.id).all()
            updated_sale_dict['items'] = [item.to_dict() for item in current_items]
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to update sale items", "details_dev": str(e)}), 500
    else: # Nenhum item no payload, apenas atualiza os campos da venda.
        try:
            db.session.commit()
            updated_sale_dict = sale.to_dict()
            current_items = SaleItem.query.filter_by(sale_order_id=sale.id).all()
            updated_sale_dict['items'] = [item.to_dict() for item in current_items]
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to update sale fields", "details_dev": str(e)}), 500
    
    return jsonify(updated_sale_dict), 200


@sale_orders_bp.route('/<int:sale_id>', methods=["DELETE"])
@jwt_required()
def delete_sale_by_id(sale_id: int):
    try:
        sale = db.session.get(SaleOrder, sale_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching sale for deletion", "details_dev": str(e)}), 500
    
    if not sale:
        return jsonify({"msg": "Sale not found"}), 404
    
    try:
        SaleItem.query.filter_by(sale_order_id=sale.id).delete() #
        db.session.delete(sale) #
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete sale from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return Response(status=204)