# Simple RBAC Service

A lightweight Role-Based Access Control (RBAC) service for managing users, roles, and permissions.

## Project Overview

This service provides a simple API for implementing role-based access control. It allows creating roles, assigning permissions to roles, assigning roles to users, and checking user permissions.

## Functional Requirements

### Core Features

1. **Role Management**: Create and manage roles in the system
2. **Permission Assignment**: Assign permissions to roles
3. **User Role Assignment**: Assign roles to users
4. **Permission Check**: Verify if a user has specific permissions

### Data Model

- **Role**: A named role (e.g., "admin", "editor", "viewer")
- **Permission**: A named permission (e.g., "read", "write", "delete")
- **User**: A user identified by user_id with assigned roles

## API Specification

The service runs on **port 8080** and provides the following REST APIs:

### 1. Create Role

**Endpoint**: `POST /api/roles`

**Description**: Create a new role in the system.

**Input Schema**:
```json
{
  "role_name": "string (required, unique)"
}
```

**Output Schema**:
```json
{
  "status": "success",
  "role_id": "string",
  "role_name": "string"
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "string"
}
```

### 2. Assign Permission to Role

**Endpoint**: `POST /api/roles/{role_id}/permissions`

**Description**: Assign one or more permissions to a role.

**Input Schema**:
```json
{
  "permissions": ["string (required, array of permission names)"]
}
```

**Output Schema**:
```json
{
  "status": "success",
  "role_id": "string",
  "permissions": ["string"]
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "string"
}
```

### 3. Assign Role to User

**Endpoint**: `POST /api/users/{user_id}/roles`

**Description**: Assign one or more roles to a user.

**Input Schema**:
```json
{
  "role_ids": ["string (required, array of role IDs)"]
}
```

**Output Schema**:
```json
{
  "status": "success",
  "user_id": "string",
  "role_ids": ["string"]
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "string"
}
```

### 4. Check User Permissions

**Endpoint**: `GET /api/users/{user_id}/permissions`

**Description**: Get all permissions for a user based on their assigned roles.

**Input Schema**: None (user_id in URL path)

**Output Schema**:
```json
{
  "status": "success",
  "user_id": "string",
  "permissions": ["string"]
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "string"
}
```

## Implementation Notes

- The service should persist data in memory (no database required for this benchmark)
- All responses should use JSON format
- HTTP status codes should follow REST conventions:
  - 200 OK for successful operations
  - 400 Bad Request for invalid input
  - 404 Not Found for non-existent resources
  - 500 Internal Server Error for server errors
- Role IDs and User IDs should be handled as strings
- Permission names are case-sensitive
- A user can have multiple roles
- A role can have multiple permissions
- Permissions from multiple roles are combined (union)

