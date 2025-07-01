from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@health_bp.route('/', methods=['GET'])
def root_check():
    return jsonify({"message": "Inventory Service Root"}), 200