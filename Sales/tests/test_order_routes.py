import json
from datetime import datetime, timedelta

# Payloads de exemplo para testes de Sales
# IDs fictícios para client, employee, product.
# Em um cenário real com mocks, você controlaria o que os mocks retornam.
new_sale_order_payload_valid = {
    "client_id": 1,
    "employee_id": 101,
    "date": datetime.now(),
    "payment_method": "Credit Card",
    "status": "Pending",
    "items": [
        {"product_id": 10, "quantity": 2, "price": 50.00, "discount": 0.0},
        {"product_id": 20, "quantity": 1, "price": 120.00, "discount": 10.0}
    ]
}

updated_sale_order_payload = {
    "client_id": 2, # Cliente atualizado
    "employee_id": 102, # Funcionário atualizado
    "payment_method": "Bank Transfer",
    "status": "Processing",
    "items": [
        {"product_id": 30, "quantity": 5, "price": 10.00, "discount": 1.0}
    ]
}


class TestSaleOrderRoutes:

    # POST /api/sales/
    def test_create_sale_order_success(self, test_client_sales, authorized_headers_sales):
        response = test_client_sales.post('/api/sales/', headers=authorized_headers_sales, json=new_sale_order_payload_valid)
        assert response.status_code == 201
        data = response.json
        assert data['client_id'] == new_sale_order_payload_valid['client_id']
        assert data['employee_id'] == new_sale_order_payload_valid['employee_id']
        assert data['payment_method'] == new_sale_order_payload_valid['payment_method']
        assert len(data['items']) == len(new_sale_order_payload_valid['items'])
        assert data['items'][0]['product_id'] == new_sale_order_payload_valid['items'][0]['product_id']
        assert 'id' in data
        assert response.headers['Location'].endswith(f"/api/sales/{data['id']}")

    def test_create_sale_order_missing_client_or_employee_id(self, test_client_sales, authorized_headers_sales):
        payload = new_sale_order_payload_valid.copy()
        del payload['client_id'] # Remove client_id
        response = test_client_sales.post('/api/sales/', headers=authorized_headers_sales, json=payload)
        assert response.status_code == 422
        assert "Client ID and Employee ID are required" in response.json['msg']

    def test_create_sale_order_no_items(self, test_client_sales, authorized_headers_sales):
        payload = {k: v for k, v in new_sale_order_payload_valid.items() if k != 'items'}
        payload['items'] = [] # Lista de itens vazia
        response = test_client_sales.post('/api/sales/', headers=authorized_headers_sales, json=payload)
        assert response.status_code == 422
        assert "Items are required and must be a non-empty list" in response.json['msg']

    def test_create_sale_order_item_missing_fields(self, test_client_sales, authorized_headers_sales):
        payload = new_sale_order_payload_valid.copy()
        payload['items'] = [{"product_id": 10, "quantity": 1}] # Falta 'price'
        response = test_client_sales.post('/api/sales/', headers=authorized_headers_sales, json=payload)
        assert response.status_code == 422
        assert "Product ID, quantity, and price are required for each item" in response.json['msg']

    def test_create_sale_order_item_invalid_quantity(self, test_client_sales, authorized_headers_sales):
        payload = new_sale_order_payload_valid.copy()
        payload['items'] = [{"product_id": 10, "quantity": 0, "price": 10.0}] # Quantidade inválida
        response = test_client_sales.post('/api/sales/', headers=authorized_headers_sales, json=payload)
        assert response.status_code == 422
        assert "Item quantity must be a positive integer" in response.json['msg']

    # GET /api/sales/
    def test_get_all_sales_empty(self, test_client_sales, authorized_headers_sales):
        response = test_client_sales.get('/api/sales/', headers=authorized_headers_sales)
        assert response.status_code == 200
        assert response.json == []

    def test_get_all_sales_with_data(self, test_client_sales, authorized_headers_sales, created_sale_order_data):
        # created_sale_order_data já está no BD
        response = test_client_sales.get('/api/sales/', headers=authorized_headers_sales)
        assert response.status_code == 200
        data_list = response.json
        assert len(data_list) == 1
        retrieved_order = data_list[0]
        assert retrieved_order['id'] == created_sale_order_data['id']
        assert retrieved_order['client_id'] == created_sale_order_data['client_id']
        assert len(retrieved_order['items']) == len(created_sale_order_data['items_payload'])

    # GET /api/sales/<sale_id>
    def test_get_sale_by_id_success(self, test_client_sales, authorized_headers_sales, created_sale_order_data):
        sale_id = created_sale_order_data['id']
        response = test_client_sales.get(f'/api/sales/{sale_id}', headers=authorized_headers_sales)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == sale_id
        assert data['client_id'] == created_sale_order_data['client_id']
        assert len(data['items']) == len(created_sale_order_data['items_payload'])

    def test_get_sale_by_id_not_found(self, test_client_sales, authorized_headers_sales):
        response = test_client_sales.get('/api/sales/99999', headers=authorized_headers_sales)
        assert response.status_code == 404
        assert "Sale not found" in response.json['msg']

    # PUT /api/sales/<sale_id>
    def test_update_sale_by_id_success(self, test_client_sales, authorized_headers_sales, created_sale_order_data):
        sale_id = created_sale_order_data['id']
        payload = updated_sale_order_payload.copy()
        payload['date'] = (datetime.now() - timedelta(days=1))

        response = test_client_sales.put(f'/api/sales/{sale_id}', headers=authorized_headers_sales, json=payload)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == sale_id
        assert data['client_id'] == payload['client_id']
        assert data['status'] == payload['status']
        assert len(data['items']) == len(payload['items'])
        assert data['items'][0]['product_id'] == payload['items'][0]['product_id']

    def test_update_sale_by_id_not_found(self, test_client_sales, authorized_headers_sales):
        response = test_client_sales.put('/api/sales/99999', headers=authorized_headers_sales, json=updated_sale_order_payload)
        assert response.status_code == 404
        assert "Sale not found" in response.json['msg']

    def test_update_sale_by_id_invalid_item_in_payload(self, test_client_sales, authorized_headers_sales, created_sale_order_data):
        sale_id = created_sale_order_data['id']
        payload = updated_sale_order_payload.copy()
        payload['items'] = [{"product_id": 30, "quantity": 0, "price": 10.00}] # Quantidade inválida
        
        response = test_client_sales.put(f'/api/sales/{sale_id}', headers=authorized_headers_sales, json=payload)
        assert response.status_code == 422 # Validação de item na atualização
        assert "Item quantity must be a positive integer" in response.json['msg']

    # DELETE /api/sales/<sale_id>
    def test_delete_sale_by_id_success(self, test_client_sales, authorized_headers_sales, created_sale_order_data):
        sale_id = created_sale_order_data['id']
        response_delete = test_client_sales.delete(f'/api/sales/{sale_id}', headers=authorized_headers_sales)
        assert response_delete.status_code == 204

        response_get = test_client_sales.get(f'/api/sales/{sale_id}', headers=authorized_headers_sales)
        assert response_get.status_code == 404 # Deveria ser não encontrado após deletar

    def test_delete_sale_by_id_not_found(self, test_client_sales, authorized_headers_sales):
        response = test_client_sales.delete('/api/sales/99999', headers=authorized_headers_sales)
        assert response.status_code == 404
        assert "Sale not found" in response.json['msg']