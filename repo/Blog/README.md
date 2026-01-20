# Blog CMS API

## Functionality Description

This is a backend API service for a blog content management system (CMS) that provides complete blog post management functionality. The system supports user authentication, article CRUD operations, category management, tag management, and comment functionality.

## API Definition

### Service Configuration
- **Listening Port**: 8000
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`

### 1. User Authentication APIs

#### 1.1 User Registration
- **API Name**: `POST /api/v1/auth/register`
- **Function**: Register new user
- **Input Schema**:
```json
{
  "username": "string (required, 3-20 characters)",
  "email": "string (required, valid email format)",
  "password": "string (required, 6-50 characters)"
}
```
- **Output Schema**:
```json
{
  "message": "string",
  "user_id": "integer",
  "username": "string"
}
```

#### 1.2 User Login
- **API Name**: `POST /api/v1/auth/login`
- **Function**: User login to get access token
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
  "user_id": "integer",
  "username": "string"
}
```

### 2. Article Management APIs

#### 2.1 Create Article
- **API Name**: `POST /api/v1/posts`
- **Function**: Create new blog post
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "title": "string (required, 1-200 characters)",
  "content": "string (required, 1-10000 characters)",
  "excerpt": "string (optional, 1-500 characters)",
  "category_id": "integer (required)",
  "tags": "array of strings (optional)",
  "status": "string (optional, draft|published, default draft)"
}
```
- **Output Schema**:
```json
{
  "id": "integer",
  "title": "string",
  "content": "string",
  "excerpt": "string",
  "author_id": "integer",
  "category_id": "integer",
  "tags": "array of strings",
  "status": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

#### 2.2 Get Article List
- **API Name**: `GET /api/v1/posts`
- **Function**: Get article list with pagination and filtering
- **Authentication**: Optional
- **Query Parameters**:
  - `page`: integer (default 1)
  - `limit`: integer (default 10, max 100)
  - `status`: string (draft|published)
  - `category_id`: integer
  - `author_id`: integer
  - `search`: string (search in title and content)
- **Output Schema**:
```json
{
  "posts": [
    {
      "id": "integer",
      "title": "string",
      "excerpt": "string",
      "author": {
        "id": "integer",
        "username": "string"
      },
      "category": {
        "id": "integer",
        "name": "string"
      },
      "tags": "array of strings",
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

#### 2.3 Get Single Article
- **API Name**: `GET /api/v1/posts/{post_id}`
- **Function**: Get detailed information of specified article
- **Authentication**: Optional
- **Output Schema**:
```json
{
  "id": "integer",
  "title": "string",
  "content": "string",
  "excerpt": "string",
  "author": {
    "id": "integer",
    "username": "string"
  },
  "category": {
    "id": "integer",
    "name": "string"
  },
  "tags": "array of strings",
  "status": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

#### 2.4 Update Article
- **API Name**: `PUT /api/v1/posts/{post_id}`
- **Function**: Update specified article
- **Authentication**: Bearer Token required, can only update own articles
- **Input Schema**: Same as create article
- **Output Schema**: Same as create article

#### 2.5 Delete Article
- **API Name**: `DELETE /api/v1/posts/{post_id}`
- **Function**: Delete specified article
- **Authentication**: Bearer Token required, can only delete own articles
- **Output Schema**:
```json
{
  "message": "string"
}
```

### 3. Category Management APIs

#### 3.1 Create Category
- **API Name**: `POST /api/v1/categories`
- **Function**: Create new category
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "name": "string (required, 1-50 characters)",
  "description": "string (optional, 1-200 characters)"
}
```
- **Output Schema**:
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "created_at": "string"
}
```

#### 3.2 Get Category List
- **API Name**: `GET /api/v1/categories`
- **Function**: Get all categories list
- **Authentication**: Optional
- **Output Schema**:
```json
{
  "categories": [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "post_count": "integer",
      "created_at": "string"
    }
  ]
}
```

### 4. Comment Management APIs

#### 4.1 Create Comment
- **API Name**: `POST /api/v1/posts/{post_id}/comments`
- **Function**: Create comment for specified article
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "content": "string (required, 1-1000 characters)",
  "parent_id": "integer (optional, ID of comment being replied to)"
}
```
- **Output Schema**:
```json
{
  "id": "integer",
  "content": "string",
  "author": {
    "id": "integer",
    "username": "string"
  },
  "post_id": "integer",
  "parent_id": "integer",
  "created_at": "string"
}
```

#### 4.2 Get Article Comments
- **API Name**: `GET /api/v1/posts/{post_id}/comments`
- **Function**: Get all comments for specified article
- **Authentication**: Optional
- **Output Schema**:
```json
{
  "comments": [
    {
      "id": "integer",
      "content": "string",
      "author": {
        "id": "integer",
        "username": "string"
      },
      "parent_id": "integer",
      "replies": "array of comment objects",
      "created_at": "string"
    }
  ]
}
```

## Error Response Format

All APIs return unified format when errors occur:
```json
{
  "error": "string",
  "message": "string",
  "details": "object (optional)"
}
```

Common HTTP Status Codes:
- 200: Success
- 201: Created successfully
- 400: Request parameter error
- 401: Unauthenticated
- 403: Insufficient permissions
- 404: Resource not found
- 422: Data validation failed
- 500: Internal server error
