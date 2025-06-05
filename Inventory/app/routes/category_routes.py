from flask import Blueprint, request, jsonify, Response, url_for
from app.models import Category
from app import db
from flask_jwt_extended import jwt_required

category_bp = Blueprint('category', __name__)


@category_bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    name = data.get("name")
    details_model = data.get("details_model")
    parent_category_id = data.get("parent_category_id")

    if not name or not details_model:
        missing_fields = []
        if not name: missing_fields.append('name')
        if not details_model: missing_fields.append('details_model')
        return jsonify({
            "msg": "Insufficient or invalid data provided.",
            "details": {field: f"{field.capitalize()} is required." for field in missing_fields}
        }), 422

    if parent_category_id is not None:
        parent_category = db.session.get(Category, parent_category_id)
        if not parent_category:
            return jsonify({"msg": "Parent category not found"}), 404

    new_category = Category(
        name=name,
        details_model=details_model,
        parent_category_id=parent_category_id
    )

    try:
        db.session.add(new_category)
        db.session.commit()
        db.session.refresh(new_category)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save category to database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    location_uri = url_for('category.get_category_by_id', category_id=new_category.id, _external=True)

    return jsonify(new_category.to_dict()), 201, {'Location': location_uri}


@category_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_categories():
    try:
        categories = Category.query.all()
        categories_dict = [category.to_dict() for category in categories]
        return jsonify(categories_dict), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500

@category_bp.route('/<int:category_id>', methods=['GET'])
@jwt_required()
def get_category_by_id(category_id: int):
    try:
        category = db.session.get(Category, category_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching category", "details_dev": str(e)}), 500

    if category:
        return jsonify(category.to_dict()), 200
    else:
        return jsonify({"msg": "Category not found"}), 404


@category_bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category_by_id(category_id: int):
    try:
        category = db.session.get(Category, category_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching category for update", "details_dev": str(e)}), 500

    if not category:
        return jsonify({"msg": "Category not found"}), 404

    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400


    name = data.get("name")
    details_model = data.get("details_model")
    parent_category_id = data.get("parent_category_id")

    # Se os campos obrigatórios estiverem presentes no payload, eles não devem ser vazios
    if 'name' in data and not name:
        return jsonify({"msg": "Invalid data for update.", "details": {"name": "Name cannot be empty if provided."}}), 422
    if 'details_model' in data and not details_model:
        return jsonify({"msg": "Invalid data for update.", "details": {"details_model": "Details model cannot be empty if provided."}}), 422

    if parent_category_id is not None:
        parent_category = db.session.get(Category, parent_category_id)
        if not parent_category:
            # Swagger 404: ErrorResponse (Categoria pai não encontrada)
            return jsonify({"msg": "Parent category not found"}), 404

    category.name = data.get('name', category.name)
    category.details_model = data.get('details_model', category.details_model)
    if "parent_category_id" in data:
        category.parent_category_id = parent_category_id
    
    try:
        db.session.commit()
        category_data_dict = category.to_dict()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update category in database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return jsonify(category_data_dict), 200


@category_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category_by_id(category_id: int):
    try:
        category = db.session.get(Category, category_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching category for deletion", "details_dev": str(e)}), 500
    
    if not category:
        return jsonify({"msg": "Category not found"}), 404
    
    try:
        db.session.delete(category)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete category from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return Response(status=204)