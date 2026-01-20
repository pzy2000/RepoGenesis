"""
WebPan测试配置文件
提供测试用的fixtures和配置
"""

import pytest
import requests
import tempfile
import os
from typing import Generator


@pytest.fixture(scope="session")
def base_url() -> str:
    """测试服务器基础URL"""
    return "http://localhost:8080/api/v1"


@pytest.fixture(scope="session")
def test_server_available(base_url: str) -> bool:
    """检查测试服务器是否可用"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture
def test_user() -> dict:
    """测试用户数据"""
    return {
        "username": "testuser",
        "password": "testpass123",
        "email": "test@example.com"
    }


@pytest.fixture
def test_file_content() -> bytes:
    """测试文件内容"""
    return b"This is a test file content for WebPan API testing."


@pytest.fixture
def test_file_name() -> str:
    """测试文件名"""
    return "test_file.txt"


@pytest.fixture
def temp_file(test_file_content: bytes, test_file_name: str) -> Generator[str, None, None]:
    """创建临时文件"""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(test_file_content)
        temp_file_path = f.name
    
    yield temp_file_path
    
    # 清理临时文件
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def authenticated_session(base_url: str, test_user: dict) -> Generator[requests.Session, None, None]:
    """创建已认证的会话"""
    session = requests.Session()
    
    # 注册用户
    session.post(f"{base_url}/auth/register", json=test_user)
    
    # 登录获取token
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    response = session.post(f"{base_url}/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json()["token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
    
    yield session


@pytest.fixture
def uploaded_file_id(authenticated_session: requests.Session, base_url: str, 
                    temp_file: str, test_file_name: str) -> str:
    """上传测试文件并返回文件ID"""
    with open(temp_file, 'rb') as f:
        files = {'file': (test_file_name, f, 'text/plain')}
        response = authenticated_session.post(
            f"{base_url}/files/upload",
            files=files
        )
    
    if response.status_code == 200:
        return response.json()["file_id"]
    else:
        pytest.skip("Failed to upload test file")


@pytest.fixture
def share_link_id(authenticated_session: requests.Session, base_url: str, 
                 uploaded_file_id: str) -> str:
    """创建分享链接并返回分享ID"""
    share_data = {
        "is_public": True,
        "expires_in": 3600
    }
    
    response = authenticated_session.post(
        f"{base_url}/files/{uploaded_file_id}/share",
        json=share_data
    )
    
    if response.status_code == 200:
        return response.json()["share_id"]
    else:
        pytest.skip("Failed to create share link")


@pytest.fixture(autouse=True)
def skip_if_server_unavailable(test_server_available: bool):
    """如果服务器不可用则跳过所有测试"""
    if not test_server_available:
        pytest.skip("Test server is not available")


# 测试标记
pytest_plugins = []


def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "upload: mark test as file upload related"
    )
    config.addinivalue_line(
        "markers", "download: mark test as file download related"
    )
    config.addinivalue_line(
        "markers", "share: mark test as file sharing related"
    )
    config.addinivalue_line(
        "markers", "storage: mark test as storage management related"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为测试方法添加标记
        if "auth" in item.name:
            item.add_marker(pytest.mark.auth)
        elif "upload" in item.name:
            item.add_marker(pytest.mark.upload)
        elif "download" in item.name:
            item.add_marker(pytest.mark.download)
        elif "share" in item.name:
            item.add_marker(pytest.mark.share)
        elif "storage" in item.name or "quota" in item.name:
            item.add_marker(pytest.mark.storage)
        elif "large" in item.name or "oversized" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # 所有测试都是集成测试
        item.add_marker(pytest.mark.integration)
