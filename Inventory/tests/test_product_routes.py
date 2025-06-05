import json

# Payloads de exemplo
new_product_payload = {
    "name": "Teclado Mecânico RGB",
    "buy_price": 250.75,
    "desc": "Teclado mecânico com iluminação RGB e switches azuis.",
    "sell_price": 499.90,
    # category_id será pego da fixture created_category_data
    "category_details": "Switches: Blue, Layout: ABNT2",
    "product_image": "http://example.com/keyboard.jpg"
}

updated_product_payload = {
    "name": "Teclado Mecânico Gamer Pro",
    "buy_price": 300.00,
    "sell_price": 599.00,
}


class TestProductRoutes:

    # POST /api/inventory/products/
    def test_create_product_success(self, test_client_instance, authorized_headers, created_category_data):
        payload = {**new_product_payload, "category_id": created_category_data['id']}
        response = test_client_instance.post('/api/inventory/products/', headers=authorized_headers, json=payload)
        assert response.status_code == 201
        data = response.json
        assert data['name'] == payload['name']
        assert data['buy_price'] == payload['buy_price']
        assert data['category_id'] == created_category_data['id']
        assert response.headers['Location'].endswith(f"/api/inventory/products/{data['id']}")

    def test_create_product_missing_fields(self, test_client_instance, authorized_headers):
        # 'name' e 'buy_price' são obrigatórios
        incomplete_payload = {"name": "Apenas Nome"}
        response = test_client_instance.post('/api/inventory/products/', headers=authorized_headers, json=incomplete_payload)
        assert response.status_code == 422
        data = response.json
        assert "Insufficient or invalid data provided" in data['msg']
        assert "buy_price" in data['details']

    def test_create_product_nonexistent_category(self, test_client_instance, authorized_headers):
        payload = {**new_product_payload, "category_id": 9999} # Categoria não existente
        response = test_client_instance.post('/api/inventory/products/', headers=authorized_headers, json=payload)
        assert response.status_code == 404 # Rota retorna 404 para category_id não encontrado
        assert "Category not found" in response.json['msg']


    # GET /api/inventory/products/
    def test_get_all_products_empty(self, test_client_instance, authorized_headers):
        response = test_client_instance.get('/api/inventory/products/', headers=authorized_headers)
        assert response.status_code == 200
        assert response.json == []

    def test_get_all_products_with_data(self, test_client_instance, authorized_headers, created_product_data):
        # created_product_data já está no BD
        response = test_client_instance.get('/api/inventory/products/', headers=authorized_headers)
        assert response.status_code == 200
        data_list = response.json
        assert len(data_list) == 1
        assert data_list[0]['name'] == created_product_data['name']

    # GET /api/inventory/products/<id>
    def test_get_product_by_id_success(self, test_client_instance, authorized_headers, created_product_data):
        product_id = created_product_data['id']
        response = test_client_instance.get(f'/api/inventory/products/{product_id}', headers=authorized_headers)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == product_id
        assert data['name'] == created_product_data['name']

    def test_get_product_by_id_not_found(self, test_client_instance, authorized_headers):
        response = test_client_instance.get('/api/inventory/products/99999', headers=authorized_headers)
        assert response.status_code == 404
        assert "Product not found" in response.json['msg']

    # PUT /api/inventory/products/<id>
    def test_update_product_success(self, test_client_instance, authorized_headers, created_product_data, created_category_data):
        product_id = created_product_data['id']
        # Criar uma nova categoria para testar a atualização da categoria do produto
        other_category_payload = {"name": "Periféricos", "details_model": "Modelo para Periféricos"}
        res_cat = test_client_instance.post('/api/inventory/categories/', headers=authorized_headers, json=other_category_payload)
        assert res_cat.status_code == 201
        other_category_id = res_cat.json['id']

        payload_for_update = {**updated_product_payload, "category_id": other_category_id}
        response = test_client_instance.put(f'/api/inventory/products/{product_id}', headers=authorized_headers, json=payload_for_update)
        assert response.status_code == 200
        data = response.json
        assert data['name'] == payload_for_update['name']
        assert data['buy_price'] == payload_for_update['buy_price']
        assert data['category_id'] == other_category_id

    def test_update_product_not_found(self, test_client_instance, authorized_headers):
        response = test_client_instance.put('/api/inventory/products/99999', headers=authorized_headers, json=updated_product_payload)
        assert response.status_code == 404

    # DELETE /api/inventory/products/<id>
    def test_delete_product_success(self, test_client_instance, authorized_headers, created_product_data):
        product_id = created_product_data['id']
        response = test_client_instance.delete(f'/api/inventory/products/{product_id}', headers=authorized_headers)
        assert response.status_code == 204

        response_get = test_client_instance.get(f'/api/inventory/products/{product_id}', headers=authorized_headers)
        assert response_get.status_code == 404

    # GET /api/inventory/products/search
    def test_search_products_by_name_found(self, test_client_instance, authorized_headers, created_product_data):
        search_term = created_product_data['name'][:5] # Pega uma parte do nome
        response = test_client_instance.get(f'/api/inventory/products/search?name={search_term}', headers=authorized_headers)
        assert response.status_code == 200
        data_list = response.json
        assert len(data_list) >= 1
        assert any(p['id'] == created_product_data['id'] for p in data_list)

    def test_search_products_by_name_not_found(self, test_client_instance, authorized_headers):
        search_term = "ProdutoInexistenteABCXYZ"
        response = test_client_instance.get(f'/api/inventory/products/search?name={search_term}', headers=authorized_headers)
        assert response.status_code == 200
        assert response.json == []

    def test_search_products_no_term(self, test_client_instance, authorized_headers):
        response = test_client_instance.get('/api/inventory/products/search', headers=authorized_headers)
        assert response.status_code == 400 # Rota exige o parâmetro 'name'
        assert "Search term 'name' is required" in response.json['msg']