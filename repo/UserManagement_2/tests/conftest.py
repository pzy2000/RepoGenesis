"""
Pytest配置文件
提供测试夹具和配置
"""

import pytest
import requests
import time
import os


@pytest.fixture(scope="session")
def api_base_url():
    """API基础URL配置"""
    return os.getenv("API_BASE_URL", "http://localhost:8080/api/v1")


@pytest.fixture(scope="session")
def wait_for_service(api_base_url):
    """等待服务启动"""
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"{api_base_url.replace('/api/v1', '')}/health", timeout=5)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        
        retry_count += 1
        time.sleep(1)
    
    if retry_count >= max_retries:
        pytest.skip("Service not available")


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }


@pytest.fixture
def registered_user(api_base_url, test_user_data, wait_for_service):
    """注册测试用户并返回用户信息"""
    # 清理可能存在的测试用户
    try:
        requests.delete(f"{api_base_url}/users/cleanup", timeout=5)
    except:
        pass
    
    # 注册用户
    response = requests.post(f"{api_base_url}/users/register", json=test_user_data)
    if response.status_code == 201:
        user_data = response.json()["data"]
        return user_data
    elif response.status_code == 400 and "already exists" in response.json().get("message", ""):
        # 用户已存在，尝试登录获取信息
        login_response = requests.post(
            f"{api_base_url}/users/login",
            json={"username": test_user_data["username"], "password": test_user_data["password"]}
        )
        if login_response.status_code == 200:
            return login_response.json()["data"]["user"]
    
    pytest.fail("Failed to register or login test user")


@pytest.fixture
def auth_token(api_base_url, test_user_data, wait_for_service):
    """获取认证token"""
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    
    response = requests.post(f"{api_base_url}/users/login", json=login_data)
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    
    pytest.fail("Failed to get auth token")


@pytest.fixture(autouse=True)
def cleanup_after_test(api_base_url, wait_for_service):
    """测试后清理"""
    yield
    # 这里可以添加测试后的清理逻辑
    # 例如删除测试创建的数据
    pass


def pytest_configure(config):
    """Pytest配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为所有测试添加integration标记
        item.add_marker(pytest.mark.integration)
        
        # 为包含"edge"的测试添加slow标记
        if "edge" in item.name:
            item.add_marker(pytest.mark.slow)
