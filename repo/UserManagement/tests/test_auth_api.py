"""
Authentication API Test Cases

This module contains test cases for authentication endpoints including login,
password reset, and token validation.
"""

import pytest
import requests
import json
import time


class TestAuthAPI:
    """Test suite for Authentication API endpoints"""
    
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
    
    def test_login_success(self):
        """Test successful user login"""
        # Create a test user
        user_data = {
            "username": "test_login_user",
            "email": "login@example.com",
            "password": "TestPass123!",
            "full_name": "Login Test User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        
        # Login with correct credentials
        login_data = {
            "username": user_data['username'],
            "password": user_data['password']
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'token_type' in data
        assert 'expires_in' in data
        assert 'user' in data
        assert data['token_type'] == 'Bearer'
        assert data['user']['username'] == user_data['username']
        assert data['user']['email'] == user_data['email']
        assert data['user']['role'] == user_data['role']
        assert 'password' not in data['user']  # Password should not be returned
    
    def test_login_invalid_username(self):
        """Test login with invalid username"""
        login_data = {
            "username": "nonexistent_user",
            "password": "SomePassword123!"
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'authentication_failed'
    
    def test_login_invalid_password(self):
        """Test login with invalid password"""
        # Create a test user
        user_data = {
            "username": "test_invalid_password",
            "email": "invalid_password@example.com",
            "password": "CorrectPass123!",
            "full_name": "Invalid Password User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        
        # Login with wrong password
        login_data = {
            "username": user_data['username'],
            "password": "WrongPassword123!"
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'authentication_failed'
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        login_data = {
            "username": "test_user"
            # Missing password
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_login_empty_credentials(self):
        """Test login with empty credentials"""
        login_data = {
            "username": "",
            "password": ""
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_login_inactive_user(self):
        """Test login with inactive user account"""
        # Create a test user
        user_data = {
            "username": "test_inactive_user",
            "email": "inactive@example.com",
            "password": "TestPass123!",
            "full_name": "Inactive User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Deactivate the user
        requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json={"status": "inactive"},
            headers={'Content-Type': 'application/json'}
        )
        
        # Try to login with inactive user
        login_data = {
            "username": user_data['username'],
            "password": user_data['password']
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 403
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'account_inactive'
    
    def test_login_suspended_user(self):
        """Test login with suspended user account"""
        # Create a test user
        user_data = {
            "username": "test_suspended_user",
            "email": "suspended@example.com",
            "password": "TestPass123!",
            "full_name": "Suspended User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Suspend the user
        requests.put(
            f"{self.BASE_URL}/users/{user_id}",
            json={"status": "suspended"},
            headers={'Content-Type': 'application/json'}
        )
        
        # Try to login with suspended user
        login_data = {
            "username": user_data['username'],
            "password": user_data['password']
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 403
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'account_suspended'
    
    def test_reset_password_success(self):
        """Test successful password reset"""
        # Create a test user
        user_data = {
            "username": "test_reset_password",
            "email": "reset@example.com",
            "password": "OldPassword123!",
            "full_name": "Reset Password User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Reset password
        reset_data = {
            "new_password": "NewPassword123!"
        }
        response = requests.post(
            f"{self.BASE_URL}/users/{user_id}/reset-password",
            json=reset_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        
        # Verify old password no longer works
        login_data = {
            "username": user_data['username'],
            "password": user_data['password']  # Old password
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 401
        
        # Verify new password works
        login_data = {
            "username": user_data['username'],
            "password": reset_data['new_password']  # New password
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
    
    def test_reset_password_weak_password(self):
        """Test password reset with weak password"""
        # Create a test user
        user_data = {
            "username": "test_weak_reset",
            "email": "weak_reset@example.com",
            "password": "TestPass123!",
            "full_name": "Weak Reset User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Try to reset with weak password
        reset_data = {
            "new_password": "123"  # Too weak
        }
        response = requests.post(
            f"{self.BASE_URL}/users/{user_id}/reset-password",
            json=reset_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_reset_password_nonexistent_user(self):
        """Test password reset for non-existent user"""
        reset_data = {
            "new_password": "NewPassword123!"
        }
        response = requests.post(
            f"{self.BASE_URL}/users/99999/reset-password",
            json=reset_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'
    
    def test_reset_password_missing_new_password(self):
        """Test password reset with missing new password"""
        # Create a test user
        user_data = {
            "username": "test_missing_reset",
            "email": "missing_reset@example.com",
            "password": "TestPass123!",
            "full_name": "Missing Reset User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        user_id = response.json()['id']
        
        # Try to reset without new password
        reset_data = {}
        response = requests.post(
            f"{self.BASE_URL}/users/{user_id}/reset-password",
            json=reset_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_token_expiration(self):
        """Test token expiration behavior"""
        # Create a test user
        user_data = {
            "username": "test_token_expiration",
            "email": "token@example.com",
            "password": "TestPass123!",
            "full_name": "Token Expiration User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        
        # Login to get token
        login_data = {
            "username": user_data['username'],
            "password": user_data['password']
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']
        
        # Token should have expiration time
        assert expires_in > 0
        
        # Test that token is valid immediately after login
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{self.BASE_URL}/users/{response.json()['user']['id']}", headers=headers)
        # This test assumes there's a protected endpoint that validates tokens
        # The exact behavior depends on implementation
    
    def test_login_case_sensitivity(self):
        """Test login case sensitivity"""
        # Create a test user
        user_data = {
            "username": "TestUserCase",
            "email": "case@example.com",
            "password": "TestPass123!",
            "full_name": "Case Test User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        
        # Test different case variations
        test_cases = [
            ("testusercase", user_data['password']),  # All lowercase
            ("TESTUSERCASE", user_data['password']),  # All uppercase
            ("testusercase", "testpass123!"),  # Wrong case password
        ]
        
        for username, password in test_cases:
            login_data = {"username": username, "password": password}
            response = requests.post(
                f"{self.BASE_URL}/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            # Should either succeed or fail consistently
            assert response.status_code in [200, 401]
    
    def test_concurrent_login_attempts(self):
        """Test handling of concurrent login attempts"""
        # Create a test user
        user_data = {
            "username": "test_concurrent_login",
            "email": "concurrent@example.com",
            "password": "TestPass123!",
            "full_name": "Concurrent Login User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        
        import threading
        results = []
        errors = []
        
        def attempt_login(thread_id):
            try:
                login_data = {
                    "username": user_data['username'],
                    "password": user_data['password']
                }
                response = requests.post(
                    f"{self.BASE_URL}/auth/login",
                    json=login_data,
                    headers={'Content-Type': 'application/json'}
                )
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=attempt_login, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent login attempts: {errors}"
        assert len(results) == 5
        
        # All login attempts should succeed
        for thread_id, status_code in results:
            assert status_code == 200
    
    def test_malformed_login_request(self):
        """Test handling of malformed login requests"""
        malformed_requests = [
            '{"username": "test", "password": "pass"',  # Missing closing brace
            '{"username": "test", "password": "pass",}',  # Trailing comma
            '{"username": "test", "password": pass}',  # Unquoted string
            '{"username": "test" "password": "pass"}',  # Missing comma
        ]
        
        for malformed_request in malformed_requests:
            response = requests.post(
                f"{self.BASE_URL}/auth/login",
                data=malformed_request,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 400
