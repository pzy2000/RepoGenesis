"""
边界情况和异常处理测试用例
测试API的边界条件和异常情况处理
"""

import pytest
import requests
import json


class TestEdgeCases:
    """边界情况测试类"""
    
    BASE_URL = "http://localhost:8080/api/v1"
    
    def test_register_empty_request_body(self):
        """测试空请求体注册"""
        response = requests.post(f"{self.BASE_URL}/users/register", json={})
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "required" in data["message"].lower()
    
    def test_register_missing_required_fields(self):
        """测试缺少必填字段注册"""
        incomplete_user = {"username": "testuser"}
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=incomplete_user
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_register_username_too_long(self):
        """测试用户名过长"""
        long_username_user = {
            "username": "a" * 21,  # 超过20字符限制
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
        """测试用户名过短"""
        short_username_user = {
            "username": "ab",  # 少于3字符
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
        """测试密码过长"""
        long_password_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "a" * 51  # 超过50字符限制
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
        """测试全名过长"""
        long_name_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "a" * 101  # 超过100字符限制
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
        """测试用户名包含特殊字符"""
        special_char_user = {
            "username": "test@user#",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            json=special_char_user
        )
        
        # 根据业务规则，可能接受或拒绝特殊字符
        assert response.status_code in [200, 400]
        data = response.json()
        if response.status_code == 400:
            assert data["success"] is False
    
    def test_login_empty_credentials(self):
        """测试空凭据登录"""
        response = requests.post(f"{self.BASE_URL}/users/login", json={})
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_login_missing_password(self):
        """测试缺少密码登录"""
        login_data = {"username": "testuser"}
        
        response = requests.post(
            f"{self.BASE_URL}/users/login",
            json=login_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_get_user_info_nonexistent_user(self):
        """测试获取不存在用户信息"""
        # 先注册并登录一个用户获取token
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
        """测试空更新请求体"""
        # 先注册并登录用户
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
        
        # 空更新请求应该返回成功（无变化）
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_user_info_duplicate_email(self):
        """测试更新为已存在的邮箱"""
        # 注册两个用户
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
        
        # 登录user2
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": user2["username"], "password": user2["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user_id = login_response.json()["data"]["user"]["user_id"]
        
        # 尝试将user2的邮箱更新为user1的邮箱
        update_data = {"email": user1["email"]}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{self.BASE_URL}/users/{user_id}", json=update_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "email" in data["message"].lower()
    
    def test_access_other_user_data(self):
        """测试访问其他用户数据"""
        # 注册两个用户
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
        
        # 登录user1
        login_response = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": user1["username"], "password": user1["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        user1_id = login_response.json()["data"]["user"]["user_id"]
        
        # 登录user2获取user2的ID
        login_response2 = requests.post(
            f"{self.BASE_URL}/users/login",
            json={"username": user2["username"], "password": user2["password"]}
        )
        user2_id = login_response2.json()["data"]["user"]["user_id"]
        
        # 使用user1的token尝试访问user2的数据
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.BASE_URL}/users/{user2_id}", headers=headers)
        
        # 应该被拒绝访问
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
    
    def test_malformed_json_request(self):
        """测试格式错误的JSON请求"""
        response = requests.post(
            f"{self.BASE_URL}/users/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_unsupported_http_methods(self):
        """测试不支持的HTTP方法"""
        # 对注册接口使用GET方法
        response = requests.get(f"{self.BASE_URL}/users/register")
        assert response.status_code == 405
        
        # 对登录接口使用PUT方法
        response = requests.put(f"{self.BASE_URL}/users/login")
        assert response.status_code == 405
    
    def test_invalid_url_path(self):
        """测试无效的URL路径"""
        response = requests.get(f"{self.BASE_URL}/invalid/path")
        assert response.status_code == 404
        
        response = requests.post(f"{self.BASE_URL}/users/invalid")
        assert response.status_code == 404
