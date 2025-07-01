import json
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, Response, url_for, current_app, send_from_directory
from inventory.models import Product, Category
from inventory import db
from flask_jwt_extended import jwt_required
from google.cloud import storage

product_bp = Blueprint('products', __name__)

storage_client = None
if os.environ.get('KUBERNETES_DEPLOYMENT'):
    storage_client = storage.Client()


@product_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    if 'product' not in request.files:
        return jsonify({"msg": "O campo 'product' (enviado como Blob/file) é obrigatório."}), 400

    try:
        product_file = request.files['product']
        product_json_string = product_file.read().decode('utf-8')
        data = json.loads(product_json_string)
    except Exception as e:
        return jsonify({"msg": "Erro ao processar o JSON do produto.", "details_dev": str(e)}), 400

    print("Dados recebidos:", data)
    name = data.get("name")
    buy_price = data.get("price")

    if not name or buy_price is None:
        return jsonify({"msg": "Dados insuficientes (name, buy_price são obrigatórios)."}), 422

    category_id = data.get('category_id')
    if category_id:
        category = db.session.get(Category, category_id)
        if not category:
            return jsonify({"msg": "Categoria não encontrada"}), 404

    product_image_url = None
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            # Generate a unique filename for GCS
            # Use secure_filename to clean the original filename, but prepend a UUID or timestamp
            import uuid
            unique_filename = f"{uuid.uuid4()}_{secure_filename(image_file.filename)}"
            
            try:
                bucket_name = current_app.config['GCS_BUCKET_NAME']
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(unique_filename)
                
                # Upload the file
                blob.upload_from_file(image_file, content_type=image_file.content_type)
                
                # Make the blob publicly accessible if desired (for direct serving)
                # Alternatively, use signed URLs for private access control
                # blob.make_public() # Consider if truly needed, usually signed URLs or CDN is better

                product_image_url = blob.public_url # Or blob.media_link, depending on access setup

            except Exception as e:
                return jsonify({"error": f"Falha ao fazer upload da imagem para GCS: {str(e)}"}), 500


    new_product = Product(
        name=name,
        buy_price=buy_price,
        desc=data.get('desc'),
        sell_price=data.get('sell_price'),
        category_id=category_id,
        category_details=data.get('category_details'),
        product_image=product_image_url # Store the GCS URL
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        db.session.refresh(new_product)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Falha ao salvar o produto no banco de dados", "details_dev": str(e)}), 500
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

    # Handle image update for GCS similar to creation, if 'image' is in request.files
    product_image_url = product.product_image # Keep existing if not updated
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            import uuid
            unique_filename = f"{uuid.uuid4()}_{secure_filename(image_file.filename)}"
            try:
                bucket_name = current_app.config['GCS_BUCKET_NAME']
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(unique_filename)
                blob.upload_from_file(image_file, content_type=image_file.content_type)
                # blob.make_public() # Uncomment if public access is desired
                product_image_url = blob.public_url
            except Exception as e:
                return jsonify({"error": f"Falha ao fazer upload da imagem atualizada para GCS: {str(e)}"}), 500
    elif 'product_image' in data and data.get('product_image') is None:
        # If product_image is explicitly set to null, delete the old one from GCS
        if product.product_image:
            try:
                bucket_name = current_app.config['GCS_BUCKET_NAME']
                bucket = storage_client.bucket(bucket_name)
                # Extract blob name from URL (simple example, may need robust parsing)
                blob_name = os.path.basename(product.product_image)
                blob = bucket.blob(blob_name)
                blob.delete()
                product_image_url = None # Set to None after deletion
            except Exception as e:
                print(f"Warning: Failed to delete old image from GCS: {e}") # Log, but don't fail update
                product_image_url = None # Ensure URL is cleared even if delete fails

    try:
        data = request.get_json()
    except Exception as e:
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
    # Use the new product_image_url if an image was uploaded/deleted, otherwise keep existing
    product.product_image = product_image_url


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
    
    # Delete image from GCS when product is deleted
    if product.product_image:
        try:
            bucket_name = current_app.config['GCS_BUCKET_NAME']
            bucket = storage_client.bucket(bucket_name)
            # Extract blob name from URL (simple example, may need robust parsing)
            blob_name = os.path.basename(product.product_image)
            blob = bucket.blob(blob_name)
            blob.delete()
        except Exception as e:
            print(f"Warning: Failed to delete image from GCS during product deletion: {e}") # Log, but don't stop product deletion

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