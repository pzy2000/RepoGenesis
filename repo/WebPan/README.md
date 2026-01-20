# WebPan - File Storage and Sharing Service

## Functionality Description

WebPan is a web-based file storage and sharing service that provides file upload, download, management, and sharing functionality. The service supports multiple file types including documents, images, videos, etc., and provides secure access control and sharing mechanisms.

### Core Features
- File Upload: Supports single and multiple file uploads
- File Download: Provides secure file download interfaces
- File Management: File list viewing, deletion, renaming
- File Sharing: Generate sharing links, supports public and private sharing
- User Authentication: Token-based user identity verification
- Storage Management: File storage space management and quota control

## API Definition

### Service Configuration
- **Listening Port**: 8080
- **Base Path**: `/api/v1`
- **Authentication Method**: Bearer Token

### API Interfaces

#### 1. User Authentication APIs

**POST** `/api/v1/auth/login`
- **Function**: User login to get access token
- **Input Schema**:
```json
{
  "username": "string",
  "password": "string"
}
```
- **Output Schema**:
```json
{
  "success": true,
  "token": "string",
  "user_id": "string",
  "expires_in": 3600
}
```

**POST** `/api/v1/auth/register`
- **Function**: User registration
- **Input Schema**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```
- **Output Schema**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": "string"
}
```

#### 2. File Upload APIs

**POST** `/api/v1/files/upload`
- **Function**: Upload single file
- **Authentication**: Bearer Token required
- **Input Schema**: multipart/form-data
```json
{
  "file": "file",
  "folder_id": "string (optional)",
  "description": "string (optional)"
}
```
- **Output Schema**:
```json
{
  "success": true,
  "file_id": "string",
  "filename": "string",
  "size": 1024,
  "upload_time": "2024-01-01T12:00:00Z",
  "download_url": "string"
}
```

**POST** `/api/v1/files/upload-multiple`
- **Function**: Batch upload multiple files
- **Authentication**: Bearer Token required
- **Input Schema**: multipart/form-data
```json
{
  "files": "file[]",
  "folder_id": "string (optional)"
}
```
- **Output Schema**:
```json
{
  "success": true,
  "uploaded_files": [
    {
      "file_id": "string",
      "filename": "string",
      "size": 1024,
      "status": "success"
    }
  ],
  "failed_files": [
    {
      "filename": "string",
      "error": "string"
    }
  ]
}
```

#### 3. File Download APIs

**GET** `/api/v1/files/{file_id}/download`
- **Function**: Download specified file
- **Authentication**: Bearer Token or share token required
- **Input Schema**: URL parameters
```
file_id: string (path parameter)
```
- **Output Schema**: File stream or error response
```json
{
  "success": false,
  "error": "File not found"
}
```

**GET** `/api/v1/files/{file_id}/info`
- **Function**: Get file information
- **Authentication**: Bearer Token required
- **Input Schema**: URL parameters
```
file_id: string (path parameter)
```
- **Output Schema**:
```json
{
  "success": true,
  "file_id": "string",
  "filename": "string",
  "size": 1024,
  "mime_type": "string",
  "upload_time": "2024-01-01T12:00:00Z",
  "download_count": 0,
  "owner_id": "string"
}
```

#### 4. File Management APIs

**GET** `/api/v1/files`
- **Function**: Get user file list
- **Authentication**: Bearer Token required
- **Input Schema**: Query parameters
```
page: integer (optional, default: 1)
limit: integer (optional, default: 20)
folder_id: string (optional)
sort_by: string (optional, values: name, size, upload_time)
order: string (optional, values: asc, desc)
```
- **Output Schema**:
```json
{
  "success": true,
  "files": [
    {
      "file_id": "string",
      "filename": "string",
      "size": 1024,
      "mime_type": "string",
      "upload_time": "2024-01-01T12:00:00Z",
      "download_count": 0
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

**DELETE** `/api/v1/files/{file_id}`
- **Function**: Delete specified file
- **Authentication**: Bearer Token required
- **Input Schema**: URL parameters
```
file_id: string (path parameter)
```
- **Output Schema**:
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

**PUT** `/api/v1/files/{file_id}/rename`
- **Function**: Rename file
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "new_name": "string"
}
```
- **Output Schema**:
```json
{
  "success": true,
  "message": "File renamed successfully",
  "new_filename": "string"
}
```

#### 5. File Sharing APIs

**POST** `/api/v1/files/{file_id}/share`
- **Function**: Create file sharing link
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "is_public": true,
  "expires_in": 3600,
  "password": "string (optional)"
}
```
- **Output Schema**:
```json
{
  "success": true,
  "share_id": "string",
  "share_url": "string",
  "expires_at": "2024-01-01T13:00:00Z",
  "access_count": 0
}
```

**GET** `/api/v1/share/{share_id}`
- **Function**: Access file through sharing link
- **Authentication**: Optional (if password is set)
- **Input Schema**: URL parameters
```
share_id: string (path parameter)
password: string (query parameter, optional)
```
- **Output Schema**:
```json
{
  "success": true,
  "file_info": {
    "filename": "string",
    "size": 1024,
    "mime_type": "string"
  },
  "download_url": "string"
}
```

**DELETE** `/api/v1/share/{share_id}`
- **Function**: Delete sharing link
- **Authentication**: Bearer Token required
- **Input Schema**: URL parameters
```
share_id: string (path parameter)
```
- **Output Schema**:
```json
{
  "success": true,
  "message": "Share link deleted successfully"
}
```

#### 6. Storage Management APIs

**GET** `/api/v1/storage/quota`
- **Function**: Get user storage quota information
- **Authentication**: Bearer Token required
- **Input Schema**: None
- **Output Schema**:
```json
{
  "success": true,
  "used_space": 1024000,
  "total_space": 10485760,
  "available_space": 9461760,
  "usage_percentage": 9.8
}
```

## Error Response Format

All interfaces return unified error format when errors occur:

```json
{
  "success": false,
  "error": "string",
  "error_code": "string",
  "details": "string (optional)"
}
```

### Common Error Codes
- `AUTH_REQUIRED`: Authentication required
- `AUTH_INVALID`: Authentication failed
- `FILE_NOT_FOUND`: File not found
- `FILE_TOO_LARGE`: File too large
- `QUOTA_EXCEEDED`: Storage quota exceeded
- `INVALID_FORMAT`: File format not supported
- `SHARE_EXPIRED`: Share link expired
- `SHARE_NOT_FOUND`: Share link not found

## Technical Specifications

### File Limitations
- Maximum single file size: 100MB
- Supported file types: All common formats
- User storage quota: 10GB (default)

### Security Requirements
- All file uploads require authentication
- Sharing links support password protection
- File access logging and audit logs
- Prevent malicious file uploads

### Performance Requirements
- File upload response time: <5 seconds (10MB file)
- File download response time: <2 seconds
- Concurrent user support: 100+
- System availability: 99.9%
