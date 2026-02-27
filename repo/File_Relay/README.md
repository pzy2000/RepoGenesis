# File Relay Service

## Project Overview

File Relay is a microservice for file upload, download, and management. It supports various file types including images, videos, documents, and other binary files. The service provides RESTful APIs for file operations with proper authentication, file type validation, and size limitation.

## Functional Requirements

The File Relay service implements the following core functionalities:

1. **File Upload**: Upload files to the server with automatic storage and metadata tracking
2. **File Download**: Download files by ID with proper content type headers
3. **File Listing**: Query and list uploaded files with pagination support
4. **File Information**: Retrieve metadata for specific files
5. **File Deletion**: Remove files from storage
6. **Authentication**: Token-based authentication for secure file operations
7. **File Type Support**: Images (JPEG, PNG, GIF, BMP), Videos (MP4, AVI, MOV, MKV), Documents (PDF, DOC, DOCX, TXT, XLS, XLSX), Archives (ZIP, RAR, TAR, GZ)

## API Specifications

### Service Configuration

- **Port**: 8085
- **Protocol**: HTTP/1.1
- **Base Path**: `/api/v1`
- **Content-Type**: application/json (for metadata), multipart/form-data (for file upload)

### Endpoints

#### 1. Health Check

**Endpoint**: `GET /api/v1/health`

**Description**: Check service health status

**Input Schema**: None

**Output Schema**:
```json
{
  "status": "string",
  "service": "string",
  "version": "string"
}
```

**Example Response**:
```json
{
  "status": "ok",
  "service": "file-relay",
  "version": "1.0.0"
}
```

#### 2. User Registration

**Endpoint**: `POST /api/v1/auth/register`

**Description**: Register a new user for file operations

**Input Schema**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Constraints**:
- `username`: 3-32 characters, alphanumeric and underscores only
- `password`: minimum 8 characters

**Output Schema**:
```json
{
  "id": "string",
  "username": "string",
  "created_at": "string"
}
```

**Status Codes**:
- 201: User created successfully
- 400: Invalid input
- 409: Username already exists

**Example Request**:
```json
{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

**Example Response**:
```json
{
  "id": "usr_123456",
  "username": "john_doe",
  "created_at": "2025-10-16T10:30:00Z"
}
```

#### 3. User Login

**Endpoint**: `POST /api/v1/auth/login`

**Description**: Login and receive an access token

**Input Schema**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Output Schema**:
```json
{
  "access_token": "string",
  "token_type": "string"
}
```

**Status Codes**:
- 200: Login successful
- 401: Invalid credentials

**Example Request**:
```json
{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

**Example Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

#### 4. Upload File

**Endpoint**: `POST /api/v1/files`

**Description**: Upload a file to the server

**Authentication**: Bearer Token required

**Input Schema**: multipart/form-data
- `file`: Binary file data (required)
- `description`: Text description (optional, max 500 characters)
- `tags`: Comma-separated tags (optional)

**Output Schema**:
```json
{
  "id": "string",
  "filename": "string",
  "size": "integer",
  "content_type": "string",
  "upload_time": "string",
  "uploader": "string",
  "description": "string",
  "tags": "array",
  "download_url": "string"
}
```

**Status Codes**:
- 201: File uploaded successfully
- 400: Invalid file or missing file
- 401: Unauthorized
- 413: File too large (max 100MB)
- 415: Unsupported file type

**Supported File Types**:
- Images: .jpg, .jpeg, .png, .gif, .bmp, .webp
- Videos: .mp4, .avi, .mov, .mkv, .flv, .wmv
- Documents: .pdf, .doc, .docx, .txt, .xls, .xlsx, .ppt, .pptx
- Archives: .zip, .rar, .tar, .gz, .7z

**File Size Limit**: 100MB per file

**Example Response**:
```json
{
  "id": "file_789abc",
  "filename": "presentation.pdf",
  "size": 2048576,
  "content_type": "application/pdf",
  "upload_time": "2025-10-16T10:35:00Z",
  "uploader": "john_doe",
  "description": "Q4 Sales Presentation",
  "tags": ["sales", "q4", "presentation"],
  "download_url": "/api/v1/files/file_789abc/download"
}
```

#### 5. List Files

**Endpoint**: `GET /api/v1/files`

**Description**: List uploaded files with pagination

**Authentication**: Bearer Token required

**Query Parameters**:
- `page`: Page number (integer, minimum 1, default 1)
- `page_size`: Items per page (integer, 1-100, default 20)
- `file_type`: Filter by file type (optional, values: image, video, document, archive, other)
- `uploader`: Filter by uploader username (optional)

**Output Schema**:
```json
{
  "files": "array",
  "page": "integer",
  "page_size": "integer",
  "total": "integer",
  "total_pages": "integer"
}
```

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 400: Invalid query parameters

**Example Response**:
```json
{
  "files": [
    {
      "id": "file_789abc",
      "filename": "presentation.pdf",
      "size": 2048576,
      "content_type": "application/pdf",
      "upload_time": "2025-10-16T10:35:00Z",
      "uploader": "john_doe"
    },
    {
      "id": "file_456def",
      "filename": "logo.png",
      "size": 102400,
      "content_type": "image/png",
      "upload_time": "2025-10-16T09:20:00Z",
      "uploader": "jane_smith"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 45,
  "total_pages": 3
}
```

#### 6. Get File Information

**Endpoint**: `GET /api/v1/files/{file_id}`

**Description**: Get detailed information about a specific file

**Authentication**: Bearer Token required

**Input Schema**: Path parameter `file_id` (string)

**Output Schema**:
```json
{
  "id": "string",
  "filename": "string",
  "size": "integer",
  "content_type": "string",
  "upload_time": "string",
  "uploader": "string",
  "description": "string",
  "tags": "array",
  "download_url": "string",
  "checksum": "string"
}
```

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 404: File not found

**Example Response**:
```json
{
  "id": "file_789abc",
  "filename": "presentation.pdf",
  "size": 2048576,
  "content_type": "application/pdf",
  "upload_time": "2025-10-16T10:35:00Z",
  "uploader": "john_doe",
  "description": "Q4 Sales Presentation",
  "tags": ["sales", "q4", "presentation"],
  "download_url": "/api/v1/files/file_789abc/download",
  "checksum": "sha256:a3f2b..."
}
```

#### 7. Download File

**Endpoint**: `GET /api/v1/files/{file_id}/download`

**Description**: Download a file by its ID

**Authentication**: Bearer Token required

**Input Schema**: Path parameter `file_id` (string)

**Output**: Binary file data with appropriate Content-Type and Content-Disposition headers

**Headers**:
- `Content-Type`: File's MIME type
- `Content-Disposition`: attachment; filename="original_filename"
- `Content-Length`: File size in bytes

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 404: File not found

#### 8. Delete File

**Endpoint**: `DELETE /api/v1/files/{file_id}`

**Description**: Delete a file (only the uploader or admin can delete)

**Authentication**: Bearer Token required

**Input Schema**: Path parameter `file_id` (string)

**Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "file_id": "string"
}
```

**Status Codes**:
- 200: File deleted successfully
- 401: Unauthorized
- 403: Forbidden (not the owner)
- 404: File not found

**Example Response**:
```json
{
  "success": true,
  "message": "File deleted successfully",
  "file_id": "file_789abc"
}
```

#### 9. Update File Metadata

**Endpoint**: `PATCH /api/v1/files/{file_id}`

**Description**: Update file description and tags

**Authentication**: Bearer Token required

**Input Schema**:
```json
{
  "description": "string",
  "tags": "array"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "file": "object"
}
```

**Status Codes**:
- 200: Updated successfully
- 401: Unauthorized
- 403: Forbidden (not the owner)
- 404: File not found

**Example Request**:
```json
{
  "description": "Updated Q4 Sales Presentation",
  "tags": ["sales", "q4", "presentation", "updated"]
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "File metadata updated successfully",
  "file": {
    "id": "file_789abc",
    "filename": "presentation.pdf",
    "description": "Updated Q4 Sales Presentation",
    "tags": ["sales", "q4", "presentation", "updated"]
  }
}
```

#### 10. Search Files

**Endpoint**: `GET /api/v1/files/search`

**Description**: Search files by filename or tags

**Authentication**: Bearer Token required

**Query Parameters**:
- `q`: Search query (string, minimum 2 characters)
- `page`: Page number (integer, minimum 1, default 1)
- `page_size`: Items per page (integer, 1-100, default 20)

**Output Schema**:
```json
{
  "files": "array",
  "query": "string",
  "page": "integer",
  "page_size": "integer",
  "total": "integer"
}
```

**Status Codes**:
- 200: Success
- 400: Invalid query
- 401: Unauthorized

**Example Response**:
```json
{
  "files": [
    {
      "id": "file_789abc",
      "filename": "presentation.pdf",
      "size": 2048576,
      "content_type": "application/pdf",
      "upload_time": "2025-10-16T10:35:00Z",
      "uploader": "john_doe"
    }
  ],
  "query": "presentation",
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

## Error Responses

All endpoints should return standard error responses:

**Schema**:
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object"
  }
}
```

**Common Error Codes**:

- `INVALID_REQUEST`: Invalid request parameters (HTTP 400)
- `UNAUTHORIZED`: Missing or invalid authentication (HTTP 401)
- `FORBIDDEN`: Insufficient permissions (HTTP 403)
- `NOT_FOUND`: Resource not found (HTTP 404)
- `CONFLICT`: Resource already exists (HTTP 409)
- `FILE_TOO_LARGE`: File exceeds size limit (HTTP 413)
- `UNSUPPORTED_TYPE`: Unsupported file type (HTTP 415)
- `INTERNAL_ERROR`: Server error (HTTP 500)

**Example Error Response**:
```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds the maximum allowed limit of 100MB",
    "details": {
      "file_size": 150000000,
      "max_size": 104857600
    }
  }
}
```

## Implementation Requirements

1. The service must be implemented as a web application
2. All endpoints must return JSON responses (except file download)
3. File storage must be persistent
4. User authentication must be secure (hashed passwords)
5. File uploads must be validated for type and size
6. Concurrent requests must be handled safely
7. Error handling must be comprehensive
8. Logging should capture all operations

## Running Tests

```bash
# Navigate to the tests directory
cd tests

# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest -v

# Run specific test file
pytest test_file_api.py -v

# Run with coverage
pytest --cov=.. --cov-report=html

# Run edge case tests only
pytest test_edge_cases.py -v
```

## Success Criteria

A successful implementation must:

1. Pass all test cases (100% pass rate)
2. Support all specified file types
3. Enforce file size limits correctly
4. Implement proper authentication and authorization
5. Handle concurrent uploads without data corruption
6. Provide accurate file metadata
7. Support pagination correctly
8. Handle edge cases and errors gracefully
9. Return appropriate HTTP status codes
10. Implement proper file cleanup on deletion

## Notes

- This project is designed as a benchmark for evaluating code generation capabilities
- The implementation should follow RESTful API best practices
- File storage should be organized efficiently (e.g., by date or user)
- Consider implementing file deduplication based on checksum
- Ensure proper cleanup of orphaned files
- Implement proper logging for debugging and auditing


