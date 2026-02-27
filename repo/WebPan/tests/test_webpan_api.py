import pytest
import requests
import json
import os
import tempfile
from datetime import datetime, timedelta


class TestWebPanAPI:
    
    BASE_URL = "http://localhost:8080/api/v1"
    
    @pytest.fixture(autouse=True)
    def setup(self):
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
        self.session.post(f"{self.BASE_URL}/auth/register", json=self.test_user)
        
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
        
        self.auth_token = data["token"]
        
    def test_login_invalid_credentials(self):
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
        self._login_user()
        
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
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "file_id" in data
            assert data["filename"] == self.test_file_name
            assert data["size"] == len(self.test_file_content)
            assert "upload_time" in data
            assert "download_url" in data
            
            self.test_file_id = data["file_id"]
            
        finally:
            os.unlink(temp_file_path)
            
    def test_file_upload_without_auth(self):
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
        self._login_user()
        
        temp_files = []
        file_names = ["file1.txt", "file2.txt", "file3.txt"]
        
        try:
            for i, name in enumerate(file_names):
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
                    content = f"Test content for {name}".encode()
                    f.write(content)
                    temp_files.append((f.name, name, content))
            
            files = []
            for temp_path, name, _ in temp_files:
                files.append(('files', (name, open(temp_path, 'rb'), 'text/plain')))
            
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.post(
                f"{self.BASE_URL}/files/upload-multiple",
                files=files,
                headers=headers
            )
            
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
        self._login_user()
        self._upload_test_file()
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = self.session.get(
            f"{self.BASE_URL}/files/{self.test_file_id}/download",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.content == self.test_file_content
        
    def test_file_download_not_found(self):
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
        
        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "pages" in pagination
        
    def test_file_list_with_pagination(self):
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
        
        response = self.session.get(
            f"{self.BASE_URL}/files/{self.test_file_id}/info",
            headers=headers
        )
        assert response.status_code == 404
        
    def test_file_rename(self):
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
        
        response = self.session.get(
            f"{self.BASE_URL}/files/{self.test_file_id}/info",
            headers=headers
        )
        assert response.status_code == 200
        file_info = response.json()
        assert file_info["filename"] == new_name
        
    def test_file_share_create(self):
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
        
        self.test_share_id = data["share_id"]
        
    def test_file_share_with_password(self):
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
        self._login_user()
        self._upload_test_file()
        self._create_share_link()
        
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
        
        share_id = response.json()["share_id"]
        
        response = self.session.get(f"{self.BASE_URL}/share/{share_id}")
        assert response.status_code == 401
        
        params = {"password": "sharepass123"}
        response = self.session.get(
            f"{self.BASE_URL}/share/{share_id}",
            params=params
        )
        assert response.status_code == 200
        
    def test_share_delete(self):
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
        
        response = self.session.get(f"{self.BASE_URL}/share/{self.test_share_id}")
        assert response.status_code == 404
        
    def test_storage_quota(self):
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
        
        assert data["used_space"] >= 0
        assert data["total_space"] > 0
        assert data["available_space"] >= 0
        assert 0 <= data["usage_percentage"] <= 100
        
    def test_file_upload_large_file(self):
        self._login_user()
        
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
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
            else:
                data = response.json()
                assert data["success"] is False
                assert data["error_code"] in ["FILE_TOO_LARGE", "QUOTA_EXCEEDED"]
                
        finally:
            os.unlink(temp_file_path)
            
    def test_file_upload_oversized_file(self):
        self._login_user()
        
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
        self._login_user()
        self._upload_test_file()
        
        share_data = {
            "is_public": True,
            "expires_in": 1
        }
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        response = self.session.post(
            f"{self.BASE_URL}/files/{self.test_file_id}/share",
            json=share_data,
            headers=headers
        )
        share_id = response.json()["share_id"]
        import time
        time.sleep(2)
        response = self.session.get(f"{self.BASE_URL}/share/{share_id}")
        assert response.status_code == 410
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "SHARE_EXPIRED"
        

    def _login_user(self):


        self.session.post(f"{self.BASE_URL}/auth/register", json=self.test_user)
        

        login_data = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        response = self.session.post(f"{self.BASE_URL}/auth/login", json=login_data)
        self.auth_token = response.json()["token"]
        
    def _upload_test_file(self):

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
