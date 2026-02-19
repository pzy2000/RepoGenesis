# API Examples

This document provides concrete examples of API requests and responses for the Simple RBAC Service.

## Base URL
```
http://localhost:8080
```

## Example Workflow

### 1. Create Roles

#### Request: Create "admin" role
```bash
curl -X POST http://localhost:8080/api/roles \
  -H "Content-Type: application/json" \
  -d '{"role_name": "admin"}'
```

#### Response:
```json
{
  "status": "success",
  "role_id": "role_001",
  "role_name": "admin"
}
```

#### Request: Create "editor" role
```bash
curl -X POST http://localhost:8080/api/roles \
  -H "Content-Type: application/json" \
  -d '{"role_name": "editor"}'
```

#### Response:
```json
{
  "status": "success",
  "role_id": "role_002",
  "role_name": "editor"
}
```

### 2. Assign Permissions to Roles

#### Request: Assign permissions to admin role
```bash
curl -X POST http://localhost:8080/api/roles/role_001/permissions \
  -H "Content-Type: application/json" \
  -d '{"permissions": ["read", "write", "delete", "admin"]}'
```

#### Response:
```json
{
  "status": "success",
  "role_id": "role_001",
  "permissions": ["read", "write", "delete", "admin"]
}
```

#### Request: Assign permissions to editor role
```bash
curl -X POST http://localhost:8080/api/roles/role_002/permissions \
  -H "Content-Type: application/json" \
  -d '{"permissions": ["read", "write"]}'
```

#### Response:
```json
{
  "status": "success",
  "role_id": "role_002",
  "permissions": ["read", "write"]
}
```

### 3. Assign Roles to Users

#### Request: Assign admin role to user
```bash
curl -X POST http://localhost:8080/api/users/user123/roles \
  -H "Content-Type: application/json" \
  -d '{"role_ids": ["role_001"]}'
```

#### Response:
```json
{
  "status": "success",
  "user_id": "user123",
  "role_ids": ["role_001"]
}
```

#### Request: Assign multiple roles to user
```bash
curl -X POST http://localhost:8080/api/users/user456/roles \
  -H "Content-Type: application/json" \
  -d '{"role_ids": ["role_001", "role_002"]}'
```

#### Response:
```json
{
  "status": "success",
  "user_id": "user456",
  "role_ids": ["role_001", "role_002"]
}
```

### 4. Check User Permissions

#### Request: Get permissions for user with single role
```bash
curl -X GET http://localhost:8080/api/users/user123/permissions
```

#### Response:
```json
{
  "status": "success",
  "user_id": "user123",
  "permissions": ["read", "write", "delete", "admin"]
}
```

#### Request: Get permissions for user with multiple roles
```bash
curl -X GET http://localhost:8080/api/users/user456/permissions
```

#### Response (combined permissions from both roles):
```json
{
  "status": "success",
  "user_id": "user456",
  "permissions": ["read", "write", "delete", "admin"]
}
```

#### Request: Get permissions for user without roles
```bash
curl -X GET http://localhost:8080/api/users/user789/permissions
```

#### Response:
```json
{
  "status": "success",
  "user_id": "user789",
  "permissions": []
}
```

## Error Examples

### Duplicate Role Name

#### Request:
```bash
curl -X POST http://localhost:8080/api/roles \
  -H "Content-Type: application/json" \
  -d '{"role_name": "admin"}'
```

#### Response (when role already exists):
```json
{
  "status": "error",
  "message": "Role 'admin' already exists"
}
```

### Invalid Role ID

#### Request:
```bash
curl -X POST http://localhost:8080/api/roles/invalid_role_id/permissions \
  -H "Content-Type: application/json" \
  -d '{"permissions": ["read"]}'
```

#### Response:
```json
{
  "status": "error",
  "message": "Role 'invalid_role_id' not found"
}
```

### Missing Required Fields

#### Request:
```bash
curl -X POST http://localhost:8080/api/roles \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Response:
```json
{
  "status": "error",
  "message": "Missing required field: role_name"
}
```

## Testing with Python

```python
import requests

# Create a role
response = requests.post(
    'http://localhost:8080/api/roles',
    json={'role_name': 'developer'}
)
role_data = response.json()
role_id = role_data['role_id']

# Assign permissions
requests.post(
    f'http://localhost:8080/api/roles/{role_id}/permissions',
    json={'permissions': ['read', 'write']}
)

# Assign role to user
requests.post(
    'http://localhost:8080/api/users/dev001/roles',
    json={'role_ids': [role_id]}
)

# Check user permissions
response = requests.get('http://localhost:8080/api/users/dev001/permissions')
print(response.json())
# Output: {'status': 'success', 'user_id': 'dev001', 'permissions': ['read', 'write']}
```

