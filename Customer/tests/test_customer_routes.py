import json

# Pytest will automatically discover and use fixtures from conftest.py.

# Define standard payloads for creating and updating customers to keep tests DRY.
new_customer_payload = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "123-456-7890",
    "address": "123 Main St, Anytown, USA"
}

updated_customer_payload = {
    "name": "Jane Doer",
    "email": "jane.doer@example.com",
    "phone": "987-654-3210",
    "address": "456 Oak Ave, Otherville, USA"
}

class TestCustomerRoutes:

    # --- Test POST /api/customers/ ---
    def test_create_customer_success(self, test_client_instance, authorized_headers):
        """Test successful creation of a new customer."""
        response = test_client_instance.post('/api/customers/', headers=authorized_headers, json=new_customer_payload)
        assert response.status_code == 201
        data = response.json
        assert data['name'] == new_customer_payload['name']
        assert data['email'] == new_customer_payload['email']
        assert data['phone'] == new_customer_payload['phone']
        assert data['address'] == new_customer_payload['address']
        assert 'id' in data
        assert response.headers['Location'].endswith(f"/api/customers/{data['id']}") #

    def test_create_customer_missing_fields(self, test_client_instance, authorized_headers):
        """Test customer creation failure due to missing required fields."""
        incomplete_payload = {
            "name": "Only Name Field",
            "email": "only.name@example.com"
            # 'phone' and 'address' are missing
        }
        response = test_client_instance.post('/api/customers/', headers=authorized_headers, json=incomplete_payload)
        assert response.status_code == 422 #
        data = response.json
        assert "Insufficient or invalid data provided" in data['msg'] #
        assert "phone" in data['details'] and data['details']['phone'] == "Phone is required." #
        assert "address" in data['details'] and data['details']['address'] == "Address is required." #

    def test_create_customer_no_payload(self, test_client_instance, authorized_headers):
        """Test customer creation failure when no JSON payload is sent."""
        response = test_client_instance.post('/api/customers/', headers=authorized_headers, json=None) # No json data
        print("HERE")
        print(response.json)  # Debugging line to see the response content
        assert response.status_code == 400 #
        assert "The browser (or proxy) sent a request that this server could not understand." in response.json['msg'] #

    def test_create_customer_invalid_json_structure(self, test_client_instance, authorized_headers):
        """Test customer creation failure with malformed JSON."""
        custom_headers = authorized_headers.copy()
        custom_headers['Content-Type'] = 'application/json' # Ensure Flask tries to parse it
        response = test_client_instance.post('/api/customers/', headers=custom_headers, data="{this is not valid json")
        assert response.status_code == 400 # Flask's default for unparseable JSON
        assert "The browser (or proxy) sent a request that this server could not understand." in response.json.get('msg', '') or "Failed to decode JSON" in response.json.get('message', '')

    # --- Test GET /api/customers/ ---
    def test_get_all_customers_empty(self, test_client_instance, authorized_headers):
        """Test retrieving all customers when the database is empty."""
        response = test_client_instance.get('/api/customers/', headers=authorized_headers)
        assert response.status_code == 200
        assert response.json == []

    def test_get_all_customers_with_data(self, test_client_instance, authorized_headers, pre_existing_customer_data):
        """Test retrieving all customers when there's data."""
        # pre_existing_customer_data is already in DB via the fixture.
        # Create a second customer via API to test retrieval of multiple items.
        response_post = test_client_instance.post('/api/customers/', headers=authorized_headers, json=new_customer_payload)
        assert response_post.status_code == 201 # Ensure creation was successful

        response_get_all = test_client_instance.get('/api/customers/', headers=authorized_headers)
        assert response_get_all.status_code == 200
        data = response_get_all.json
        assert len(data) == 2
        # Verify that the names of the created customers are in the response list
        retrieved_customer_names = {c['name'] for c in data}
        assert pre_existing_customer_data['name'] in retrieved_customer_names
        assert new_customer_payload['name'] in retrieved_customer_names

    # --- Test GET /api/customers/<customer_id> ---
    def test_get_customer_by_id_success(self, test_client_instance, authorized_headers, pre_existing_customer_data):
        """Test successful retrieval of a customer by their ID."""
        customer_id = pre_existing_customer_data['id']
        response = test_client_instance.get(f'/api/customers/{customer_id}', headers=authorized_headers)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == customer_id
        assert data['name'] == pre_existing_customer_data['name']
        assert data['email'] == pre_existing_customer_data['email']
        assert data['phone'] == pre_existing_customer_data['phone']
        assert data['address'] == pre_existing_customer_data['address']

    def test_get_customer_by_id_not_found(self, test_client_instance, authorized_headers):
        """Test retrieval of a non-existent customer by ID."""
        non_existent_id = 99999
        response = test_client_instance.get(f'/api/customers/{non_existent_id}', headers=authorized_headers)
        assert response.status_code == 404 #
        assert "Customer not found" in response.json['msg'] #

    # --- Test PUT /api/customers/<customer_id> ---
    def test_update_customer_success(self, test_client_instance, authorized_headers, pre_existing_customer_data):
        """Test successful update of an existing customer."""
        customer_id = pre_existing_customer_data['id']
        response = test_client_instance.put(f'/api/customers/{customer_id}', headers=authorized_headers, json=updated_customer_payload)
        assert response.status_code == 200
        data = response.json
        assert data['id'] == customer_id
        assert data['name'] == updated_customer_payload['name']
        assert data['email'] == updated_customer_payload['email']
        assert data['phone'] == updated_customer_payload['phone']
        assert data['address'] == updated_customer_payload['address']

    def test_update_customer_partial_update(self, test_client_instance, authorized_headers, pre_existing_customer_data):
        """Test partial update of an existing customer (e.g., only name)."""
        customer_id = pre_existing_customer_data['id']
        partial_payload = {"name": "Super Updated Name"}
        response = test_client_instance.put(f'/api/customers/{customer_id}', headers=authorized_headers, json=partial_payload)
        assert response.status_code == 200
        data = response.json
        assert data['name'] == partial_payload['name']
        # Ensure other fields remain unchanged from pre_existing_customer_data
        assert data['email'] == pre_existing_customer_data['email']
        assert data['phone'] == pre_existing_customer_data['phone']

    def test_update_customer_empty_name_validation(self, test_client_instance, authorized_headers, pre_existing_customer_data):
        """Test update failure if 'name' field is provided but empty."""
        customer_id = pre_existing_customer_data['id']
        payload_with_empty_name = {"name": "", "email": "still.valid@example.com"}
        response = test_client_instance.put(f'/api/customers/{customer_id}', headers=authorized_headers, json=payload_with_empty_name)
        assert response.status_code == 422 #
        data = response.json
        assert "Invalid data for update" in data['msg'] #
        assert "Name cannot be empty" in data['details']['name'] #

    def test_update_customer_not_found(self, test_client_instance, authorized_headers):
        """Test update failure for a non-existent customer."""
        non_existent_id = 99999
        response = test_client_instance.put(f'/api/customers/{non_existent_id}', headers=authorized_headers, json=updated_customer_payload)
        assert response.status_code == 404 #
        assert "Customer not found" in response.json['msg'] #

    def test_update_customer_no_payload(self, test_client_instance, authorized_headers, pre_existing_customer_data):
        """Test update failure when no JSON payload is sent."""
        customer_id = pre_existing_customer_data['id']
        response = test_client_instance.put(f'/api/customers/{customer_id}', headers=authorized_headers) # No json data
        assert response.status_code == 400 #
        assert "Request body is missing or not JSON" in response.json['msg']  or "The browser (or proxy) sent a request that this server could not understand." in response.json['msg']#

    # --- Test DELETE /api/customers/<customer_id> ---
    def test_delete_customer_success(self, test_client_instance, authorized_headers, pre_existing_customer_data):
        """Test successful deletion of an existing customer."""
        customer_id = pre_existing_customer_data['id']
        response_delete = test_client_instance.delete(f'/api/customers/{customer_id}', headers=authorized_headers)
        assert response_delete.status_code == 204 #

        # Verify the customer is actually deleted by trying to GET them
        response_get = test_client_instance.get(f'/api/customers/{customer_id}', headers=authorized_headers)
        assert response_get.status_code == 404 # Should now be not found

    def test_delete_customer_not_found(self, test_client_instance, authorized_headers):
        """Test deletion failure for a non-existent customer."""
        non_existent_id = 99999
        response = test_client_instance.delete(f'/api/customers/{non_existent_id}', headers=authorized_headers)
        assert response.status_code == 404 #
        assert "Customer not found" in response.json['msg'] #

    # --- Test Authentication ---
    def test_get_all_customers_unauthorized(self, test_client_instance):
        """Test that accessing a protected route without a token fails."""
        response = test_client_instance.get('/api/customers/') # No 'authorized_headers'
        assert response.status_code == 401 # Expecting JWT to block
        # The exact message can vary based on Flask-JWT-Extended default error handlers
        # Common messages include "Missing Authorization Header" or similar.
        assert "Missing Authorization Header" in response.json.get("msg", "")