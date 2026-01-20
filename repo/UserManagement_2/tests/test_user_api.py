"""
用户管理API测试用例
测试用户注册、登录、查询、更新和删除功能
"""

import pytest
import requests
import json
from datetime import datetime, timedelta
import jwt


class TestUserAPI:
    """用户API测试类"""
    
    BASE_URL = "http://localhost:8080/api/v1"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        self.access_token = None
        self.user_id = None
    
    def test_user_registration_success(self):
        """测试用户注册成功"""
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=self.test_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data["data"]
        assert data["data"]["username"] == self.test_user["username"]
        assert data["data"]["email"] == self.test_user["email"]
        assert data["data"]["full_name"] == self.test_user["full_name"]
        assert "created_at" in data["data"]
        
        # 保存user_id供后续测试使用
        self.user_id = data["data"]["user_id"]
    
    def test_user_registration_duplicate_username(self):
        """测试重复用户名注册"""
        # 先注册一个用户
        requests.post(f"{self.BASE_URL}/users/register", json=self.test_user)
        
        # 尝试用相同用户名注册
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=self.test_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "username" in data["message"].lower()
    
    def test_user_registration_invalid_email(self):
        """测试无效邮箱注册"""
        invalid_user = self.test_user.copy()
        invalid_user["email"] = "invalid-email"
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=invalid_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "email" in data["message"].lower()
    
    def test_user_registration_short_password(self):
        """测试密码过短"""
        invalid_user = self.test_user.copy()
        invalid_user["password"] = "123"
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=invalid_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "password" in data["message"].lower()
    
    def test_user_login_success(self):
        """测试用户登录成功"""
        # 先注册用户
        requests.post(f"{self.BASE_URL}/users/register", json=self.test_user)
        
        login_data = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/login",
            json=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"
        assert "expires_in" in data["data"]
        assert "user" in data["data"]
        assert data["data"]["user"]["username"] == self.test_user["username"]
        
        # 保存token供后续测试使用
        self.access_token = data["data"]["access_token"]
        self.user_id = data["data"]["user"]["user_id"]
    
    def test_user_login_invalid_credentials(self):
        """测试无效凭据登录"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/login",
            json=login_data
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "credentials" in data["message"].lower() or "invalid" in data["message"].lower()
    
    def test_get_user_info_success(self):
        """测试获取用户信息成功"""
        # 先注册并登录用户
        requests.post(f"{self.BASE_URL}/users/register", json=self.test_user)
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": self.test_user["username"], "password": self.test_user["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user_id = login_response.json()["data"]["user"]["user_id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.BASE_URL}/users/{user_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == user_id
        assert data["data"]["username"] == self.test_user["username"]
        assert data["data"]["email"] == self.test_user["email"]
        assert data["data"]["full_name"] == self.test_user["full_name"]
        assert "created_at" in data["data"]
        assert "updated_at" in data["data"]
    
    def test_get_user_info_unauthorized(self):
        """测试未授权获取用户信息"""
        response = requests.get(f"{self.BASE_URL}/users/1")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "authorization" in data["message"].lower() or "token" in data["message"].lower()
    
    def test_get_user_info_invalid_token(self):
        """测试无效token获取用户信息"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{self.BASE_URL}/users/1", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_update_user_info_success(self):
        """测试更新用户信息成功"""
        # 先注册并登录用户
        requests.post(f"{self.BASE_URL}/users/register", json=self.test_user)
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": self.test_user["username"], "password": self.test_user["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user_id = login_response.json()["data"]["user"]["user_id"]
        
        update_data = {
            "email": "newemail@example.com",
            "full_name": "Updated Name"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{self.BASE_URL}/users/{user_id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == update_data["email"]
        assert data["data"]["full_name"] == update_data["full_name"]
        assert data["data"]["username"] == self.test_user["username"]  # username不应被更新
        assert "updated_at" in data["data"]
    
    def test_update_user_info_unauthorized(self):
        """测试未授权更新用户信息"""
        update_data = {"email": "newemail@example.com"}
        response = requests.put(f"{self.BASE_URL}/users/1", json=update_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_update_user_info_invalid_email(self):
        """测试更新无效邮箱"""
        # 先注册并登录用户
        requests.post(f"{self.BASE_URL}/users/register", json=self.test_user)
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": self.test_user["username"], "password": self.test_user["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user_id = login_response.json()["data"]["user"]["user_id"]
        
        update_data = {"email": "invalid-email"}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{self.BASE_URL}/users/{user_id}", json=update_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "email" in data["message"].lower()
    
    def test_delete_user_success(self):
        """测试删除用户成功"""
        # 先注册并登录用户
        requests.post(f"{self.BASE_URL}/users/register", json=self.test_user)
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": self.test_user["username"], "password": self.test_user["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user_id = login_response.json()["data"]["user"]["user_id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{self.BASE_URL}/users/{user_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证用户已被删除，无法再次获取信息
        get_response = requests.get(f"{self.BASE_URL}/users/{user_id}", headers=headers)
        assert get_response.status_code == 404
    
    def test_delete_user_unauthorized(self):
        """测试未授权删除用户"""
        response = requests.delete(f"{self.BASE_URL}/users/1")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_delete_nonexistent_user(self):
        """测试删除不存在的用户"""
        # 先注册并登录用户
        requests.post(f"{self.BASE_URL}/users/register", json=self.test_user)
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": self.test_user["username"], "password": self.test_user["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{self.BASE_URL}/users/99999", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
