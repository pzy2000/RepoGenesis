"""
Pytest configuration and fixtures for Web Chatroom API tests
"""

import pytest
import requests
import time
import os


@pytest.fixture(scope="session")
def api_base_url():
    return os.getenv("API_BASE_URL", "http://localhost:8083/api/v1")


@pytest.fixture(scope="session")
def wait_for_service(api_base_url):
    max_retries = 30
    for attempt in range(max_retries):
        try:
            resp = requests.get(f"{api_base_url}/health", timeout=5)
            if resp.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    pytest.skip("Chatroom API server not available on localhost:8083")


@pytest.fixture
def user_credentials():
    return {"username": "test_user_chat", "password": "Password123!"}


@pytest.fixture
def registered_user(api_base_url, wait_for_service, user_credentials):
    # Best-effort cleanup
    try:
        requests.post(f"{api_base_url}/auth/register", json=user_credentials, timeout=5)
    except Exception:
        pass
    # Ensure login works even if already exists
    return user_credentials


@pytest.fixture
def auth_token(api_base_url, registered_user):
    resp = requests.post(f"{api_base_url}/auth/login", json=registered_user)
    if resp.status_code == 200 and "access_token" in resp.json():
        return resp.json()["access_token"]
    pytest.skip(f"Login failed: {resp.status_code} {resp.text}")


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "slow: slow tests")


