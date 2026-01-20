"""
WebPan API测试用例
测试文件存储与分享服务的所有API接口
"""

import pytest
import requests
import json
import os
import tempfile
from datetime import datetime, timedelta


class TestWebPanAPI:
    """WebPan API测试类"""
    
    BASE_URL = "http://localhost:8080/api/v1"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前置设置"""
        self.session = requests.Session()
        self.auth_token = None
        self.test_user = {
            "username": "testuser",
            "password": "testpass123",
            "email": "test@example.com"
        }
        self.test_file_content = b"This is a test file content for WebPan API testing."
        self.test_file_name = "test_file.txt"
        
    def test_user_registration(self):
        """测试用户注册接口"""
        response = self.session.post(
            f"{self.BASE_URL}/auth/register",
            json=self.test_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data
        assert data["message"] == "User registered successfully"
        
    def test_user_login(self):
        """测试用户登录接口"""
        # 先注册用户
        self.session.post(f"{self.BASE_URL}/auth/register", json=self.test_user)
        
        # 测试登录
        login_data = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        response = self.session.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data
        assert "user_id" in data
        assert "expires_in" in data
        
        # 保存token用于后续测试
        self.auth_token = data["token"]
        
    def test_login_invalid_credentials(self):
        """测试无效凭据登录"""
        login_data = {
            "username": "invalid_user",
            "password": "invalid_pass"
        }
        response = self.session.post(
            f"{self.BASE_URL}/auth/login",
            json=login_data
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "AUTH_INVALID"
        
    def test_file_upload_single(self):
        """测试单文件上传"""
        # 先登录获取token
        self._login_user()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
            
        try:
            # 上传文件
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(
                    f"{self.BASE_URL}/files/upload",
                    files=files,
                    headers=headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "file_id" in data
            assert data["filename"] == self.test_file_name
            assert data["size"] == len(self.test_file_content)
            assert "upload_time" in data
            assert "download_url" in data
            
            # 保存file_id用于后续测试
            self.test_file_id = data["file_id"]
            
        finally:
            os.unlink(temp_file_path)
            
    def test_file_upload_without_auth(self):
        """测试未认证的文件上传"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
            
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                response = self.session.post(
                    f"{self.BASE_URL}/files/upload",
                    files=files
                )
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "AUTH_REQUIRED"
            
        finally:
            os.unlink(temp_file_path)
            
    def test_file_upload_multiple(self):
        """测试多文件上传"""
        self._login_user()
        
        # 创建多个临时文件
        temp_files = []
        file_names = ["file1.txt", "file2.txt", "file3.txt"]
        
        try:
            for i, name in enumerate(file_names):
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
                    content = f"Test content for {name}".encode()
                    f.write(content)
                    temp_files.append((f.name, name, content))
            
            # 准备多文件上传
            files = []
            for temp_path, name, _ in temp_files:
                files.append(('files', (name, open(temp_path, 'rb'), 'text/plain')))
            
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(
                f"{self.BASE_URL}/files/upload-multiple",
                files=files,
                headers=headers
            )
            
            # 关闭文件句柄
            for _, (_, file_obj, _) in enumerate(files):
                file_obj[1][1].close()
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["uploaded_files"]) == 3
            assert len(data["failed_files"]) == 0
            
            for uploaded_file in data["uploaded_files"]:
                assert "file_id" in uploaded_file
                assert uploaded_file["status"] == "success"
                
        finally:
            for temp_path, _, _ in temp_files:
                os.unlink(temp_path)
                
    def test_file_download(self):
        """测试文件下载"""
        self._login_user()
        self._upload_test_file()
        
        # 下载文件
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(
            f"{self.BASE_URL}/files/{self.test_file_id}/download",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.content == self.test_file_content
        
    def test_file_download_not_found(self):
        """测试下载不存在的文件"""
        self._login_user()
        
        fake_file_id = "non-existent-file-id"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(
            f"{self.BASE_URL}/files/{fake_file_id}/download",
            headers=headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "FILE_NOT_FOUND"
        
    def test_file_info(self):
        """测试获取文件信息"""
        self._login_user()
        self._upload_test_file()
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(
            f"{self.BASE_URL}/files/{self.test_file_id}/info",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_id"] == self.test_file_id
        assert data["filename"] == self.test_file_name
        assert data["size"] == len(self.test_file_content)
        assert "mime_type" in data
        assert "upload_time" in data
        assert "download_count" in data
        assert "owner_id" in data
        
    def test_file_list(self):
        """测试获取文件列表"""
        self._login_user()
        self._upload_test_file()
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(
            f"{self.BASE_URL}/files",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "files" in data
        assert "pagination" in data
        assert len(data["files"]) >= 1
        
        # 检查分页信息
        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "pages" in pagination
        
    def test_file_list_with_pagination(self):
        """测试文件列表分页"""
        self._login_user()
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        params = {"page": 1, "limit": 5}
        response = self.session.get(
            f"{self.BASE_URL}/files",
            headers=headers,
            params=params
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 5
        
    def test_file_delete(self):
        """测试删除文件"""
        self._login_user()
        self._upload_test_file()
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.delete(
            f"{self.BASE_URL}/files/{self.test_file_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        
        # 验证文件已被删除
        response = self.session.get(
            f"{self.BASE_URL}/files/{self.test_file_id}/info",
            headers=headers
        )
        assert response.status_code == 404
        
    def test_file_rename(self):
        """测试文件重命名"""
        self._login_user()
        self._upload_test_file()
        
        new_name = "renamed_file.txt"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        data = {"new_name": new_name}
        
        response = self.session.put(
            f"{self.BASE_URL}/files/{self.test_file_id}/rename",
            json=data,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["new_filename"] == new_name
        
        # 验证重命名成功
        response = self.session.get(
            f"{self.BASE_URL}/files/{self.test_file_id}/info",
            headers=headers
        )
        assert response.status_code == 200
        file_info = response.json()
        assert file_info["filename"] == new_name
        
    def test_file_share_create(self):
        """测试创建文件分享链接"""
        self._login_user()
        self._upload_test_file()
        
        share_data = {
            "is_public": True,
            "expires_in": 3600
        }
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        response = self.session.post(
            f"{self.BASE_URL}/files/{self.test_file_id}/share",
            json=share_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "share_id" in data
        assert "share_url" in data
        assert "expires_at" in data
        assert "access_count" in data
        
        # 保存share_id用于后续测试
        self.test_share_id = data["share_id"]
        
    def test_file_share_with_password(self):
        """测试创建带密码的分享链接"""
        self._login_user()
        self._upload_test_file()
        
        share_data = {
            "is_public": False,
            "expires_in": 3600,
            "password": "sharepass123"
        }
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        response = self.session.post(
            f"{self.BASE_URL}/files/{self.test_file_id}/share",
            json=share_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "share_id" in data
        
    def test_share_access(self):
        """测试通过分享链接访问文件"""
        self._login_user()
        self._upload_test_file()
        self._create_share_link()
        
        # 通过分享链接访问
        response = self.session.get(
            f"{self.BASE_URL}/share/{self.test_share_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "file_info" in data
        assert "download_url" in data
        assert data["file_info"]["filename"] == self.test_file_name
        
    def test_share_access_with_password(self):
        """测试带密码的分享链接访问"""
        self._login_user()
        self._upload_test_file()
        
        # 创建带密码的分享链接
        share_data = {
            "is_public": False,
            "expires_in": 3600,
            "password": "sharepass123"
        }
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        response = self.session.post(
            f"{self.BASE_URL}/files/{self.test_file_id}/share",
            json=share_data,
            headers=headers
        )
        
        share_id = response.json()["share_id"]
        
        # 不带密码访问应该失败
        response = self.session.get(f"{self.BASE_URL}/share/{share_id}")
        assert response.status_code == 401
        
        # 带正确密码访问应该成功
        params = {"password": "sharepass123"}
        response = self.session.get(
            f"{self.BASE_URL}/share/{share_id}",
            params=params
        )
        assert response.status_code == 200
        
    def test_share_delete(self):
        """测试删除分享链接"""
        self._login_user()
        self._upload_test_file()
        self._create_share_link()
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.delete(
            f"{self.BASE_URL}/share/{self.test_share_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证分享链接已被删除
        response = self.session.get(f"{self.BASE_URL}/share/{self.test_share_id}")
        assert response.status_code == 404
        
    def test_storage_quota(self):
        """测试获取存储配额信息"""
        self._login_user()
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(
            f"{self.BASE_URL}/storage/quota",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "used_space" in data
        assert "total_space" in data
        assert "available_space" in data
        assert "usage_percentage" in data
        
        # 验证配额数据的合理性
        assert data["used_space"] >= 0
        assert data["total_space"] > 0
        assert data["available_space"] >= 0
        assert 0 <= data["usage_percentage"] <= 100
        
    def test_file_upload_large_file(self):
        """测试大文件上传（边界测试）"""
        self._login_user()
        
        # 创建接近限制大小的文件（99MB）
        large_content = b"x" * (99 * 1024 * 1024)
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(large_content)
            temp_file_path = f.name
            
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('large_file.bin', f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(
                    f"{self.BASE_URL}/files/upload",
                    files=files,
                    headers=headers
                )
            
            # 根据实际实现，可能成功或失败
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
            else:
                # 如果文件过大，应该返回相应错误
                data = response.json()
                assert data["success"] is False
                assert data["error_code"] in ["FILE_TOO_LARGE", "QUOTA_EXCEEDED"]
                
        finally:
            os.unlink(temp_file_path)
            
    def test_file_upload_oversized_file(self):
        """测试超大文件上传（超过限制）"""
        self._login_user()
        
        # 创建超过限制的文件（101MB）
        oversized_content = b"x" * (101 * 1024 * 1024)
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(oversized_content)
            temp_file_path = f.name
            
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('oversized_file.bin', f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(
                    f"{self.BASE_URL}/files/upload",
                    files=files,
                    headers=headers
                )
            
            assert response.status_code == 413
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "FILE_TOO_LARGE"
            
        finally:
            os.unlink(temp_file_path)
            
    def test_share_expired(self):
        """测试过期分享链接"""
        self._login_user()
        self._upload_test_file()
        
        # 创建立即过期的分享链接
        share_data = {
            "is_public": True,
            "expires_in": 1  # 1秒后过期
        }
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        response = self.session.post(
            f"{self.BASE_URL}/files/{self.test_file_id}/share",
            json=share_data,
            headers=headers
        )
        
        share_id = response.json()["share_id"]
        
        # 等待过期
        import time
        time.sleep(2)
        
        # 尝试访问过期链接
        response = self.session.get(f"{self.BASE_URL}/share/{share_id}")
        assert response.status_code == 410
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "SHARE_EXPIRED"
        
    # 辅助方法
    def _login_user(self):
        """登录用户并获取token"""
        # 先注册用户
        self.session.post(f"{self.BASE_URL}/auth/register", json=self.test_user)
        
        # 登录
        login_data = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        response = self.session.post(f"{self.BASE_URL}/auth/login", json=login_data)
        self.auth_token = response.json()["token"]
        
    def _upload_test_file(self):
        """上传测试文件"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
            f.write(self.test_file_content)
            temp_file_path = f.name
            
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (self.test_file_name, f, 'text/plain')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                response = self.session.post(
                    f"{self.BASE_URL}/files/upload",
                    files=files,
                    headers=headers
                )
            self.test_file_id = response.json()["file_id"]
        finally:
            os.unlink(temp_file_path)
            
    def _create_share_link(self):
        """创建分享链接"""
        share_data = {
            "is_public": True,
            "expires_in": 3600
        }
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        response = self.session.post(
            f"{self.BASE_URL}/files/{self.test_file_id}/share",
            json=share_data,
            headers=headers
        )
        self.test_share_id = response.json()["share_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
