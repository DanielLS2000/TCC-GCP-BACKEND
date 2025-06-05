import json

# Payloads de exemplo para testes de Stock
# Os IDs de produto e local de inventário virão das fixtures

class TestStockRoutes:

    # POST /api/inventory/stock/
    def test_create_stock_item_success(self, test_client_instance, authorized_headers, created_product_data, created_inventory_location_data):
        """Testa a criação bem-sucedida de um item de estoque."""
        payload = {
            "product_id": created_product_data['id'],
            "inventory_location_id": created_inventory_location_data['id'],
            "quantity": 50
        }
        response = test_client_instance.post('/api/inventory/stock/', headers=authorized_headers, json=payload)
        assert response.status_code == 201
        data = response.json
        assert data['product_id'] == payload['product_id']
        # Assumindo que Stock.to_dict() retorna 'inventory_location_id'
        assert data['inventory_location_id'] == payload['inventory_location_id']
        assert data['quantity'] == payload['quantity']
        assert 'id' in data
        assert response.headers['Location'].endswith(f"/api/inventory/stock/{data['id']}")

    def test_create_stock_item_missing_fields(self, test_client_instance, authorized_headers, created_product_data):
        """Testa a falha na criação de item de estoque por falta de campos."""
        # product_id, inventory_location_id, quantity são obrigatórios
        incomplete_payload = {"product_id": created_product_data['id']} # Faltando inventory_location_id e quantity
        response = test_client_instance.post('/api/inventory/stock/', headers=authorized_headers, json=incomplete_payload)
        assert response.status_code == 422
        data = response.json
        assert "Insufficient or invalid data provided" in data['msg']
        assert "inventory_location_id" in data['details']
        assert "quantity" in data['details']

    def test_create_stock_item_nonexistent_product(self, test_client_instance, authorized_headers, created_inventory_location_data):
        """Testa a falha na criação com ID de produto inexistente."""
        payload = {
            "product_id": 99999, # ID inexistente
            "inventory_location_id": created_inventory_location_data['id'],
            "quantity": 10
        }
        response = test_client_instance.post('/api/inventory/stock/', headers=authorized_headers, json=payload)
        assert response.status_code == 404 # Rota retorna 404 para product_id não encontrado
        assert "Product not found" in response.json['msg']

    def test_create_stock_item_nonexistent_location(self, test_client_instance, authorized_headers, created_product_data):
        """Testa a falha na criação com ID de local de inventário inexistente."""
        payload = {
            "product_id": created_product_data['id'],
            "inventory_location_id": 99999, # ID inexistente
            "quantity": 10
        }
        response = test_client_instance.post('/api/inventory/stock/', headers=authorized_headers, json=payload)
        assert response.status_code == 404 # Rota retorna 404 para inventory_location_id não encontrado
        assert "Inventory location not found" in response.json['msg']

    # GET /api/inventory/stock/
    def test_get_all_stock_items_empty(self, test_client_instance, authorized_headers):
        """Testa a obtenção de todos os itens de estoque quando não há nenhum."""
        response = test_client_instance.get('/api/inventory/stock/', headers=authorized_headers)
        assert response.status_code == 200
        assert response.json == []

    def test_get_all_stock_items_with_data(self, test_client_instance, authorized_headers, created_stock_data):
        """Testa a obtenção de todos os itens de estoque com dados existentes."""
        # created_stock_data já está no BD via fixture
        response = test_client_instance.get('/api/inventory/stock/', headers=authorized_headers)
        assert response.status_code == 200
        data_list = response.json
        assert len(data_list) == 1
        # Confere se o item criado pela fixture está na lista
        assert any(item['id'] == created_stock_data['id'] and \
                   item['product_id'] == created_stock_data['product_id'] and \
                   item['inventory_location_id'] == created_stock_data['inventory_location_id'] \
                   for item in data_list)


    # GET /api/inventory/stock/<stock_item_id>
    def test_get_stock_item_by_id_success(self, test_client_instance, authorized_headers, created_stock_data):
        """Testa a obtenção bem-sucedida de um item de estoque por ID."""
        stock_item_id = created_stock_data['id']
        response = test_client_instance.get(f'/api/inventory/stock/{stock_item_id}', headers=authorized_headers)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == stock_item_id
        assert data['product_id'] == created_stock_data['product_id']
        assert data['inventory_location_id'] == created_stock_data['inventory_location_id']
        assert data['quantity'] == created_stock_data['quantity']

    def test_get_stock_item_by_id_not_found(self, test_client_instance, authorized_headers):
        """Testa a falha na obtenção de um item de estoque com ID inexistente."""
        response = test_client_instance.get('/api/inventory/stock/99999', headers=authorized_headers)
        assert response.status_code == 404
        assert "Stock item not found" in response.json['msg']

    # PUT /api/inventory/stock/<stock_item_id>
    def test_update_stock_item_success(self, test_client_instance, authorized_headers, created_stock_data, created_product_data, created_inventory_location_data):
        """Testa a atualização bem-sucedida de um item de estoque."""
        stock_item_id = created_stock_data['id']
        
        # Criar um novo produto e local para testar a atualização desses IDs (opcional, mas bom para cobertura)
        # Se não quiser criar novos, pode usar os IDs existentes ou testar apenas a quantidade.
        # Para este exemplo, vamos atualizar apenas a quantidade.
        updated_payload = {
            "quantity": 150
            # "product_id": created_product_data['id'], # Poderia ser um novo ID de produto
            # "inventory_location_id": created_inventory_location_data['id'] # Poderia ser um novo ID de local
        }
        response = test_client_instance.put(f'/api/inventory/stock/{stock_item_id}', headers=authorized_headers, json=updated_payload)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == stock_item_id
        assert data['quantity'] == updated_payload['quantity']
        # Verifica se os outros campos não mudaram se não foram enviados no payload
        assert data['product_id'] == created_stock_data['product_id']
        assert data['inventory_location_id'] == created_stock_data['inventory_location_id']

    def test_update_stock_item_invalid_quantity(self, test_client_instance, authorized_headers, created_stock_data):
        """Testa a falha na atualização com quantidade inválida."""
        stock_item_id = created_stock_data['id']
        invalid_payload = {"quantity": -5} # Quantidade não pode ser negativa
        response = test_client_instance.put(f'/api/inventory/stock/{stock_item_id}', headers=authorized_headers, json=invalid_payload)
        assert response.status_code == 422
        data = response.json
        assert "Invalid data for update" in data['msg']
        assert "Quantity must be a non-negative integer if provided" in data['details']['quantity']

    def test_update_stock_item_not_found(self, test_client_instance, authorized_headers):
        """Testa a falha na atualização de um item de estoque com ID inexistente."""
        response = test_client_instance.put('/api/inventory/stock/99999', headers=authorized_headers, json={"quantity": 10})
        assert response.status_code == 404
        assert "Stock item not found" in response.json['msg']

    def test_update_stock_item_with_nonexistent_product_id(self, test_client_instance, authorized_headers, created_stock_data):
        """Testa a falha na atualização se um product_id inexistente for fornecido."""
        stock_item_id = created_stock_data['id']
        payload = {"product_id": 88888} # ID de produto inexistente
        response = test_client_instance.put(f'/api/inventory/stock/{stock_item_id}', headers=authorized_headers, json=payload)
        assert response.status_code == 404
        assert "Product not found for update" in response.json['msg']


    # DELETE /api/inventory/stock/<stock_item_id>
    def test_delete_stock_item_success(self, test_client_instance, authorized_headers, created_stock_data):
        """Testa a exclusão bem-sucedida de um item de estoque."""
        stock_item_id = created_stock_data['id']
        response_delete = test_client_instance.delete(f'/api/inventory/stock/{stock_item_id}', headers=authorized_headers)
        assert response_delete.status_code == 204

        # Verifica se o item foi realmente excluído
        response_get = test_client_instance.get(f'/api/inventory/stock/{stock_item_id}', headers=authorized_headers)
        assert response_get.status_code == 404

    def test_delete_stock_item_not_found(self, test_client_instance, authorized_headers):
        """Testa a falha na exclusão de um item de estoque com ID inexistente."""
        response = test_client_instance.delete('/api/inventory/stock/99999', headers=authorized_headers)
        assert response.status_code == 404
        assert "Stock item not found" in response.json['msg']