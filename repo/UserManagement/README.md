# User Management Microservice

## Functionality Description

This is a RESTful API-based user management microservice that provides complete user CRUD operations, authentication, and permission management functionality. The service allows administrators to create, view, update, and delete user accounts, while supporting user status management, role assignment, and password reset functionality.

## API Definition

### Service Configuration
- **Listening Port**: 8081
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`

### API Interfaces

#### 1. Create User
- **API Name**: `POST /api/v1/users`
- **Function**: Create new user account
- **Input Schema**:
```json
{
  "username": "string (required, min 3, max 50 chars, alphanumeric)",
  "email": "string (required, valid email format)",
  "password": "string (required, min 8 chars)",
  "full_name": "string (required, max 100 chars)",
  "role": "string (required, enum: ['user', 'admin', 'moderator'])",
  "phone": "string (optional, valid phone format)"
}
```
- **Output Schema**:
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "role": "string",
  "phone": "string",
  "status": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

#### 2. Get User List
- **API Name**: `GET /api/v1/users`
- **Function**: Get all users list with pagination and filtering
- **Query Parameters**:
  - `page`: integer (optional, default: 1)
  - `limit`: integer (optional, default: 10, max: 100)
  - `status`: string (optional, enum: ['active', 'inactive', 'suspended'])
  - `role`: string (optional, enum: ['user', 'admin', 'moderator'])
  - `search`: string (optional, search in username, email, full_name)
- **Output Schema**:
```json
{
  "users": [
    {
      "id": "integer",
      "username": "string",
      "email": "string",
      "full_name": "string",
      "role": "string",
      "phone": "string",
      "status": "string",
      "created_at": "string",
      "updated_at": "string"
    }
  ],
  "pagination": {
    "page": "integer",
    "limit": "integer",
    "total": "integer",
    "pages": "integer"
  }
}
```

#### 3. Get Single User
- **API Name**: `GET /api/v1/users/{user_id}`
- **Function**: Get detailed information of specific user by user ID
- **Path Parameters**:
  - `user_id`: integer (required)
- **Output Schema**:
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "role": "string",
  "phone": "string",
  "status": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

#### 4. Update User
- **API Name**: `PUT /api/v1/users/{user_id}`
- **Function**: Update specified user information
- **Path Parameters**:
  - `user_id`: integer (required)
- **Input Schema**:
```json
{
  "username": "string (optional, min 3, max 50 chars, alphanumeric)",
  "email": "string (optional, valid email format)",
  "full_name": "string (optional, max 100 chars)",
  "role": "string (optional, enum: ['user', 'admin', 'moderator'])",
  "phone": "string (optional, valid phone format)",
  "status": "string (optional, enum: ['active', 'inactive', 'suspended'])"
}
```
- **Output Schema**:
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "role": "string",
  "phone": "string",
  "status": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

#### 5. Delete User
- **API Name**: `DELETE /api/v1/users/{user_id}`
- **Function**: Delete specified user account
- **Path Parameters**:
  - `user_id`: integer (required)
- **Output Schema**:
```json
{
  "message": "string"
}
```

#### 6. User Login
- **API Name**: `POST /api/v1/auth/login`
- **Function**: User authentication and login
- **Input Schema**:
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```
- **Output Schema**:
```json
{
  "access_token": "string",
  "token_type": "string",
  "expires_in": "integer",
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "role": "string"
  }
}
```

#### 7. Reset Password
- **API Name**: `POST /api/v1/users/{user_id}/reset-password`
- **Function**: Reset specified user's password
- **Path Parameters**:
  - `user_id`: integer (required)
- **Input Schema**:
```json
{
  "new_password": "string (required, min 8 chars)"
}
```
- **Output Schema**:
```json
{
  "message": "string"
}
```

#### 8. Health Check
- **API Name**: `GET /api/v1/health`
- **Function**: Check service health status
- **Output Schema**:
```json
{
  "status": "string",
  "timestamp": "string",
  "version": "string",
  "database": "string"
}
```

## Error Response Format

All interfaces return unified error format when errors occur:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)"
  }
}
```

Common Error Codes:
- `400`: Request parameter error
- `401`: Unauthorized access
- `403`: Insufficient permissions
- `404`: Resource not found
- `409`: Resource conflict (e.g., username or email already exists)
- `422`: Data validation failed
- `500`: Internal server error

## Data Model

### User Entity
- `id`: Primary key, auto-increment integer
- `username`: Username, required, 3-50 characters, alphanumeric combination, unique
- `email`: Email address, required, valid email format, unique
- `password_hash`: Password hash, required, stores encrypted password
- `full_name`: Full name, required, max 100 characters
- `role`: Role, enum values ['user', 'admin', 'moderator'], default 'user'
- `phone`: Phone number, optional, valid phone format
- `status`: Status, enum values ['active', 'inactive', 'suspended'], default 'active'
- `created_at`: Creation time, auto-generated
- `updated_at`: Update time, auto-updated

### Data Validation Rules
- Username: 3-50 characters, only letters, numbers, underscores allowed
- Email: Complies with RFC 5322 standard
- Password: Minimum 8 characters, recommended to include uppercase, lowercase, numbers, special characters
- Phone number: Supports international format, optional
- Full name: 1-100 characters, supports Unicode characters

## Security Requirements

- **Password Security**: Use strong hashing algorithms to store passwords, never return plaintext passwords
- **Input Validation**: Strictly validate all input data to prevent injection attacks
- **Access Control**: Role-based access control, sensitive operations require admin permissions
- **Data Protection**: Encrypt sensitive information storage, API responses don't contain sensitive data
- **Error Handling**: Don't leak internal system information, provide user-friendly error messages

## Technical Specifications

- **Framework**: Supports mainstream web frameworks (Flask, FastAPI, Django, etc.)
- **Database**: Supports relational databases (SQLite, PostgreSQL, MySQL, etc.)
- **Data Validation**: Strict input data validation and type checking
- **Error Handling**: Complete error handling and user-friendly error messages
- **Logging**: Complete operation logging, including security events
- **API Documentation**: Auto-generated API documentation (Swagger/OpenAPI)
- **Test Coverage**: Comprehensive unit tests and integration tests

## Deployment Requirements

- **Port**: Service must listen on port 8081
- **Environment Variables**: Support configuration of database connections, JWT keys, etc. through environment variables
- **Health Check**: Provide health check endpoint for service monitoring
- **Containerization**: Support Docker containerized deployment
- **Database Migration**: Support database schema version management and migration
- **Configuration Management**: Support configuration management for different environments (development, testing, production)
