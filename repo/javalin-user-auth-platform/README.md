# Javalin User Authentication Platform

A lightweight user registration and login management platform built with the Javalin framework.

## Project Overview

This project provides a simple yet complete user authentication system with registration, login, profile management, and session handling capabilities. It demonstrates RESTful API design patterns using Javalin, a lightweight Java web framework.

## Features

- User registration with validation
- User login with session management
- User profile retrieval and updates
- Password change functionality
- User logout
- Session validation
- User deletion (admin)

## API Specifications

### Server Configuration

- **Port**: `7070`
- **Base URL**: `http://localhost:7070`
- **Content-Type**: `application/json`

### API Endpoints

#### 1. User Registration

**Endpoint**: `POST /api/users/register`

**Description**: Register a new user account

**Input Schema**:
```json
{
  "username": "string (required, 3-20 characters, alphanumeric)",
  "email": "string (required, valid email format)",
  "password": "string (required, minimum 6 characters)"
}
```

**Output Schema** (Success - 201):
```json
{
  "success": true,
  "message": "User registered successfully",
  "userId": "string (UUID)"
}
```

**Output Schema** (Error - 400):
```json
{
  "success": false,
  "message": "string (error description)"
}
```

---

#### 2. User Login

**Endpoint**: `POST /api/users/login`

**Description**: Authenticate user and create session

**Input Schema**:
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Output Schema** (Success - 200):
```json
{
  "success": true,
  "message": "Login successful",
  "sessionToken": "string (JWT or session ID)",
  "userId": "string (UUID)"
}
```

**Output Schema** (Error - 401):
```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

---

#### 3. Get User Profile

**Endpoint**: `GET /api/users/profile`

**Description**: Retrieve authenticated user's profile information

**Headers**:
```
Authorization: Bearer {sessionToken}
```

**Output Schema** (Success - 200):
```json
{
  "success": true,
  "user": {
    "userId": "string (UUID)",
    "username": "string",
    "email": "string",
    "createdAt": "string (ISO 8601 datetime)"
  }
}
```

**Output Schema** (Error - 401):
```json
{
  "success": false,
  "message": "Unauthorized"
}
```

---

#### 4. Update User Profile

**Endpoint**: `PUT /api/users/profile`

**Description**: Update user profile information

**Headers**:
```
Authorization: Bearer {sessionToken}
```

**Input Schema**:
```json
{
  "email": "string (optional, valid email format)"
}
```

**Output Schema** (Success - 200):
```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

**Output Schema** (Error - 400/401):
```json
{
  "success": false,
  "message": "string (error description)"
}
```

---

#### 5. Change Password

**Endpoint**: `POST /api/users/change-password`

**Description**: Change user password

**Headers**:
```
Authorization: Bearer {sessionToken}
```

**Input Schema**:
```json
{
  "currentPassword": "string (required)",
  "newPassword": "string (required, minimum 6 characters)"
}
```

**Output Schema** (Success - 200):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Output Schema** (Error - 400/401):
```json
{
  "success": false,
  "message": "string (error description)"
}
```

---

#### 6. User Logout

**Endpoint**: `POST /api/users/logout`

**Description**: Invalidate user session

**Headers**:
```
Authorization: Bearer {sessionToken}
```

**Output Schema** (Success - 200):
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

#### 7. Validate Session

**Endpoint**: `GET /api/users/validate-session`

**Description**: Check if current session is valid

**Headers**:
```
Authorization: Bearer {sessionToken}
```

**Output Schema** (Success - 200):
```json
{
  "success": true,
  "valid": true,
  "userId": "string (UUID)"
}
```

**Output Schema** (Error - 401):
```json
{
  "success": false,
  "valid": false,
  "message": "Invalid or expired session"
}
```

---

#### 8. Delete User

**Endpoint**: `DELETE /api/users/{userId}`

**Description**: Delete a user account (requires authentication)

**Headers**:
```
Authorization: Bearer {sessionToken}
```

**Path Parameters**:
- `userId`: string (UUID)

**Output Schema** (Success - 200):
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

**Output Schema** (Error - 401/404):
```json
{
  "success": false,
  "message": "string (error description)"
}
```

---

## Metrics

### Test Case Pass Rate
- **Definition**: Percentage of individual test cases that pass successfully
- **Formula**: `(Passed Tests / Total Tests) × 100%`
- **Target**: ≥ 95%

### Repository Pass Rate
- **Definition**: Whether all critical test suites pass (binary: pass/fail)
- **Criteria**: All 8 API endpoints must have at least 80% of their test cases passing
- **Target**: PASS

## Test Coverage

The test suite covers:
- ✅ User registration with valid and invalid inputs
- ✅ User login authentication
- ✅ Session management and validation
- ✅ Profile retrieval and updates
- ✅ Password change functionality
- ✅ User logout
- ✅ User deletion
- ✅ Error handling and edge cases

## Technology Stack

- **Framework**: Javalin 5.x
- **Language**: Java 11+
- **Testing**: JUnit 5, REST Assured
- **Build Tool**: Maven or Gradle
- **JSON Processing**: Jackson

## Running Tests

```bash
# Using Maven
mvn test

# Using Gradle
gradle test
```

## Notes

- All API endpoints return JSON responses
- Authentication uses session tokens passed via Authorization header
- Passwords should be hashed before storage (implementation detail)
- Session tokens should have expiration times (implementation detail)
- Input validation is performed on all endpoints
