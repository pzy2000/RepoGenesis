"""
Pytest configuration and fixtures for File Relay API tests
"""

import pytest
import requests
import time
import os
import io


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for the File Relay API"""
    return os.getenv("API_BASE_URL", "http://localhost:8085/api/v1")


@pytest.fixture(scope="session")
def wait_for_service(api_base_url):
    """Wait for the service to be available before running tests"""
    max_retries = 30
    for attempt in range(max_retries):
        try:
            resp = requests.get(f"{api_base_url}/health", timeout=5)
            if resp.status_code == 200:
                print(f"\n✓ File Relay API is ready at {api_base_url}")
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    pytest.skip(f"File Relay API server not available at {api_base_url}")


@pytest.fixture
def user_credentials():
    """Generate unique test user credentials"""
    timestamp = int(time.time() * 1000)
    return {
        "username": f"test_user_{timestamp}",
        "password": "TestPass123!"
    }


@pytest.fixture
def registered_user(api_base_url, wait_for_service, user_credentials):
    """Register a test user and return credentials"""
    try:
        resp = requests.post(
            f"{api_base_url}/auth/register",
            json=user_credentials,
            timeout=10
        )
        if resp.status_code in (201, 409):  # 201 created or 409 already exists
            return user_credentials
    except Exception as e:
        pytest.fail(f"Failed to register user: {e}")
    return user_credentials


@pytest.fixture
def auth_token(api_base_url, registered_user):
    """Login and get authentication token"""
    resp = requests.post(
        f"{api_base_url}/auth/login",
        json=registered_user,
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        if "access_token" in data:
            return data["access_token"]
    pytest.fail(f"Login failed: {resp.status_code} {resp.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Return authorization headers with bearer token"""
    return {
        "Authorization": f"Bearer {auth_token}"
    }


@pytest.fixture
def sample_text_file():
    """Create a sample text file for upload testing"""
    content = b"This is a test file for File Relay service.\nLine 2\nLine 3"
    return io.BytesIO(content), "test_file.txt", "text/plain"


@pytest.fixture
def sample_image_file():
    """Create a minimal PNG image file for testing"""
    # Minimal valid PNG file (1x1 pixel transparent)
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return io.BytesIO(png_data), "test_image.png", "image/png"


@pytest.fixture
def sample_pdf_file():
    """Create a minimal PDF file for testing"""
    # Minimal valid PDF
    pdf_data = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test PDF) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
409
%%EOF
"""
    return io.BytesIO(pdf_data), "test_document.pdf", "application/pdf"


@pytest.fixture
def uploaded_file(api_base_url, auth_headers, sample_text_file):
    """Upload a file and return its ID for testing"""
    file_obj, filename, content_type = sample_text_file
    
    files = {
        'file': (filename, file_obj, content_type)
    }
    data = {
        'description': 'Test file for automated tests',
        'tags': 'test,automation'
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        data=data,
        timeout=30
    )
    
    if resp.status_code in (200, 201):
        file_data = resp.json()
        file_id = file_data.get('id')
        if file_id:
            yield file_id
            # Cleanup after test
            try:
                requests.delete(
                    f"{api_base_url}/files/{file_id}",
                    headers=auth_headers,
                    timeout=10
                )
            except:
                pass  # Ignore cleanup errors
        else:
            pytest.fail("File upload succeeded but no ID returned")
    else:
        pytest.fail(f"Failed to upload test file: {resp.status_code} {resp.text}")


@pytest.fixture
def second_user_token(api_base_url, wait_for_service):
    """Create and authenticate a second user for permission testing"""
    timestamp = int(time.time() * 1000)
    credentials = {
        "username": f"test_user_2_{timestamp}",
        "password": "TestPass456!"
    }
    
    # Register
    reg_resp = requests.post(
        f"{api_base_url}/auth/register",
        json=credentials,
        timeout=10
    )
    
    if reg_resp.status_code not in (201, 409):
        pytest.fail(f"Failed to register second user: {reg_resp.status_code}")
    
    # Login
    login_resp = requests.post(
        f"{api_base_url}/auth/login",
        json=credentials,
        timeout=10
    )
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        if "access_token" in data:
            return data["access_token"]
    
    pytest.fail(f"Failed to login second user: {login_resp.status_code}")


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "api: API functionality tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "upload: file upload tests")
    config.addinivalue_line("markers", "download: file download tests")
    config.addinivalue_line("markers", "auth: authentication tests")
    config.addinivalue_line("markers", "edge: edge case tests")
    config.addinivalue_line("markers", "slow: slow running tests")


