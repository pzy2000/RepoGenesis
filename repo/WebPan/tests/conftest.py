import pytest
import requests
import tempfile
import os
from typing import Generator


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://localhost:8080/api/v1"


@pytest.fixture(scope="session")
def test_server_available(base_url: str) -> bool:
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture
def test_user() -> dict:
    return {
        "username": "testuser",
        "password": "testpass123",
        "email": "test@example.com"
    }


@pytest.fixture
def test_file_content() -> bytes:
    return b"This is a test file content for WebPan API testing."


@pytest.fixture
def test_file_name() -> str:
    return "test_file.txt"


@pytest.fixture
def temp_file(test_file_content: bytes, test_file_name: str) -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(test_file_content)
        temp_file_path = f.name
    
    yield temp_file_path
    
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def authenticated_session(base_url: str, test_user: dict) -> Generator[requests.Session, None, None]:
    session = requests.Session()
    
    session.post(f"{base_url}/auth/register", json=test_user)
    
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
    if not test_server_available:
        pytest.skip("Test server is not available")


pytest_plugins = []


def pytest_configure(config):
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
    for item in items:
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
        
        item.add_marker(pytest.mark.integration)
