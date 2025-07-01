import sys
import os
import pytest
from flask_jwt_extended import create_access_token
from datetime import datetime

# Adiciona o diretório pai (Sales/) ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports da sua aplicação Sales
from sales import create_app as sales_create_app, db as sales_db_instance
from sales.models import SaleOrder as SaleOrderModel_Class, SaleItem as SaleItemModel_Class

@pytest.fixture(scope='session')
def test_app_instance_sales():
    """Cria uma instância do Flask app para a sessão de teste do Sales."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-jwt-secret-key-sales",
        "SERVER_NAME": "localhost.sales.test",
    }
    # Assume que sales_create_app foi modificada para aceitar config_overrides
    app = sales_create_app(config_overrides=test_config)
    yield app

@pytest.fixture(scope='function')
def test_client_sales(test_app_instance_sales):
    """Fornece um cliente de teste para o app Flask do Sales, garantindo um BD limpo."""
    with test_app_instance_sales.test_client() as client:
        with test_app_instance_sales.app_context():
            sales_db_instance.drop_all()
            sales_db_instance.create_all()
        yield client

@pytest.fixture(scope='function')
def jwt_access_token_sales(test_app_instance_sales):
    """Gera um token de acesso JWT para um usuário autenticado (dummy)."""
    with test_app_instance_sales.app_context():
        token = create_access_token(identity="test_sales_user@example.com")
    return token

@pytest.fixture(scope='function')
def authorized_headers_sales(jwt_access_token_sales):
    """Fornece cabeçalhos de autorização para requisições autenticadas."""
    return {
        "Authorization": f"Bearer {jwt_access_token_sales}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

# Fixture para dados de uma venda pré-existente
@pytest.fixture(scope='function')
def created_sale_order_data(test_app_instance_sales):
    """
    Cria uma SaleOrder e seus SaleItems no BD e retorna seus dados como um dicionário.
    Usa IDs fictícios para client, employee e product, pois não estamos mockando os serviços externos aqui.
    """
    order_payload = {
        "client_id": 1,
        "employee_id": 101,
        "date": datetime.now(),
        "payment_method": "Credit Card",
        "status": "Pending"
    }
    items_payload = [
        {"product_id": 10, "quantity": 2, "price": 50.00, "discount": 0.0},
        {"product_id": 20, "quantity": 1, "price": 120.00, "discount": 10.0}
    ]

    with test_app_instance_sales.app_context():
        new_sale_order = SaleOrderModel_Class(
            client_id=order_payload['client_id'],
            employee_id=order_payload['employee_id'],
            date=order_payload['date'],
            payment_method=order_payload['payment_method'],
            status=order_payload['status']
        )
        sales_db_instance.session.add(new_sale_order)
        sales_db_instance.session.commit() # Commit para obter o ID da SaleOrder

        sale_items_created = []
        for item_data in items_payload:
            sale_item = SaleItemModel_Class(
                sale_order_id=new_sale_order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                price=item_data['price'],
                discount=item_data['discount']
            )
            sales_db_instance.session.add(sale_item)
            sale_items_created.append({
                "id": None, # O ID será preenchido após o commit
                "product_id": sale_item.product_id,
                "quantity": sale_item.quantity,
                "price": sale_item.price,
                "discount": sale_item.discount,
                "sale_order_id": new_sale_order.id
            })
        sales_db_instance.session.commit() # Commit para salvar os SaleItems e obter seus IDs

        # Atualiza os IDs dos itens criados (opcional, mas bom para ter dados completos)
        # Re-consultar os itens para obter seus IDs reais se necessário para a asserção.
        # Para simplificar, a fixture retorna o ID da ordem e os dados dos itens como foram enviados.

        # Retorna os dados da ordem principal e os itens como foram definidos
        # O ID da ordem é o mais importante para os testes de GET/PUT/DELETE por ID.
        return {
            "id": new_sale_order.id,
            "client_id": new_sale_order.client_id,
            "employee_id": new_sale_order.employee_id,
            "date": new_sale_order.date.isoformat(),
            "payment_method": new_sale_order.payment_method,
            "status": new_sale_order.status,
            "items_payload": items_payload # Retorna o payload original dos itens para referência
        }