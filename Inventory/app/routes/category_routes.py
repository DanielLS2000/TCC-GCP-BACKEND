from flask import Blueprint, request, jsonify
from app.models import Category
from app import db

category_bp = Blueprint('category', __name__)

@category_bp.route('/', methods=['POST'])
def create_category():
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando se a categoria pai existe
    parent_category=data.get("parent_category")
    if parent_category is not None and not Category.query.filter_by(id=parent_category).first():
        return jsonify({"error": "Category not found"}), 404

    # Verificando se os dados necessarios estão presentes
    name = data.get("name")
    details_model = data.get("details_model")
    if name is not None and details_model is not None:
        new_category = Category(
            name=data["name"],
            details_model=data["details_model"],
            parent_category=data.get("parent_category")
        )

        db.session.add(new_category)
        db.session.commit()
        db.session.refresh(new_category)
        
        return jsonify(data), 201
    else:
        return jsonify({"error": "Insuficient data"}), 406

@category_bp.route('/', methods=['GET'])
def read_category():
    categories = Category.query.all()
    categories_dict = [category.to_dict() for category in categories]

    return jsonify(categories_dict), 200

@category_bp.route('/<int:category_id>/update', methods=['PUT'])
def update_category(category_id):
    data = request.get_json()

    # Verificação do Pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando se a categoria existe
    category = Category.query.filter_by(id=category_id).first()
    if not category:
        return jsonify({"message": "Categoria não encontrada"}), 404
    
    # Verificando se a categoria pai existe
    parent_category=data.get("parent_category")
    if parent_category is not None and not Category.query.filter_by(id=parent_category).first():
        return jsonify({"error": "Category not found"}), 404

    # Verificando se os dados necessarios estão presentes
    name = data.get("name")
    details_model = data.get("details_model")
    
    if name is not None and details_model is not None:
        category.name=data["name"]
        category.details_model=data["details_model"]
        category.parent_category=data.get("parent_category")

        db.session.commit()
        
        return jsonify(data), 200
    else:
        return jsonify({"error": "Insuficient data"}), 406

@category_bp.route('/<int:category_id>/delete', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    
    if not category:
        return jsonify({"message": "Categoria não encontrada"}), 404
    
    db.session.delete(category)
    
    db.session.commit()

    return jsonify(200)