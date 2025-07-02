# Inventory/inventory/routes/pubsub_handlers.py
from flask import Blueprint, request, jsonify, current_app
from inventory.models import Product
from inventory import db
import base64
import json

pubsub_bp = Blueprint('pubsub', __name__)

@pubsub_bp.route('/inventory-update', methods=['POST'])
def receive_inventory_update_message():
    """
    Receives a Pub/Sub push message to update product quantities.
    """
    try:
        envelope = request.get_json()
        if not envelope:
            return jsonify({"msg": "No Pub/Sub message received"}), 400

        # Pub/Sub messages are wrapped in an envelope and data is base64 encoded
        message = envelope.get('message')
        if not message or 'data' not in message:
            return jsonify({"msg": "Invalid Pub/Sub message format"}), 400

        # Decode the base64 encoded message data
        data_decoded = base64.b64decode(message['data']).decode('utf-8')
        message_data = json.loads(data_decoded)

        product_id = message_data.get('product_id')
        quantity_sold = message_data.get('quantity_sold')

        if product_id is None or quantity_sold is None:
            print(f"Error: Missing product_id or quantity_sold in message: {message_data}")
            return jsonify({"msg": "Missing product_id or quantity_sold in message"}), 400

        current_app.logger.info(f"Received inventory update for product {product_id}, sold {quantity_sold} units.")

        with current_app.app_context(): # Ensure DB operations are in app context
            try:
                # Fetch the product from the database
                product = db.session.get(Product, product_id)

                if not product:
                    print(f"Error: Product with ID {product_id} not found for update.")
                    return jsonify({"msg": f"Product with ID {product_id} not found"}), 404 # Acknowledge for Pub/Sub, but log error

                # Calculate new quantity
                current_quantity = product.quantity if product.quantity is not None else 0
                new_quantity = current_quantity - quantity_sold
                if new_quantity < 0:
                    new_quantity = 0 # Prevent negative stock
                    print(f"Warning: Quantity for product {product_id} would go negative. Setting to 0.")

                product.quantity = new_quantity
                db.session.commit()
                current_app.logger.info(f"Successfully updated product {product_id} to quantity {new_quantity}.")
                return jsonify({"status": "success", "product_id": product_id, "new_quantity": new_quantity}), 200

            except Exception as e:
                db.session.rollback()
                print(f"Error processing inventory update for product {product_id}: {e}")
                # Returning a non-2xx status code would tell Pub/Sub to retry,
                # but for robustness against transient errors, a 200 OK is often used
                # and internal error handling/logging takes over.
                return jsonify({"status": "error", "message": str(e)}), 500 
            finally:
                db.session.close() # Close session after operation
                
    except Exception as e:
        print(f"General error in Pub/Sub handler: {e}")
        return jsonify({"status": "error", "message": "Invalid request or internal error"}), 400