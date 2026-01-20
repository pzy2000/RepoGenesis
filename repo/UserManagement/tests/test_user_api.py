"""
User Management API Test Cases

This module contains comprehensive test cases for the User Management Microservice API.
All tests follow the interface definitions specified in the README.md file.
"""

import pytest
import requests
import json
from datetime import datetime, timedelta


class TestUserAPI:
    """Test suite for User Management API endpoints"""
    
    BASE_URL = "http://localhost:8081/api/v1"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        # Clean up any existing test users before each test
        try:
            response = requests.get(f"{self.BASE_URL}/users")
            if response.status_code == 200:
                users = response.json().get('users', [])
                for user in users:
                    if user['username'].startswith('test_'):
                        requests.delete(f"{self.BASE_URL}/users/{user['id']}")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert 'database' in data
        assert data['status'] == 'healthy'
    
    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {
            "username": "test_user_001",
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "role": "user",
            "phone": "+1234567890"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['full_name'] == user_data['full_name']
        assert data['role'] == user_data['role']
        assert data['phone'] == user_data['phone']
        assert data['status'] == 'active'  # Default status
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'password' not in data  # Password should not be returned
    
    def test_create_user_minimal_data(self):
        """Test user creation with minimal required data"""
        user_data = {
            "username": "test_minimal",
            "email": "minimal@example.com",
            "password": "MinPass123!",
            "full_name": "Minimal User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == user_data['username']
        assert data['email'] == user_data['email']
        assert data['full_name'] == user_data['full_name']
        assert data['role'] == user_data['role']
        assert data['status'] == 'active'
        assert data['phone'] is None or data['phone'] == ""
    
    def test_create_user_invalid_role(self):
        """Test user creation with invalid role"""
        user_data = {
            "username": "test_invalid_role",
            "email": "invalid@example.com",
            "password": "TestPass123!",
            "full_name": "Invalid Role User",
            "role": "invalid_role"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'validation_error'
    
    def test_create_user_missing_required_fields(self):
        """Test user creation with missing required fields"""
        user_data = {
            "email": "missing@example.com"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username"""
        user_data = {
            "username": "test_duplicate",
            "email": "duplicate1@example.com",
            "password": "TestPass123!",
            "full_name": "Duplicate User 1",
            "role": "user"
        }
        
        # Create first user
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        
        # Try to create second user with same username
        user_data['email'] = "duplicate2@example.com"
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 409
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'conflict'
    
    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        user_data = {
            "username": "test_duplicate_email_1",
            "email": "duplicate@example.com",
            "password": "TestPass123!",
            "full_name": "Duplicate Email User 1",
            "role": "user"
        }
        
        # Create first user
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        
        # Try to create second user with same email
        user_data['username'] = "test_duplicate_email_2"
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 409
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'conflict'
    
    def test_create_user_invalid_email_format(self):
        """Test user creation with invalid email format"""
        user_data = {
            "username": "test_invalid_email",
            "email": "invalid-email-format",
            "password": "TestPass123!",
            "full_name": "Invalid Email User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_create_user_weak_password(self):
        """Test user creation with weak password"""
        user_data = {
            "username": "test_weak_password",
            "email": "weak@example.com",
            "password": "123",  # Too short
            "full_name": "Weak Password User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_get_users_list_empty(self):
        """Test getting users list when no users exist"""
        response = requests.get(f"{self.BASE_URL}/users")
        
        assert response.status_code == 200
        data = response.json()
        assert 'users' in data
        assert 'pagination' in data
        assert len(data['users']) == 0
        assert data['pagination']['total'] == 0
    
    def test_get_users_list_with_data(self):
        """Test getting users list with existing users"""
        # Create test users
        users_data = [
            {
                "username": "test_list_1",
                "email": "list1@example.com",
                "password": "TestPass123!",
                "full_name": "List User 1",
                "role": "user"
            },
            {
                "username": "test_list_2",
                "email": "list2@example.com",
                "password": "TestPass123!",
                "full_name": "List User 2",
                "role": "admin"
            },
            {
                "username": "test_list_3",
                "email": "list3@example.com",
                "password": "TestPass123!",
                "full_name": "List User 3",
                "role": "moderator"
            }
        ]
        
        created_users = []
        for user_data in users_data:
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            assert response.status_code == 201
            created_users.append(response.json())
        
        # Get users list
        response = requests.get(f"{self.BASE_URL}/users")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) >= 3  # At least our test users
        assert data['pagination']['total'] >= 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 10
    
    def test_get_users_list_pagination(self):
        """Test users list pagination"""
        # Create 15 test users
        for i in range(15):
            user_data = {
                "username": f"test_pagination_{i+1}",
                "email": f"pagination{i+1}@example.com",
                "password": "TestPass123!",
                "full_name": f"Pagination User {i+1}",
                "role": "user"
            }
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            assert response.status_code == 201
        
        # Test first page
        response = requests.get(f"{self.BASE_URL}/users?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 15
        assert data['pagination']['pages'] >= 2
        
        # Test second page
        response = requests.get(f"{self.BASE_URL}/users?page=2&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data['users']) >= 5
        assert data['pagination']['page'] == 2
    
    def test_get_users_list_filter_by_role(self):
        """Test filtering users by role"""
        # Create users with different roles
        roles = ["user", "admin", "moderator"]
        for role in roles:
            user_data = {
                "username": f"test_role_{role}",
                "email": f"role_{role}@example.com",
                "password": "TestPass123!",
                "full_name": f"Role {role.title()} User",
                "role": role
            }
            requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
        
        # Filter by admin role
        response = requests.get(f"{self.BASE_URL}/users?role=admin")
        assert response.status_code == 200
        data = response.json()
        admin_users = [user for user in data['users'] if user['role'] == 'admin']
        assert len(admin_users) >= 1
    
    def test_get_users_list_filter_by_status(self):
        """Test filtering users by status"""
        # Create a user
        user_data = {
            "username": "test_status_filter",
            "email": "status@example.com",
            "password": "TestPass123!",
            "full_name": "Status Filter User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Update user status
        requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json={"status": "inactive"},
            headers={'Content-Type': 'application/json'}
        )
        
        # Filter by inactive status
        response = requests.get(f"{self.BASE_URL}/users?status=inactive")
        assert response.status_code == 200
        data = response.json()
        inactive_users = [user for user in data['users'] if user['status'] == 'inactive']
        assert len(inactive_users) >= 1
    
    def test_get_users_list_search(self):
        """Test searching users by username, email, or full_name"""
        # Create a user with specific name
        user_data = {
            "username": "test_search_unique",
            "email": "search_unique@example.com",
            "password": "TestPass123!",
            "full_name": "Unique Search User",
            "role": "user"
        }
        requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Search by username
        response = requests.get(f"{self.BASE_URL}/users?search=test_search_unique")
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'test_search_unique' in user['username']]
        assert len(found_users) >= 1
        
        # Search by email
        response = requests.get(f"{self.BASE_URL}/users?search=search_unique@example.com")
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'search_unique@example.com' in user['email']]
        assert len(found_users) >= 1
        
        # Search by full name
        response = requests.get(f"{self.BASE_URL}/users?search=Unique Search")
        assert response.status_code == 200
        data = response.json()
        found_users = [user for user in data['users'] if 'Unique Search' in user['full_name']]
        assert len(found_users) >= 1
    
    def test_get_single_user_success(self):
        """Test getting a single user by ID"""
        # Create a user
        user_data = {
            "username": "test_single_user",
            "email": "single@example.com",
            "password": "TestPass123!",
            "full_name": "Single User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        created_user = response.json()
        
        # Get the user by ID
        response = requests.get(f"{self.BASE_URL}/users/{created_user['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == created_user['id']
        assert data['username'] == created_user['username']
        assert data['email'] == created_user['email']
        assert data['role'] == created_user['role']
    
    def test_get_single_user_not_found(self):
        """Test getting a non-existent user"""
        response = requests.get(f"{self.BASE_URL}/users/99999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'
    
    def test_update_user_success(self):
        """Test successful user update"""
        # Create a user
        user_data = {
            "username": "test_update_user",
            "email": "update@example.com",
            "password": "TestPass123!",
            "full_name": "Original User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Update the user
        update_data = {
            "username": "test_updated_user",
            "email": "updated@example.com",
            "full_name": "Updated User",
            "role": "moderator",
            "status": "inactive"
        }
        response = requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['username'] == update_data['username']
        assert data['email'] == update_data['email']
        assert data['full_name'] == update_data['full_name']
        assert data['role'] == update_data['role']
        assert data['status'] == update_data['status']
        assert data['id'] == user_id
    
    def test_update_user_partial(self):
        """Test partial user update"""
        # Create a user
        user_data = {
            "username": "test_partial_update",
            "email": "partial@example.com",
            "password": "TestPass123!",
            "full_name": "Original Full Name",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Update only full name
        update_data = {"full_name": "Updated Full Name Only"}
        response = requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['full_name'] == update_data['full_name']
        assert data['username'] == user_data['username']  # Should remain unchanged
        assert data['email'] == user_data['email']  # Should remain unchanged
        assert data['role'] == user_data['role']  # Should remain unchanged
    
    def test_update_user_invalid_role(self):
        """Test user update with invalid role"""
        # Create a user
        user_data = {
            "username": "test_invalid_role_update",
            "email": "invalid_role@example.com",
            "password": "TestPass123!",
            "full_name": "Invalid Role User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Update with invalid role
        update_data = {"role": "invalid_role"}
        response = requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_update_user_not_found(self):
        """Test updating a non-existent user"""
        update_data = {"full_name": "Updated User"}
        response = requests.put(
            f"{self.BASE_URL}/users/99999",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'
    
    def test_delete_user_success(self):
        """Test successful user deletion"""
        # Create a user
        user_data = {
            "username": "test_delete_user",
            "email": "delete@example.com",
            "password": "TestPass123!",
            "full_name": "User to Delete",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Delete the user
        response = requests.delete(f"{self.BASE_URL}/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        
        # Verify user is deleted
        response = requests.get(f"{self.BASE_URL}/users/{user_id}")
        assert response.status_code == 404
    
    def test_delete_user_not_found(self):
        """Test deleting a non-existent user"""
        response = requests.delete(f"{self.BASE_URL}/users/99999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'
    
    def test_user_workflow_complete(self):
        """Test complete user workflow: create -> update -> deactivate -> delete"""
        # Create user
        user_data = {
            "username": "test_workflow_user",
            "email": "workflow@example.com",
            "password": "TestPass123!",
            "full_name": "Workflow User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        user_id = response.json()['id']
        
        # Update user role
        response = requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json={"role": "moderator"},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        assert response.json()['role'] == 'moderator'
        
        # Deactivate user
        response = requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json={"status": "inactive"},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'inactive'
        
        # Verify in inactive users list
        response = requests.get(f"{self.BASE_URL}/users?status=inactive")
        assert response.status_code == 200
        inactive_users = response.json()['users']
        inactive_user_ids = [user['id'] for user in inactive_users]
        assert user_id in inactive_user_ids
        
        # Delete the user
        response = requests.delete(f"{self.BASE_URL}/users/{user_id}")
        assert response.status_code == 200
        
        # Verify deletion
        response = requests.get(f"{self.BASE_URL}/users/{user_id}")
        assert response.status_code == 404
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request body"""
        response = requests.post(
            f"{self.BASE_URL}/users",
            data="invalid json",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data
    
    def test_missing_content_type_header(self):
        """Test handling of missing Content-Type header"""
        user_data = {
            "username": "test_no_content_type",
            "email": "no_content_type@example.com",
            "password": "TestPass123!",
            "full_name": "No Content Type User",
            "role": "user"
        }
        response = requests.post(f"{self.BASE_URL}/users", json=user_data)
        
        # Should either work or fail gracefully
        assert response.status_code in [201, 400, 415]
    
    def test_large_pagination_limit(self):
        """Test pagination with limit exceeding maximum"""
        response = requests.get(f"{self.BASE_URL}/users?limit=1000")
        
        # Should either return max allowed limit or error
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100  # Should be capped at max
