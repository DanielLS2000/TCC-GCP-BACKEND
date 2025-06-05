# Inventory/tests/test_inventory_location_routes.py
import json

new_location_payload = {"name": "Depósito Satélite", "address": "789 Av. Logística"}
updated_location_payload = {"name": "Depósito Central Atualizado", "address": "125 Rua Principal Modificada"}

class TestInventoryLocationRoutes:

    # POST /api/inventory/locations/
    def test_create_location_success(self, test_client_instance, authorized_headers):
        response = test_client_instance.post('/api/inventory/locations/', headers=authorized_headers, json=new_location_payload)
        assert response.status_code == 201
        data = response.json
        assert data['name'] == new_location_payload['name']
        # Lembre-se do typo no to_dict() original do modelo Inventory: 'adress'.
        # Se corrigido para 'address' no to_dict():
        assert data['address'] == new_location_payload['address']
        # Se não corrigido, a asserção seria data['adress']
        assert 'id' in data

    def test_create_location_missing_fields(self, test_client_instance, authorized_headers):
        incomplete_payload = {"name": "Apenas Nome"} # address faltando
        response = test_client_instance.post('/api/inventory/locations/', headers=authorized_headers, json=incomplete_payload)
        assert response.status_code == 422
        assert "Address is required" in response.json['details']['address']

    # GET /api/inventory/locations/
    def test_get_all_locations(self, test_client_instance, authorized_headers, created_inventory_location_data):
        response = test_client_instance.get('/api/inventory/locations/', headers=authorized_headers)
        assert response.status_code == 200
        assert len(response.json) >= 1
        assert response.json[0]['name'] == created_inventory_location_data['name']


    # GET /api/inventory/locations/<id>
    def test_get_location_by_id(self, test_client_instance, authorized_headers, created_inventory_location_data):
        location_id = created_inventory_location_data['id']
        response = test_client_instance.get(f'/api/inventory/locations/{location_id}', headers=authorized_headers)
        assert response.status_code == 200
        assert response.json['id'] == location_id

    # PUT /api/inventory/locations/<id>
    def test_update_location(self, test_client_instance, authorized_headers, created_inventory_location_data):
        location_id = created_inventory_location_data['id']
        response = test_client_instance.put(f'/api/inventory/locations/{location_id}', headers=authorized_headers, json=updated_location_payload)
        assert response.status_code == 200
        assert response.json['name'] == updated_location_payload['name']

    # DELETE /api/inventory/locations/<id>
    def test_delete_location(self, test_client_instance, authorized_headers, created_inventory_location_data):
        location_id = created_inventory_location_data['id']
        response = test_client_instance.delete(f'/api/inventory/locations/{location_id}', headers=authorized_headers)
        assert response.status_code == 204