"""
Pytest configuration and fixtures for User Management API tests
"""

import pytest
import requests
import time
from typing import Dict, Any


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for the API"""
    return "http://localhost:8081/api/v1"


@pytest.fixture(scope="session")
def api_health_check(api_base_url):
    """Check if API server is running"""
    try:
        response = requests.get(f"{api_base_url}/health", timeout=5)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    pytest.skip("API server not running on localhost:8081")


@pytest.fixture(autouse=True)
def cleanup_users(api_base_url, api_health_check):
    """Clean up test users before and after each test"""
    # Clean up before test
    try:
        response = requests.get(f"{api_base_url}/users")
        if response.status_code == 200:
            users = response.json().get('users', [])
            for user in users:
                if user['username'].startswith('test_'):
                    requests.delete(f"{api_base_url}/users/{user['id']}")
    except requests.exceptions.RequestException:
        pass
    
    yield
    
    # Clean up after test
    try:
        response = requests.get(f"{api_base_url}/users")
        if response.status_code == 200:
            users = response.json().get('users', [])
            for user in users:
                if user['username'].startswith('test_'):
                    requests.delete(f"{api_base_url}/users/{user['id']}")
    except requests.exceptions.RequestException:
        pass


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "test_user_001",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role": "user",
        "phone": "+1234567890"
    }


@pytest.fixture
def admin_user_data():
    """Admin user data for testing"""
    return {
        "username": "test_admin_001",
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Test Admin",
        "role": "admin",
        "phone": "+1234567891"
    }


@pytest.fixture
def created_user(api_base_url, sample_user_data):
    """Create a test user and return user data"""
    response = requests.post(
        f"{api_base_url}/users",
        json=sample_user_data,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code == 201:
        return response.json()
    else:
        pytest.fail(f"Failed to create test user: {response.text}")


@pytest.fixture
def created_admin_user(api_base_url, admin_user_data):
    """Create a test admin user and return user data"""
    response = requests.post(
        f"{api_base_url}/users",
        json=admin_user_data,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code == 201:
        return response.json()
    else:
        pytest.fail(f"Failed to create test admin user: {response.text}")


@pytest.fixture
def auth_token(api_base_url, created_user):
    """Get authentication token for a test user"""
    login_data = {
        "username": created_user['username'],
        "password": "TestPass123!"  # Use the original password
    }
    response = requests.post(
        f"{api_base_url}/auth/login",
        json=login_data,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        pytest.fail(f"Failed to get auth token: {response.text}")


@pytest.fixture
def admin_auth_token(api_base_url, created_admin_user):
    """Get authentication token for a test admin user"""
    login_data = {
        "username": created_admin_user['username'],
        "password": "AdminPass123!"  # Use the original password
    }
    response = requests.post(
        f"{api_base_url}/auth/login",
        json=login_data,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        pytest.fail(f"Failed to get admin auth token: {response.text}")


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
