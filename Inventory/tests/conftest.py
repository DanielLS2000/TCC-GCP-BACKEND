# Inventory/tests/conftest.py
import sys
import os
import pytest
from flask_jwt_extended import create_access_token

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports do módulo Inventory
from inventory import create_app as inventory_create_app, db as inventory_db_instance
from inventory.models import (
    Category as CategoryModel_Class,
    Inventory as InventoryLocationModel_Class, # Note: O modelo é 'Inventory' para locais
    Product as ProductModel_Class,
    Stock as StockModel_Class
)

@pytest.fixture(scope='session')
def test_app_instance():
    """Cria uma instância do Flask app para a sessão de teste."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-jwt-secret-key-inventory",
        "SERVER_NAME": "localhost.test", # Para url_for externo
    }
    app = inventory_create_app(config_overrides=test_config)
    yield app

@pytest.fixture(scope='function')
def test_client_instance(test_app_instance):
    """Fornece um cliente de teste Flask, garantindo um DB limpo para cada teste."""
    with test_app_instance.test_client() as client:
        with test_app_instance.app_context():
            inventory_db_instance.drop_all()
            inventory_db_instance.create_all()
        yield client

@pytest.fixture(scope='function')
def jwt_access_token(test_app_instance):
    """Gera um token de acesso JWT."""
    with test_app_instance.app_context():
        token = create_access_token(identity="test_inventory_user@example.com")
    return token

@pytest.fixture(scope='function')
def authorized_headers(jwt_access_token):
    """Fornece cabeçalhos de autorização para requisições autenticadas."""
    return {
        "Authorization": f"Bearer {jwt_access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

# --- Fixtures de Dados Pré-existentes ---
# Retornam dicionários para evitar DetachedInstanceError

@pytest.fixture(scope='function')
def created_category_data(test_app_instance):
    """Cria uma categoria no DB e retorna seus dados como um dicionário."""
    payload = {"name": "Eletrônicos", "details_model": "Modelo padrão para eletrônicos"}
    with test_app_instance.app_context():
        category = CategoryModel_Class(**payload)
        inventory_db_instance.session.add(category)
        inventory_db_instance.session.commit()
        return {
            "id": category.id,
            "name": category.name,
            "details_model": category.details_model,
            "parent_category": category.parent_category_id # parent_category_id no modelo é o campo correto
        }

@pytest.fixture(scope='function')
def created_inventory_location_data(test_app_instance):
    """Cria um local de inventário (modelo Inventory) no DB e retorna seus dados."""
    payload = {"name": "Armazém Principal", "address": "123 Rua do Estoque"}
    with test_app_instance.app_context():
        location = InventoryLocationModel_Class(**payload) # Usando o alias do modelo
        inventory_db_instance.session.add(location)
        inventory_db_instance.session.commit()
        # O modelo Inventory tem o campo 'address'. O to_dict() original tinha 'self.adress'.
        # A fixture usa o nome correto do campo do modelo.
        return {
            "id": location.id,
            "name": location.name,
            "address": location.address
        }

@pytest.fixture(scope='function')
def created_product_data(test_app_instance, created_category_data):
    """Cria um produto (associado a uma categoria existente) e retorna seus dados."""
    product_payload = {
        "name": "Smartphone X",
        "buy_price": 1500.00,
        "desc": "Smartphone de última geração",
        "sell_price": 2500.00,
        "category_id": created_category_data['id'], # Usa o ID da categoria criada pela fixture
        "category_details": "RAM: 8GB, Tela: OLED 6.5",
        "product_image": "http://example.com/smartphone_x.jpg"
    }
    with test_app_instance.app_context():
        product = ProductModel_Class(**product_payload)
        inventory_db_instance.session.add(product)
        inventory_db_instance.session.commit()
        data_to_return = {
            "id": product.id,
            "name": product.name,
            "buy_price": product.buy_price,
            "desc": product.desc,
            "sell_price": product.sell_price,
            "category_id": product.category_id,
            "category_details": product.category_details,
            "product_image": product.product_image
        }
    return data_to_return

@pytest.fixture(scope='function')
def created_stock_data(test_app_instance, created_product_data, created_inventory_location_data):
    """Cria um item de estoque no DB e retorna seus dados."""
    payload = {
        "product_id": created_product_data['id'],
        "inventory_location_id": created_inventory_location_data['id'],
        "quantity": 100
    }
    with test_app_instance.app_context():
        stock_item = StockModel_Class(**payload)
        inventory_db_instance.session.add(stock_item)
        inventory_db_instance.session.commit()
        # O modelo Stock tem 'inventory_location_id'. O to_dict() original tinha 'inventory_id'.
        # A fixture usa o nome correto do campo do modelo para product_id e inventory_location_id.
        return {
            "id": stock_item.id,
            "product_id": stock_item.product_id,
            "inventory_location_id": stock_item.inventory_location_id,
            "quantity": stock_item.quantity
        }