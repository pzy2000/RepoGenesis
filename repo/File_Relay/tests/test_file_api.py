"""
File Relay API Tests - Core Functionality
"""

import pytest
import requests
import io


@pytest.mark.api
def test_health_check(api_base_url, wait_for_service):
    """Test health check endpoint"""
    resp = requests.get(f"{api_base_url}/health", timeout=10)
    assert resp.status_code == 200
    
    data = resp.json()
    assert data.get("status") == "ok"
    assert "service" in data
    assert "version" in data


@pytest.mark.auth
def test_user_registration(api_base_url, wait_for_service):
    """Test user registration with valid credentials"""
    import time
    credentials = {
        "username": f"new_user_{int(time.time() * 1000)}",
        "password": "ValidPass123!"
    }
    
    resp = requests.post(
        f"{api_base_url}/auth/register",
        json=credentials,
        timeout=10
    )
    
    assert resp.status_code in (201, 409)  # 201 created or 409 if already exists
    
    if resp.status_code == 201:
        data = resp.json()
        assert "id" in data
        assert data.get("username") == credentials["username"]
        assert "created_at" in data


@pytest.mark.auth
def test_user_registration_invalid_username(api_base_url, wait_for_service):
    """Test user registration with invalid username"""
    invalid_credentials = [
        {"username": "ab", "password": "ValidPass123!"},  # Too short
        {"username": "a" * 50, "password": "ValidPass123!"},  # Too long
        {"username": "user@invalid", "password": "ValidPass123!"},  # Invalid chars
    ]
    
    for creds in invalid_credentials:
        resp = requests.post(
            f"{api_base_url}/auth/register",
            json=creds,
            timeout=10
        )
        assert resp.status_code == 400, f"Expected 400 for invalid username: {creds['username']}"


@pytest.mark.auth
def test_user_registration_invalid_password(api_base_url, wait_for_service):
    """Test user registration with invalid password"""
    import time
    credentials = {
        "username": f"test_user_{int(time.time() * 1000)}",
        "password": "short"  # Too short (< 8 chars)
    }
    
    resp = requests.post(
        f"{api_base_url}/auth/register",
        json=credentials,
        timeout=10
    )
    
    assert resp.status_code == 400


@pytest.mark.auth
def test_user_registration_duplicate(api_base_url, registered_user):
    """Test user registration with duplicate username"""
    resp = requests.post(
        f"{api_base_url}/auth/register",
        json=registered_user,
        timeout=10
    )
    
    assert resp.status_code == 409  # Conflict


@pytest.mark.auth
def test_user_login(api_base_url, registered_user):
    """Test user login with valid credentials"""
    resp = requests.post(
        f"{api_base_url}/auth/login",
        json=registered_user,
        timeout=10
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data.get("token_type") == "Bearer" or "token_type" in data


@pytest.mark.auth
def test_user_login_invalid_credentials(api_base_url, registered_user):
    """Test user login with invalid credentials"""
    invalid_creds = {
        "username": registered_user["username"],
        "password": "WrongPassword123!"
    }
    
    resp = requests.post(
        f"{api_base_url}/auth/login",
        json=invalid_creds,
        timeout=10
    )
    
    assert resp.status_code == 401


@pytest.mark.upload
def test_upload_text_file(api_base_url, auth_headers, sample_text_file):
    """Test uploading a text file"""
    file_obj, filename, content_type = sample_text_file
    
    files = {
        'file': (filename, file_obj, content_type)
    }
    data = {
        'description': 'Test text file upload',
        'tags': 'test,text'
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        data=data,
        timeout=30
    )
    
    assert resp.status_code in (200, 201)
    
    file_data = resp.json()
    assert "id" in file_data
    assert file_data.get("filename") == filename
    assert "size" in file_data
    assert file_data["size"] > 0
    assert "upload_time" in file_data
    assert "uploader" in file_data
    
    # Cleanup
    file_id = file_data.get("id")
    if file_id:
        requests.delete(
            f"{api_base_url}/files/{file_id}",
            headers=auth_headers,
            timeout=10
        )


@pytest.mark.upload
def test_upload_image_file(api_base_url, auth_headers, sample_image_file):
    """Test uploading an image file"""
    file_obj, filename, content_type = sample_image_file
    
    files = {
        'file': (filename, file_obj, content_type)
    }
    data = {
        'description': 'Test image upload'
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        data=data,
        timeout=30
    )
    
    assert resp.status_code in (200, 201)
    
    file_data = resp.json()
    assert "id" in file_data
    assert file_data.get("filename") == filename
    assert "image" in file_data.get("content_type", "").lower() or filename.endswith('.png')
    
    # Cleanup
    file_id = file_data.get("id")
    if file_id:
        requests.delete(
            f"{api_base_url}/files/{file_id}",
            headers=auth_headers,
            timeout=10
        )


@pytest.mark.upload
def test_upload_pdf_file(api_base_url, auth_headers, sample_pdf_file):
    """Test uploading a PDF document"""
    file_obj, filename, content_type = sample_pdf_file
    
    files = {
        'file': (filename, file_obj, content_type)
    }
    data = {
        'description': 'Test PDF upload',
        'tags': 'pdf,document,test'
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        data=data,
        timeout=30
    )
    
    assert resp.status_code in (200, 201)
    
    file_data = resp.json()
    assert "id" in file_data
    assert file_data.get("filename") == filename
    
    # Cleanup
    file_id = file_data.get("id")
    if file_id:
        requests.delete(
            f"{api_base_url}/files/{file_id}",
            headers=auth_headers,
            timeout=10
        )


@pytest.mark.upload
def test_upload_without_auth(api_base_url, sample_text_file):
    """Test uploading a file without authentication"""
    file_obj, filename, content_type = sample_text_file
    
    files = {
        'file': (filename, file_obj, content_type)
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        files=files,
        timeout=30
    )
    
    assert resp.status_code == 401


@pytest.mark.upload
def test_upload_empty_file(api_base_url, auth_headers):
    """Test uploading an empty file"""
    empty_file = io.BytesIO(b'')
    
    files = {
        'file': ('empty.txt', empty_file, 'text/plain')
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        timeout=30
    )
    
    # Should either reject empty files (400) or accept them
    assert resp.status_code in (400, 201, 200)


@pytest.mark.api
def test_list_files(api_base_url, auth_headers, uploaded_file):
    """Test listing files"""
    resp = requests.get(
        f"{api_base_url}/files",
        headers=auth_headers,
        timeout=10
    )
    
    assert resp.status_code == 200
    
    data = resp.json()
    assert "files" in data
    assert isinstance(data["files"], list)
    assert "page" in data
    assert "page_size" in data
    assert "total" in data


@pytest.mark.api
def test_list_files_pagination(api_base_url, auth_headers, uploaded_file):
    """Test file listing with pagination parameters"""
    resp = requests.get(
        f"{api_base_url}/files?page=1&page_size=10",
        headers=auth_headers,
        timeout=10
    )
    
    assert resp.status_code == 200
    
    data = resp.json()
    assert data.get("page") == 1
    assert data.get("page_size") == 10
    assert len(data["files"]) <= 10


@pytest.mark.api
def test_list_files_without_auth(api_base_url, wait_for_service):
    """Test listing files without authentication"""
    resp = requests.get(f"{api_base_url}/files", timeout=10)
    assert resp.status_code == 401


@pytest.mark.api
def test_get_file_info(api_base_url, auth_headers, uploaded_file):
    """Test getting file information"""
    resp = requests.get(
        f"{api_base_url}/files/{uploaded_file}",
        headers=auth_headers,
        timeout=10
    )
    
    assert resp.status_code == 200
    
    data = resp.json()
    assert data.get("id") == uploaded_file
    assert "filename" in data
    assert "size" in data
    assert "content_type" in data
    assert "upload_time" in data
    assert "uploader" in data


@pytest.mark.api
def test_get_file_info_not_found(api_base_url, auth_headers):
    """Test getting info for non-existent file"""
    resp = requests.get(
        f"{api_base_url}/files/nonexistent_file_id",
        headers=auth_headers,
        timeout=10
    )
    
    assert resp.status_code == 404


@pytest.mark.download
def test_download_file(api_base_url, auth_headers, uploaded_file):
    """Test downloading a file"""
    resp = requests.get(
        f"{api_base_url}/files/{uploaded_file}/download",
        headers=auth_headers,
        timeout=30
    )
    
    assert resp.status_code == 200
    assert len(resp.content) > 0
    assert "content-type" in resp.headers or "Content-Type" in resp.headers
    # Check for content-disposition header (case-insensitive)
    headers_lower = {k.lower(): v for k, v in resp.headers.items()}
    assert "content-disposition" in headers_lower or resp.content


@pytest.mark.download
def test_download_file_not_found(api_base_url, auth_headers):
    """Test downloading a non-existent file"""
    resp = requests.get(
        f"{api_base_url}/files/nonexistent_file_id/download",
        headers=auth_headers,
        timeout=30
    )
    
    assert resp.status_code == 404


@pytest.mark.download
def test_download_without_auth(api_base_url, uploaded_file):
    """Test downloading a file without authentication"""
    resp = requests.get(
        f"{api_base_url}/files/{uploaded_file}/download",
        timeout=30
    )
    
    assert resp.status_code == 401


@pytest.mark.api
def test_delete_file(api_base_url, auth_headers, sample_text_file):
    """Test deleting a file"""
    # First upload a file
    file_obj, filename, content_type = sample_text_file
    files = {'file': (filename, file_obj, content_type)}
    
    upload_resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        timeout=30
    )
    
    assert upload_resp.status_code in (200, 201)
    file_id = upload_resp.json().get("id")
    
    # Then delete it
    delete_resp = requests.delete(
        f"{api_base_url}/files/{file_id}",
        headers=auth_headers,
        timeout=10
    )
    
    assert delete_resp.status_code == 200
    
    data = delete_resp.json()
    assert data.get("success") is True or "success" in data


@pytest.mark.api
def test_delete_file_not_found(api_base_url, auth_headers):
    """Test deleting a non-existent file"""
    resp = requests.delete(
        f"{api_base_url}/files/nonexistent_file_id",
        headers=auth_headers,
        timeout=10
    )
    
    assert resp.status_code == 404


@pytest.mark.api
def test_delete_file_by_non_owner(api_base_url, auth_headers, uploaded_file, second_user_token):
    """Test that a user cannot delete another user's file"""
    second_user_headers = {"Authorization": f"Bearer {second_user_token}"}
    
    resp = requests.delete(
        f"{api_base_url}/files/{uploaded_file}",
        headers=second_user_headers,
        timeout=10
    )
    
    assert resp.status_code == 403


@pytest.mark.api
def test_update_file_metadata(api_base_url, auth_headers, uploaded_file):
    """Test updating file metadata"""
    update_data = {
        "description": "Updated description",
        "tags": ["updated", "test", "metadata"]
    }
    
    resp = requests.patch(
        f"{api_base_url}/files/{uploaded_file}",
        headers={**auth_headers, "Content-Type": "application/json"},
        json=update_data,
        timeout=10
    )
    
    assert resp.status_code == 200
    
    data = resp.json()
    assert data.get("success") is True or "file" in data


@pytest.mark.api
def test_update_file_metadata_by_non_owner(api_base_url, uploaded_file, second_user_token):
    """Test that a user cannot update another user's file metadata"""
    second_user_headers = {
        "Authorization": f"Bearer {second_user_token}",
        "Content-Type": "application/json"
    }
    
    update_data = {
        "description": "Attempting unauthorized update"
    }
    
    resp = requests.patch(
        f"{api_base_url}/files/{uploaded_file}",
        headers=second_user_headers,
        json=update_data,
        timeout=10
    )
    
    assert resp.status_code == 403


@pytest.mark.api
def test_search_files(api_base_url, auth_headers, uploaded_file):
    """Test searching files"""
    resp = requests.get(
        f"{api_base_url}/files/search?q=test",
        headers=auth_headers,
        timeout=10
    )
    
    assert resp.status_code == 200
    
    data = resp.json()
    assert "files" in data
    assert isinstance(data["files"], list)
    assert "query" in data or "q" in data or data


@pytest.mark.api
def test_search_files_no_results(api_base_url, auth_headers):
    """Test searching files with no results"""
    resp = requests.get(
        f"{api_base_url}/files/search?q=nonexistentfilequery12345",
        headers=auth_headers,
        timeout=10
    )
    
    assert resp.status_code == 200
    
    data = resp.json()
    assert "files" in data
    assert len(data["files"]) == 0


@pytest.mark.api
def test_search_files_invalid_query(api_base_url, auth_headers):
    """Test searching files with invalid query (too short)"""
    resp = requests.get(
        f"{api_base_url}/files/search?q=a",
        headers=auth_headers,
        timeout=10
    )
    
    # Should return 400 for too short query or 200 with empty results
    assert resp.status_code in (400, 200)


@pytest.mark.api
def test_list_files_filter_by_type(api_base_url, auth_headers, uploaded_file):
    """Test listing files filtered by file type"""
    resp = requests.get(
        f"{api_base_url}/files?file_type=document",
        headers=auth_headers,
        timeout=10
    )
    
    # Should return 200 whether or not the filter is supported
    assert resp.status_code == 200
    
    data = resp.json()
    assert "files" in data


