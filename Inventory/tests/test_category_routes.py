# Inventory/tests/test_category_routes.py
import json

# Payloads de teste
new_category_payload = {
    "name": "Livros",
    "details_model": "Informações sobre ISBN, autor, editora"
}
updated_category_payload = {
    "name": "Livros Infantis",
    "details_model": "Faixa etária, ilustrador"
}

class TestCategoryRoutes:

    # POST /api/inventory/categories/
    def test_create_category_success(self, test_client_instance, authorized_headers):
        response = test_client_instance.post('/api/inventory/categories/', headers=authorized_headers, json=new_category_payload)
        assert response.status_code == 201
        data = response.json
        assert data['name'] == new_category_payload['name']
        assert data['details_model'] == new_category_payload['details_model']
        assert 'id' in data
        assert response.headers['Location'].endswith(f"/api/inventory/categories/{data['id']}")

    def test_create_category_missing_fields(self, test_client_instance, authorized_headers):
        incomplete_payload = {"name": "Apenas Nome"} # details_model faltando
        response = test_client_instance.post('/api/inventory/categories/', headers=authorized_headers, json=incomplete_payload)
        assert response.status_code == 422
        data = response.json
        assert "Insufficient or invalid data provided" in data['msg']
        assert "Details_model is required." in data['details']['details_model']

    def test_create_category_with_parent(self, test_client_instance, authorized_headers, created_category_data):
        """Testa a criação de uma subcategoria."""
        sub_category_payload = {
            "name": "Ficção Científica",
            "details_model": "Subgênero de livros",
            "parent_category_id": created_category_data['id']
        }
        response = test_client_instance.post('/api/inventory/categories/', headers=authorized_headers, json=sub_category_payload)
        assert response.status_code == 201
        data = response.json
        assert data['name'] == sub_category_payload['name']
        # No modelo Category, 'parent_category_id' é o campo, e 'to_dict' retorna 'parent_category' com o ID.
        assert data['parent_category'] == created_category_data['id']


    def test_create_category_with_non_existent_parent(self, test_client_instance, authorized_headers):
        payload = {**new_category_payload, "parent_category_id": 9999}
        response = test_client_instance.post('/api/inventory/categories/', headers=authorized_headers, json=payload)
        assert response.status_code == 404 # Rota retorna 404 se pai não existe
        assert "Parent category not found" in response.json['msg']

    # GET /api/inventory/categories/
    def test_get_all_categories_empty(self, test_client_instance, authorized_headers):
        response = test_client_instance.get('/api/inventory/categories/', headers=authorized_headers)
        assert response.status_code == 200
        assert response.json == []

    def test_get_all_categories_with_data(self, test_client_instance, authorized_headers, created_category_data):
        # created_category_data já está no DB
        response = test_client_instance.get('/api/inventory/categories/', headers=authorized_headers)
        assert response.status_code == 200
        data = response.json
        assert len(data) == 1
        assert data[0]['name'] == created_category_data['name']

    # GET /api/inventory/categories/<id>
    def test_get_category_by_id_success(self, test_client_instance, authorized_headers, created_category_data):
        category_id = created_category_data['id']
        response = test_client_instance.get(f'/api/inventory/categories/{category_id}', headers=authorized_headers)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == category_id
        assert data['name'] == created_category_data['name']

    def test_get_category_by_id_not_found(self, test_client_instance, authorized_headers):
        response = test_client_instance.get('/api/inventory/categories/99999', headers=authorized_headers)
        assert response.status_code == 404
        assert "Category not found" in response.json['msg']

    # PUT /api/inventory/categories/<id>
    def test_update_category_success(self, test_client_instance, authorized_headers, created_category_data):
        category_id = created_category_data['id']
        response = test_client_instance.put(f'/api/inventory/categories/{category_id}', headers=authorized_headers, json=updated_category_payload)
        assert response.status_code == 200
        data = response.json
        assert data['name'] == updated_category_payload['name']
        assert data['details_model'] == updated_category_payload['details_model']

    def test_update_category_not_found(self, test_client_instance, authorized_headers):
        response = test_client_instance.put('/api/inventory/categories/99999', headers=authorized_headers, json=updated_category_payload)
        assert response.status_code == 404

    # DELETE /api/inventory/categories/<id>
    def test_delete_category_success(self, test_client_instance, authorized_headers, created_category_data):
        category_id = created_category_data['id']
        response = test_client_instance.delete(f'/api/inventory/categories/{category_id}', headers=authorized_headers)
        assert response.status_code == 204

        # Verifica se foi deletado
        response_get = test_client_instance.get(f'/api/inventory/categories/{category_id}', headers=authorized_headers)
        assert response_get.status_code == 404

    def test_delete_category_not_found(self, test_client_instance, authorized_headers):
        response = test_client_instance.delete('/api/inventory/categories/99999', headers=authorized_headers)
        assert response.status_code == 404