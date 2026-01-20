import pytest
import requests
import json


class TestEdgeCases:
    
    BASE_URL = "http://localhost:8080/api/v1"
    
    def test_register_empty_request_body(self):
        response = requests.post(f"{self.BASE_URL}/users/register", json={})
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "required" in data["message"].lower()
    
    def test_register_missing_required_fields(self):
        incomplete_user = {"username": "testuser"}
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=incomplete_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_register_username_too_long(self):
        long_username_user = {
            "username": "a" * 21,
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=long_username_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "username" in data["message"].lower()
    
    def test_register_username_too_short(self):
        short_username_user = {
            "username": "ab",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=short_username_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "username" in data["message"].lower()
    
    def test_register_password_too_long(self):
        long_password_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "a" * 51
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=long_password_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "password" in data["message"].lower()
    
    def test_register_full_name_too_long(self):
        long_name_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "a" * 101
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=long_name_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "full_name" in data["message"].lower()
    
    def test_register_special_characters_in_username(self):
        special_char_user = {
            "username": "test@user#",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=special_char_user
        )
        
        assert response.status_code in [200, 400]
        data = response.json()
        if response.status_code == 400:
            assert data["success"] is False
    
    def test_login_empty_credentials(self):
        response = requests.post(f"{self.BASE_URL}/users/login", json={})
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_login_missing_password(self):
        login_data = {"username": "testuser"}
        
        response = requests.post(
            f"{self.BASE_URL}/users/login",
            json=login_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_get_user_info_nonexistent_user(self):
        test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        requests.post(f"{self.BASE_URL}/users/register", json=test_user)
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": test_user["username"], "password": test_user["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.BASE_URL}/users/99999", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
    
    def test_update_user_info_empty_body(self):
        test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        requests.post(f"{self.BASE_URL}/users/register", json=test_user)
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": test_user["username"], "password": test_user["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user_id = login_response.json()["data"]["user"]["user_id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{self.BASE_URL}/users/{user_id}", json={}, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_user_info_duplicate_email(self):
        user1 = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123"
        }
        user2 = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        
        requests.post(f"{self.BASE_URL}/users/register", json=user1)
        requests.post(f"{self.BASE_URL}/users/register", json=user2)
        
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": user2["username"], "password": user2["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user_id = login_response.json()["data"]["user"]["user_id"]
        
        update_data = {"email": user1["email"]}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{self.BASE_URL}/users/{user_id}", json=update_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "email" in data["message"].lower()
    
    def test_access_other_user_data(self):
        user1 = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123"
        }
        user2 = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        
        requests.post(f"{self.BASE_URL}/users/register", json=user1)
        requests.post(f"{self.BASE_URL}/users/register", json=user2)
        
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": user1["username"], "password": user1["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user1_id = login_response.json()["data"]["user"]["user_id"]
        
        login_response2 = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": user2["username"], "password": user2["password"]}
        )
        user2_id = login_response2.json()["data"]["user"]["user_id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.BASE_URL}/users/{user2_id}", headers=headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
    
    def test_malformed_json_request(self):
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_unsupported_http_methods(self):
        response = requests.get(f"{self.BASE_URL}/users/register")
        assert response.status_code == 405
        
        response = requests.put(f"{self.BASE_URL}/users/login")
        assert response.status_code == 405
    
    def test_invalid_url_path(self):
        response = requests.get(f"{self.BASE_URL}/invalid/path")
        assert response.status_code == 404
        
        response = requests.post(f"{self.BASE_URL}/users/invalid")
        assert response.status_code == 404
