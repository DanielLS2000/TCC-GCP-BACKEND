class TestEmployeeRoutes:

    def test_create_employee_success(self, client, auth_headers, sample_employee_data, db):
        """Test successful employee creation."""
        response = client.post('/api/employees/', headers=auth_headers, json=sample_employee_data)
        print(response.data)  # Debugging line to see the response content
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['name'] == sample_employee_data['name']
        assert json_data['email'] == sample_employee_data['email']
        assert 'id' in json_data
        assert response.headers['Location'] is not None

        # Verify hiredate is a string (assuming model's to_dict is fixed)
        assert isinstance(json_data.get('hiredate'), str)


    def test_create_employee_missing_name(self, client, auth_headers, sample_employee_data):
        """Test employee creation with missing name."""
        data = sample_employee_data.copy()
        del data['name']
        response = client.post('/api/employees/', headers=auth_headers, json=data)
        assert response.status_code == 422 # As per route validation
        json_data = response.get_json()
        assert "details" in json_data
        assert "name" in json_data["details"]

    def test_create_employee_missing_auth(self, client, sample_employee_data):
        """Test employee creation without JWT token."""
        response = client.post('/api/employees/', json=sample_employee_data)
        assert response.status_code == 401 # Unauthorized

    def test_get_all_employees_success(self, client, auth_headers, db, sample_employee_data):
        """Test getting all employees."""
        # Create an employee first
        client.post('/api/employees/', headers=auth_headers, json=sample_employee_data)

        response = client.get('/api/employees/', headers=auth_headers)
        assert response.status_code == 200
        json_data = response.get_json()
        assert isinstance(json_data, list)
        assert len(json_data) >= 1
        assert json_data[0]['name'] == sample_employee_data['name']
         # Verify hiredate is a string in the list
        assert isinstance(json_data[0].get('hiredate'), str)


    def test_get_all_employees_empty(self, client, auth_headers, db):
        """Test getting all employees when none exist."""
        # Ensure DB is clean (handled by app fixture and reset_db)
        response = client.get('/api/employees/', headers=auth_headers)
        assert response.status_code == 200
        json_data = response.get_json()
        assert isinstance(json_data, list)
        assert len(json_data) == 0

    def test_get_employee_by_id_success(self, client, auth_headers, sample_employee_data, db):
        """Test getting a single employee by ID."""
        post_response = client.post('/api/employees/', headers=auth_headers, json=sample_employee_data)
        employee_id = post_response.get_json()['id']

        response = client.get(f'/api/employees/{employee_id}', headers=auth_headers)
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['id'] == employee_id
        assert json_data['name'] == sample_employee_data['name']
        assert isinstance(json_data.get('hiredate'), str)


    def test_get_employee_by_id_not_found(self, client, auth_headers, db):
        """Test getting a non-existent employee by ID."""
        response = client.get('/api/employees/9999', headers=auth_headers) # Assuming 9999 does not exist
        assert response.status_code == 404

    def test_update_employee_success(self, client, auth_headers, sample_employee_data, db):
        """Test successfully updating an employee."""
        post_response = client.post('/api/employees/', headers=auth_headers, json=sample_employee_data)
        employee_id = post_response.get_json()['id']

        update_data = {"name": "Jane Doe Updated", "salary": 80000.0}
        response = client.put(f'/api/employees/{employee_id}', headers=auth_headers, json=update_data)
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['id'] == employee_id
        assert json_data['name'] == "Jane Doe Updated"
        assert json_data['salary'] == 80000.0
        assert json_data['email'] == sample_employee_data['email'] # Unchanged field
        assert isinstance(json_data.get('hiredate'), str)


    def test_update_employee_not_found(self, client, auth_headers, db):
        """Test updating a non-existent employee."""
        update_data = {"name": "Non Existent Updated"}
        response = client.put('/api/employees/9999', headers=auth_headers, json=update_data)
        assert response.status_code == 404

    def test_update_employee_invalid_data(self, client, auth_headers, sample_employee_data, db):
        """Test updating an employee with invalid data (e.g., empty name)."""
        post_response = client.post('/api/employees/', headers=auth_headers, json=sample_employee_data)
        employee_id = post_response.get_json()['id']

        update_data = {"name": ""} # Name cannot be empty if provided
        response = client.put(f'/api/employees/{employee_id}', headers=auth_headers, json=update_data)
        assert response.status_code == 422
        json_data = response.get_json()
        assert "details" in json_data and "name" in json_data["details"]

    def test_delete_employee_success(self, client, auth_headers, sample_employee_data, db):
        """Test successfully deleting an employee."""
        post_response = client.post('/api/employees/', headers=auth_headers, json=sample_employee_data)
        employee_id = post_response.get_json()['id']

        delete_response = client.delete(f'/api/employees/{employee_id}', headers=auth_headers)
        assert delete_response.status_code == 204

        # Verify employee is deleted
        get_response = client.get(f'/api/employees/{employee_id}', headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_employee_not_found(self, client, auth_headers, db):
        """Test deleting a non-existent employee."""
        response = client.delete('/api/employees/9999', headers=auth_headers)
        assert response.status_code == 404

    def test_create_employee_no_json(self, client, auth_headers):
        """Test employee creation with no JSON body."""
        response = client.post('/api/employees/', headers=auth_headers)
        assert response.status_code == 400 # "Request body is missing or not JSON"
        json_data = response.get_json()
        assert "msg" in json_data
        assert "Request body is missing or not JSON" in json_data["msg"]

    def test_update_employee_no_json(self, client, auth_headers, sample_employee_data, db):
        """Test employee update with no JSON body."""
        post_response = client.post('/api/employees/', headers=auth_headers, json=sample_employee_data)
        employee_id = post_response.get_json()['id']

        response = client.put(f'/api/employees/{employee_id}', headers=auth_headers)
        assert response.status_code == 400 # "Request body is missing or not JSON"
        json_data = response.get_json()
        assert "msg" in json_data
        assert "Request body is missing or not JSON" in json_data["msg"]