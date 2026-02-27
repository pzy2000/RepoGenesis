import pytest
import requests
import time
import os


@pytest.fixture(scope="session")
def api_base_url():
    return os.getenv("API_BASE_URL", "http://localhost:8080/api/v1")


@pytest.fixture(scope="session")
def wait_for_service(api_base_url):
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
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }


@pytest.fixture
def registered_user(api_base_url, test_user_data, wait_for_service):
    try:
        requests.delete(f"{api_base_url}/users/cleanup", timeout=5)
    except:
        pass
    
    response = requests.post(f"{api_base_url}/users/register", json=test_user_data)
    if response.status_code == 201:
        user_data = response.json()["data"]
        return user_data
    elif response.status_code == 400 and "already exists" in response.json().get("message", ""):
        login_response = requests.post(
            f"{api_base_url}/users/login",
            json={"username": test_user_data["username"], "password": test_user_data["password"]}
        )
        if login_response.status_code == 200:
            return login_response.json()["data"]["user"]
    
    pytest.fail("Failed to register or login test user")


@pytest.fixture
def auth_token(api_base_url, test_user_data, wait_for_service):
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
    yield
    pass


def pytest_configure(config):
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
    for item in items:
        item.add_marker(pytest.mark.integration)
        
        if "edge" in item.name:
            item.add_marker(pytest.mark.slow)
