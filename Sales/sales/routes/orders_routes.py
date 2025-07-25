import json
from flask import Blueprint, request, jsonify, Response, url_for, current_app
import uuid
from datetime import datetime
from sales.models import SaleOrder, SaleItem
from sales import db
from flask_jwt_extended import jwt_required
from google.cloud import pubsub_v1
import os

sale_orders_bp = Blueprint('saleorders', __name__)

publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
TOPIC_NAME = 'inventory-updates'
TOPIC_PATH = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

INVOICE_TOPIC_NAME = 'sale-invoice-events'
INVOICE_TOPIC_PATH = publisher.topic_path(PROJECT_ID, INVOICE_TOPIC_NAME)


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
            order_dict['client_name'] = "Cliente Desconhecido"  # Placeholder
            order_dict['employee_name'] = "Funcionário Desconhecido"  # Placeholder
            order_dict['total'] = sum(item.price * item.quantity for item in items)
            orders_data.append(order_dict)
        return jsonify(orders_data), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500

@sale_orders_bp.route('/', methods=["POST"])
@jwt_required()
def create_sale():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    client_id = data.get("client_id")
    employee_id = data.get("employee_id")
    items_payload = data.get("items")

    if client_id is None or employee_id is None:
        return jsonify({"msg": "Client ID and Employee ID are required"}), 422

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
            return jsonify({"msg": "Product ID, quantity, and price are required for each item"}), 422
        
        if not isinstance(quantity, int) or quantity <= 0:
            return jsonify({"msg": "Item quantity must be a positive integer", "details": {"product_id": product_id}}), 422
        if not isinstance(price, (int, float)) or price < 0:
            return jsonify({"msg": "Item price must be a non-negative number", "details": {"product_id": product_id}}), 422

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
        db.session.commit() # Commit the sale order to get its ID
        db.session.refresh(new_sale)

        total_sale_value = 0.0
        invoice_items = []

        for item_data_dict in sale_items_to_create:
            sale_item = SaleItem(
                sale_order_id=new_sale.id, 
                product_id=item_data_dict['product_id'],
                quantity=item_data_dict['quantity'],
                price=item_data_dict['price'],
                discount=item_data_dict['discount']
            )
            db.session.add(sale_item)
            # --- Publicar mensagem no Pub/Sub para atualização de inventário ---
            message_data = {
                "product_id": item_data_dict['product_id'],
                "quantity_sold": item_data_dict['quantity']
            }
            future = publisher.publish(TOPIC_PATH, json.dumps(message_data).encode('utf-8'))
            # A operação é assíncrona, não esperamos pelo resultado aqui.
            current_app.logger.info(f"Published message for product {item_data_dict['product_id']}. Message ID: {future.result()}")
            
            # Calculo para Nota Fiscal
            item_total = (item_data_dict['quantity'] * item_data_dict['price']) - item_data_dict['discount']
            total_sale_value += item_total
            invoice_items.append({
                "product_id": item_data_dict['product_id'],
                "quantity": item_data_dict['quantity'],
                "unit_price": item_data_dict['price'],
                "discount": item_data_dict['discount'],
                "total_item_price": item_total
            })

        db.session.commit() # Commit all sale items to the database
        
        # Prepare the response with the created sale and its items
        created_sale_dict = new_sale.to_dict()
        items_created = SaleItem.query.filter_by(sale_order_id=new_sale.id).all()
        created_sale_dict['items'] = [item.to_dict() for item in items_created]

        invoice_data = {
            "nf_id": str(uuid.uuid4()), # Unique invoice identifier
            "sale_order_id": new_sale.id,
            "issue_date": datetime.now().isoformat(),
            "client_id": new_sale.client_id,
            "employee_id": new_sale.employee_id,
            "payment_method": new_sale.payment_method,
            "status": new_sale.status,
            "total_value": total_sale_value,
            "items": invoice_items,
            "observacoes": "Nota Fiscal gerada automaticamente."
        }
        invoice_message_data = {
            "sale_order": created_sale_dict,
            "invoice_data": invoice_data
        }
        invoice_future = publisher.publish(INVOICE_TOPIC_PATH, json.dumps(invoice_message_data).encode('utf-8'))
        current_app.logger.info(f"Published invoice generation message for Sale Order {new_sale.id}. Message ID: {invoice_future.result()}")

        location_uri = url_for('saleorders.get_sale_by_id', sale_id=new_sale.id, _external=True)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save sale to database", "details_dev": str(e)}), 500
    finally:
        db.session.close() # Close the database session after all operations

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
        sale_dict['client_name'] = "Cliente Desconhecido"  # Placeholder
        sale_dict['employee_name'] = "Funcionário Desconhecido"  # Placeholder
        sale_dict['total'] = sum(item.price * item.quantity for item in items)
        return jsonify(sale_dict), 200
    else:
        return jsonify({"msg": "Sale not found"}), 404

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

    items_payload = data.get("items")
    if items_payload is not None: 
        if not isinstance(items_payload, list): 
             return jsonify({"msg": "Items must be a list if provided"}), 422

        try:
            SaleItem.query.filter_by(sale_order_id=sale.id).delete()
            sale_items_to_update = []
            for item_data in items_payload:
                if not isinstance(item_data, dict):
                    return jsonify({"msg": "Invalid item format in items list"}), 400
                
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')
                price = item_data.get('price')

                if product_id is None or quantity is None or price is None:
                    return jsonify({"msg": "Product ID, quantity, and price are required for each new item"}), 422

                if not isinstance(quantity, int) or quantity <= 0:
                    return jsonify({"msg": "Item quantity must be a positive integer", "details": {"product_id": product_id}}), 422
                if not isinstance(price, (int, float)) or price < 0:
                    return jsonify({"msg": "Item price must be a non-negative number", "details": {"product_id": product_id}}), 422

                sale_items_to_update.append(SaleItem(
                    sale_order_id=sale.id,
                    product_id=product_id,
                    quantity=quantity,
                    price=price,
                    discount=item_data.get('discount', 0.0)
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
    else: 
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
        SaleItem.query.filter_by(sale_order_id=sale.id).delete()
        db.session.delete(sale)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete sale from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return Response(status=204)