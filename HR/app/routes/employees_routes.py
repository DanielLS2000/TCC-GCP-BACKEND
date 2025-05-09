from flask import Blueprint, request, jsonify, Response
from app.models import Employee
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

hr_bp = Blueprint('hr', __name__)

#CRUD
@hr_bp.route('/employees', methods=["GET"])
@jwt_required()
def get_employees() -> tuple[Response, int]:
    try:
        employees = Employee.query.all()
        employees_dict = [employee.to_dict() for employee in employees]

        return jsonify(employees_dict), 200
    except Exception as e:
        return jsonify({"error": "Failed to connect to Database"}), 500

@hr_bp.route('/employees', methods=["POST"])
@jwt_required()
def create_employee():
    data = request.get_json()

    # Verificando o pacote recebido
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format"}), 400

    # Verificando os dados necessarios
    name = data.get("name")
    if name is not None:
        new_employee = Employee(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            role=data.get('role'),
            salary=data.get('salary'),
            status=data.get('status')
        )

        try:
            db.session.add(new_employee)
            db.session.commit()
            db.session.refresh(new_employee)
        except Exception as e:
            return jsonify({"error": "Failed to connect to Database"}), 500

        return jsonify(data), 201
    else:
        return jsonify({"error": "Insuficient data"}), 406

@hr_bp.route('/employees/<int:employee_id>', methods=["GET"])
@jwt_required()
def detail_employee(employee_id):
    try:
        employee = Employee.query.filter_by(id=employee_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500
    if employee:
        return jsonify(employee.to_dict()), 200
    else:
        return jsonify({"error": "Employee not found"}), 404

@hr_bp.route('/employees/<int:employee_id>', methods=["PUT"])
@jwt_required()
def update_employee(employee_id):
    try:
        employee = Employee.query.filter_by(id=employee_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500

    if employee:
        data = request.get_json()
        # Verificando o pacote recebido
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON format"}), 400

        # Atualizando os dados do funcionário
        employee.name = data.get('name', employee.name)
        employee.email = data.get('email', employee.email)
        employee.phone = data.get('phone', employee.phone)
        employee.address = data.get('address', employee.address)
        employee.role = data.get('role', employee.role)
        employee.salary = data.get('salary', employee.salary)
        employee.hiredate = data.get('hiredate', employee.hiredate)
        employee.status = data.get('status', employee.status)

        db.session.commit()

        return jsonify(employee.to_dict()), 200
    else:
        return jsonify({"error": "Employee not found"}), 404

@hr_bp.route('/employees/<int:employee_id>', methods=["DELETE"])
@jwt_required()
def remove_employee(employee_id):
    try:
        employee = Employee.query.filter_by(id=employee_id).first()
    except:
        return jsonify({"error": "Failed to connect to Database"}), 500
    
    if employee:
        db.session.delete(employee)
        db.session.commit()
        return jsonify({"message": "Employee deleted"}), 200
    else:
        return jsonify({"error": "Employee not found"}), 404