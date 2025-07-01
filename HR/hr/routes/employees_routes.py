from flask import Blueprint, request, jsonify, Response, url_for
from hr.models import Employee
from hr import db
from flask_jwt_extended import jwt_required

hr_bp = Blueprint('hr', __name__)


# CRUD
@hr_bp.route('/', methods=["GET"])
@jwt_required()
def get_employees() -> tuple[Response, int]:
    try:
        employees = Employee.query.all()
        employees_dict = [employee.to_dict() for employee in employees]
        return jsonify(employees_dict), 200
    except Exception as e:
        return jsonify({"error": "An internal server error occurred", "details_dev": str(e)}), 500


@hr_bp.route('/', methods=["POST"])
@jwt_required()
def create_employee():
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    if not data:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    # Validando os campos obrigatórios
    name = data.get("name")
    if not name:
        return jsonify({
            "msg": "Insufficient or invalid data provided.",
            "details": {"name": "Name is a required field."}
        }), 422

    new_employee = Employee(
        name=name,
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        role=data.get('role'),
        salary=data.get('salary'),
        hiredate=data.get('hiredate'),
        status=data.get('status')
    )

    try:
        db.session.add(new_employee)
        db.session.commit()
        db.session.refresh(new_employee)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save employee to database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    location_uri = url_for('hr.get_employee_by_id', employee_id=new_employee.id, _external=True)

    return jsonify(new_employee.to_dict()), 201, {'Location': location_uri}


@hr_bp.route('/<int:employee_id>', methods=["GET"])
@jwt_required()
def get_employee_by_id(employee_id: int):
    try:
        employee = db.session.get(Employee, employee_id)
    except Exception as e:
        # Swagger 500: ErrorResponse
        return jsonify({"error": "An internal server error occurred while fetching employee", "details_dev": str(e)}), 500

    if employee:
        return jsonify(employee.to_dict()), 200
    else:
        # Swagger 404: ErrorResponse (Funcionário não encontrado)
        return jsonify({"msg": "Employee not found"}), 404


@hr_bp.route('/<int:employee_id>', methods=["PUT"])
@jwt_required()
def update_employee_by_id(employee_id: int): # Nome da função atualizado para clareza
    try:
        employee = db.session.get(Employee, employee_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching employee for update", "details_dev": str(e)}), 500

    if not employee:
        return jsonify({"msg": "Employee not found"}), 404

    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"msg": "Request body is missing or not JSON"}), 400

    # Validando os campos obrigatórios
    if 'name' in data and not data.get('name'):
        return jsonify({
            "msg": "Invalid data for update.",
            "details": {"name": "Name cannot be empty if provided."}
        }), 422

    # Atualizando os dados do funcionário
    employee.name = data.get('name', employee.name)
    employee.email = data.get('email', employee.email)
    employee.phone = data.get('phone', employee.phone)
    employee.address = data.get('address', employee.address)
    employee.role = data.get('role', employee.role)
    employee.salary = data.get('salary', employee.salary)
    employee.hiredate = data.get('hiredate', employee.hiredate)
    employee.status = data.get('status', employee.status)

    employee_data_dict = employee.to_dict()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update employee in database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return jsonify(employee_data_dict), 200


@hr_bp.route('/<int:employee_id>', methods=["DELETE"])
@jwt_required()
def delete_employee_by_id(employee_id: int):
    try:
        employee = db.session.get(Employee, employee_id)
    except Exception as e:
        return jsonify({"error": "An internal server error occurred while fetching employee for deletion", "details_dev": str(e)}), 500

    if not employee:
        return jsonify({"msg": "Employee not found"}), 404

    try:
        db.session.delete(employee)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete employee from database", "details_dev": str(e)}), 500
    finally:
        db.session.close()

    return Response(status=204)