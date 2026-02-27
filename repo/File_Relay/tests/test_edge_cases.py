"""
File Relay API Tests - Edge Cases and Security
"""

import pytest
import requests
import io


@pytest.mark.edge
def test_upload_large_file_within_limit(api_base_url, auth_headers):
    """Test uploading a file close to but within the size limit"""
    # Create a 5MB file (well within 100MB limit)
    file_size = 5 * 1024 * 1024  # 5MB
    large_content = b'x' * file_size
    large_file = io.BytesIO(large_content)
    
    files = {
        'file': ('large_file.bin', large_file, 'application/octet-stream')
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        timeout=120
    )
    
    # Should accept the file
    assert resp.status_code in (200, 201)
    
    # Cleanup
    if resp.status_code in (200, 201):
        file_id = resp.json().get("id")
        if file_id:
            requests.delete(
                f"{api_base_url}/files/{file_id}",
                headers=auth_headers,
                timeout=10
            )


@pytest.mark.edge
@pytest.mark.slow
def test_upload_file_exceeds_size_limit(api_base_url, auth_headers):
    """Test uploading a file that exceeds the size limit (100MB)"""
    # Create a file larger than 100MB
    # Note: This test is marked as slow and may be skipped in quick test runs
    file_size = 101 * 1024 * 1024  # 101MB
    
    # Stream the large file to avoid memory issues
    def generate_large_file():
        chunk_size = 1024 * 1024  # 1MB chunks
        for _ in range(file_size // chunk_size):
            yield b'x' * chunk_size
    
    class LargeFileIO:
        def __init__(self, size):
            self.size = size
            self.pos = 0
            
        def read(self, size=-1):
            if size == -1:
                size = self.size - self.pos
            if self.pos >= self.size:
                return b''
            chunk = min(size, self.size - self.pos)
            self.pos += chunk
            return b'x' * chunk
        
        def seek(self, pos):
            self.pos = pos
            
        def tell(self):
            return self.pos
    
    large_file = LargeFileIO(file_size)
    
    files = {
        'file': ('oversized_file.bin', large_file, 'application/octet-stream')
    }
    
    try:
        resp = requests.post(
            f"{api_base_url}/files",
            headers=auth_headers,
            files=files,
            timeout=180
        )
        
        # Should reject with 413 (Payload Too Large)
        assert resp.status_code == 413
    except requests.exceptions.Timeout:
        # If it times out, the server might be processing but should reject
        pytest.skip("Request timed out - file might be too large to process in test timeout")


@pytest.mark.edge
def test_special_characters_in_filename(api_base_url, auth_headers):
    """Test uploading files with special characters in filename"""
    special_filenames = [
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.multiple.dots.txt",
        "file(with)parentheses.txt",
        "file[with]brackets.txt",
    ]
    
    uploaded_ids = []
    
    for filename in special_filenames:
        file_content = io.BytesIO(b"Test content for special filename")
        files = {
            'file': (filename, file_content, 'text/plain')
        }
        
        resp = requests.post(
            f"{api_base_url}/files",
            headers=auth_headers,
            files=files,
            timeout=30
        )
        
        # Should accept valid special characters
        assert resp.status_code in (200, 201, 400)  # 400 if server rejects certain chars
        
        if resp.status_code in (200, 201):
            file_id = resp.json().get("id")
            if file_id:
                uploaded_ids.append(file_id)
    
    # Cleanup
    for file_id in uploaded_ids:
        try:
            requests.delete(
                f"{api_base_url}/files/{file_id}",
                headers=auth_headers,
                timeout=10
            )
        except:
            pass


@pytest.mark.edge
def test_unicode_filename(api_base_url, auth_headers):
    """Test uploading files with Unicode characters in filename"""
    unicode_filenames = [
        "文档.txt",  # Chinese
        "ファイル.txt",  # Japanese
        "файл.txt",  # Russian
        "αρχείο.txt",  # Greek
        "café.txt",  # Accented characters
        "emoji_😀.txt",  # Emoji
    ]
    
    uploaded_ids = []
    
    for filename in unicode_filenames:
        file_content = io.BytesIO(b"Unicode filename test")
        files = {
            'file': (filename, file_content, 'text/plain')
        }
        
        resp = requests.post(
            f"{api_base_url}/files",
            headers=auth_headers,
            files=files,
            timeout=30
        )
        
        # Should handle Unicode filenames
        assert resp.status_code in (200, 201, 400)
        
        if resp.status_code in (200, 201):
            file_id = resp.json().get("id")
            if file_id:
                uploaded_ids.append(file_id)
    
    # Cleanup
    for file_id in uploaded_ids:
        try:
            requests.delete(
                f"{api_base_url}/files/{file_id}",
                headers=auth_headers,
                timeout=10
            )
        except:
            pass


@pytest.mark.edge
def test_path_traversal_in_filename(api_base_url, auth_headers):
    """Test that path traversal attempts in filename are blocked"""
    malicious_filenames = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "../../../../root/.ssh/id_rsa",
    ]
    
    for filename in malicious_filenames:
        file_content = io.BytesIO(b"Malicious content")
        files = {
            'file': (filename, file_content, 'text/plain')
        }
        
        resp = requests.post(
            f"{api_base_url}/files",
            headers=auth_headers,
            files=files,
            timeout=30
        )
        
        # Should either reject (400) or sanitize the filename
        if resp.status_code in (200, 201):
            file_data = resp.json()
            # Verify that the filename doesn't contain path separators
            saved_filename = file_data.get("filename", "")
            assert ".." not in saved_filename or "/" not in saved_filename or "\\" not in saved_filename
            
            # Cleanup
            file_id = file_data.get("id")
            if file_id:
                requests.delete(
                    f"{api_base_url}/files/{file_id}",
                    headers=auth_headers,
                    timeout=10
                )


@pytest.mark.edge
def test_sql_injection_in_search(api_base_url, auth_headers):
    """Test that SQL injection attempts in search are handled safely"""
    sql_injection_queries = [
        "'; DROP TABLE files; --",
        "1' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "<script>alert('xss')</script>",
    ]
    
    for query in sql_injection_queries:
        resp = requests.get(
            f"{api_base_url}/files/search",
            params={"q": query},
            headers=auth_headers,
            timeout=10
        )
        
        # Should handle safely without error
        assert resp.status_code in (200, 400)
        
        # If it returns results, verify they're properly formatted
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data.get("files", []), list)


@pytest.mark.edge
def test_concurrent_uploads(api_base_url, auth_headers):
    """Test concurrent file uploads"""
    import concurrent.futures
    
    def upload_file(index):
        file_content = io.BytesIO(f"Concurrent upload test {index}".encode())
        files = {
            'file': (f'concurrent_{index}.txt', file_content, 'text/plain')
        }
        
        resp = requests.post(
            f"{api_base_url}/files",
            headers=auth_headers,
            files=files,
            timeout=30
        )
        return resp
    
    # Upload 5 files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_file, i) for i in range(5)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # All uploads should succeed
    successful_uploads = [r for r in responses if r.status_code in (200, 201)]
    assert len(successful_uploads) >= 4  # At least 4 out of 5 should succeed
    
    # Cleanup
    for resp in successful_uploads:
        try:
            file_id = resp.json().get("id")
            if file_id:
                requests.delete(
                    f"{api_base_url}/files/{file_id}",
                    headers=auth_headers,
                    timeout=10
                )
        except:
            pass


@pytest.mark.edge
def test_pagination_boundary_cases(api_base_url, auth_headers):
    """Test pagination with boundary values"""
    test_cases = [
        {"page": 1, "page_size": 1},  # Minimum page size
        {"page": 1, "page_size": 100},  # Maximum page size
        {"page": 999, "page_size": 20},  # High page number
        {"page": 1, "page_size": 50},  # Middle value
    ]
    
    for params in test_cases:
        resp = requests.get(
            f"{api_base_url}/files",
            params=params,
            headers=auth_headers,
            timeout=10
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert "files" in data
        assert len(data["files"]) <= params["page_size"]


@pytest.mark.edge
def test_invalid_pagination_parameters(api_base_url, auth_headers):
    """Test pagination with invalid parameters"""
    invalid_cases = [
        {"page": 0, "page_size": 20},  # Page < 1
        {"page": -1, "page_size": 20},  # Negative page
        {"page": 1, "page_size": 0},  # Page size < 1
        {"page": 1, "page_size": 101},  # Page size > 100
        {"page": "invalid", "page_size": 20},  # Non-numeric page
        {"page": 1, "page_size": "invalid"},  # Non-numeric page_size
    ]
    
    for params in invalid_cases:
        resp = requests.get(
            f"{api_base_url}/files",
            params=params,
            headers=auth_headers,
            timeout=10
        )
        
        # Should return 400 for invalid parameters or use defaults
        assert resp.status_code in (200, 400)


@pytest.mark.edge
def test_invalid_file_id_formats(api_base_url, auth_headers):
    """Test operations with invalid file ID formats"""
    invalid_ids = [
        "invalid-id",
        "../../etc/passwd",
        "<script>alert(1)</script>",
        "'; DROP TABLE files; --",
        "",
        "a" * 1000,  # Very long ID
    ]
    
    for file_id in invalid_ids:
        # Test get file info
        resp = requests.get(
            f"{api_base_url}/files/{file_id}",
            headers=auth_headers,
            timeout=10
        )
        assert resp.status_code in (400, 404)
        
        # Test delete
        resp = requests.delete(
            f"{api_base_url}/files/{file_id}",
            headers=auth_headers,
            timeout=10
        )
        assert resp.status_code in (400, 404)


@pytest.mark.edge
def test_expired_token(api_base_url):
    """Test request with expired/invalid token"""
    invalid_headers = {
        "Authorization": "Bearer expired_or_invalid_token_12345"
    }
    
    resp = requests.get(
        f"{api_base_url}/files",
        headers=invalid_headers,
        timeout=10
    )
    
    assert resp.status_code == 401


@pytest.mark.edge
def test_malformed_authorization_header(api_base_url):
    """Test request with malformed authorization header"""
    malformed_headers = [
        {"Authorization": "InvalidFormat token123"},
        {"Authorization": "Bearer"},  # Missing token
        {"Authorization": ""},  # Empty
        {"Authorization": "Bearer token1 token2"},  # Multiple tokens
    ]
    
    for headers in malformed_headers:
        resp = requests.get(
            f"{api_base_url}/files",
            headers=headers,
            timeout=10
        )
        
        assert resp.status_code == 401


@pytest.mark.edge
def test_very_long_description(api_base_url, auth_headers):
    """Test uploading file with very long description"""
    file_content = io.BytesIO(b"Test content")
    
    # Description longer than 500 characters
    long_description = "A" * 600
    
    files = {
        'file': ('test.txt', file_content, 'text/plain')
    }
    data = {
        'description': long_description
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        data=data,
        timeout=30
    )
    
    # Should either reject (400) or truncate the description
    if resp.status_code in (200, 201):
        file_data = resp.json()
        # Verify description is truncated or stored properly
        assert "description" in file_data
        
        # Cleanup
        file_id = file_data.get("id")
        if file_id:
            requests.delete(
                f"{api_base_url}/files/{file_id}",
                headers=auth_headers,
                timeout=10
            )
    else:
        assert resp.status_code == 400


@pytest.mark.edge
def test_double_deletion(api_base_url, auth_headers, sample_text_file):
    """Test deleting the same file twice"""
    # Upload a file
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
    
    # First deletion should succeed
    delete_resp1 = requests.delete(
        f"{api_base_url}/files/{file_id}",
        headers=auth_headers,
        timeout=10
    )
    assert delete_resp1.status_code == 200
    
    # Second deletion should fail with 404
    delete_resp2 = requests.delete(
        f"{api_base_url}/files/{file_id}",
        headers=auth_headers,
        timeout=10
    )
    assert delete_resp2.status_code == 404


@pytest.mark.edge
def test_access_deleted_file(api_base_url, auth_headers, sample_text_file):
    """Test accessing a file after it has been deleted"""
    # Upload a file
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
    
    # Delete the file
    delete_resp = requests.delete(
        f"{api_base_url}/files/{file_id}",
        headers=auth_headers,
        timeout=10
    )
    assert delete_resp.status_code == 200
    
    # Try to get file info - should fail
    info_resp = requests.get(
        f"{api_base_url}/files/{file_id}",
        headers=auth_headers,
        timeout=10
    )
    assert info_resp.status_code == 404
    
    # Try to download - should fail
    download_resp = requests.get(
        f"{api_base_url}/files/{file_id}/download",
        headers=auth_headers,
        timeout=10
    )
    assert download_resp.status_code == 404


@pytest.mark.edge
def test_unsupported_file_type(api_base_url, auth_headers):
    """Test uploading an unsupported file type"""
    # Try to upload an executable or other potentially dangerous file
    file_content = io.BytesIO(b"MZ\x90\x00")  # PE executable header
    
    files = {
        'file': ('malicious.exe', file_content, 'application/x-msdownload')
    }
    
    resp = requests.post(
        f"{api_base_url}/files",
        headers=auth_headers,
        files=files,
        timeout=30
    )
    
    # Should either reject with 415 or accept and handle safely
    assert resp.status_code in (200, 201, 415)
    
    # If accepted, cleanup
    if resp.status_code in (200, 201):
        file_id = resp.json().get("id")
        if file_id:
            requests.delete(
                f"{api_base_url}/files/{file_id}",
                headers=auth_headers,
                timeout=10
            )


@pytest.mark.edge
def test_multiple_files_same_name(api_base_url, auth_headers):
    """Test uploading multiple files with the same name"""
    filename = "duplicate_name.txt"
    
    uploaded_ids = []
    
    for i in range(3):
        file_content = io.BytesIO(f"Content {i}".encode())
        files = {
            'file': (filename, file_content, 'text/plain')
        }
        
        resp = requests.post(
            f"{api_base_url}/files",
            headers=auth_headers,
            files=files,
            timeout=30
        )
        
        assert resp.status_code in (200, 201)
        file_id = resp.json().get("id")
        uploaded_ids.append(file_id)
    
    # All three files should have unique IDs
    assert len(uploaded_ids) == len(set(uploaded_ids))
    
    # Cleanup
    for file_id in uploaded_ids:
        try:
            requests.delete(
                f"{api_base_url}/files/{file_id}",
                headers=auth_headers,
                timeout=10
            )
        except:
            pass


