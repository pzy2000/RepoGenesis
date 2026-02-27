# Personalization API

## Description

This is a personalization microservice API that provides user personalization management, including favorites, likes, and history tracking features. The service supports recording and managing user's personalized actions on content, helping to build a personalized user experience.

## API Definition

### Service Configuration
- **Listening Port**: 8082
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`

### 1. Favorites Management APIs

#### 1.1 Add Favorite
- **API Name**: `POST /api/v1/favorites`
- **Function**: User adds content to favorites
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "content_id": "string (Required, unique content identifier)",
  "content_type": "string (Required, content type: post|article|product|video)",
  "category": "string (Optional, favorite category label)"
}
```
- **Output Schema**:
```json
{
  "id": "string",
  "user_id": "string",
  "content_id": "string",
  "content_type": "string",
  "category": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

#### 1.2 Get Favorites List
- **API Name**: `GET /api/v1/favorites`
- **Function**: Retrieve user's favorites list, supports pagination and filtering
- **Authentication**: Bearer Token required
- **Query Parameters**:
  - `page`: integer (default 1)
  - `limit`: integer (default 10, max 100)
  - `content_type`: string (filter by content type)
  - `category`: string (filter by category label)
- **Output Schema**:
```json
{
  "favorites": [
    {
      "id": "string",
      "content_id": "string",
      "content_type": "string",
      "category": "string",
      "created_at": "string",
      "content_info": {
        "title": "string",
        "summary": "string",
        "thumbnail": "string"
      }
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

#### 1.3 Delete Favorite
- **API Name**: `DELETE /api/v1/favorites/{favorite_id}`
- **Function**: Delete a specific favorite record
- **Authentication**: Bearer Token required
- **Output Schema**:
```json
{
  "message": "string"
}
```

### 2. Likes Management APIs

#### 2.1 Add Like
- **API Name**: `POST /api/v1/likes`
- **Function**: User performs a like/unlike action on content
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "content_id": "string (Required, unique content identifier)",
  "content_type": "string (Required, content type: post|article|product|video)",
  "action": "string (Required, like|unlike)"
}
```
- **Output Schema**:
```json
{
  "id": "string",
  "user_id": "string",
  "content_id": "string",
  "content_type": "string",
  "action": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

#### 2.2 Get Like Stats
- **API Name**: `GET /api/v1/likes/stats/{content_id}`
- **Function**: Retrieve like statistics for specific content
- **Authentication**: Optional
- **Output Schema**:
```json
{
  "content_id": "string",
  "content_type": "string",
  "total_likes": "integer",
  "total_unlikes": "integer",
  "user_action": "string (current user's like status: like|unlike|null)"
}
```

#### 2.3 Get User Like History
- **API Name**: `GET /api/v1/likes/history`
- **Function**: Retrieve user's like action history
- **Authentication**: Bearer Token required
- **Query Parameters**:
  - `page`: integer (default 1)
  - `limit`: integer (default 10, max 50)
  - `content_type`: string (filter by content type)
- **Output Schema**:
```json
{
  "likes": [
    {
      "id": "string",
      "content_id": "string",
      "content_type": "string",
      "action": "string",
      "created_at": "string"
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

### 3. History APIs

#### 3.1 Record User Action
- **API Name**: `POST /api/v1/history`
- **Function**: Record a user's action history
- **Authentication**: Bearer Token required
- **Input Schema**:
```json
{
  "action": "string (Required, action type: view|search|share|download)",
  "content_id": "string (Optional, related content ID)",
  "content_type": "string (Optional, content type)",
  "metadata": "object (Optional, additional information)",
  "session_id": "string (Optional, session identifier)"
}
```
- **Output Schema**:
```json
{
  "id": "string",
  "user_id": "string",
  "action": "string",
  "content_id": "string",
  "content_type": "string",
  "metadata": "object",
  "session_id": "string",
  "created_at": "string (ISO 8601)",
  "ip_address": "string",
  "user_agent": "string"
}
```

#### 3.2 Get History Records
- **API Name**: `GET /api/v1/history`
- **Function**: Retrieve user's history records with various filters
- **Authentication**: Bearer Token required
- **Query Parameters**:
  - `page`: integer (default 1)
  - `limit`: integer (default 20, max 100)
  - `action`: string (filter by action type)
  - `content_type`: string (filter by content type)
  - `start_date`: string (start date, ISO 8601)
  - `end_date`: string (end date, ISO 8601)
  - `session_id`: string (filter by session)
- **Output Schema**:
```json
{
  "history": [
    {
      "id": "string",
      "action": "string",
      "content_id": "string",
      "content_type": "string",
      "metadata": "object",
      "created_at": "string",
      "content_info": {
        "title": "string",
        "summary": "string"
      }
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

#### 3.3 Delete History Record
- **API Name**: `DELETE /api/v1/history/{history_id}`
- **Function**: Delete a specific history record
- **Authentication**: Bearer Token required
- **Output Schema**:
```json
{
  "message": "string"
}
```

#### 3.4 Clear History Records
- **API Name**: `DELETE /api/v1/history`
- **Function**: Clear all history records for the user
- **Authentication**: Bearer Token required
- **Output Schema**:
```json
{
  "message": "string",
  "deleted_count": "integer"
}
```

## Error Response Format

All APIs return a unified format when an error occurs:
```json
{
  "error": "string",
  "message": "string",
  "details": "object (optional)"
}
```

Common HTTP status codes:
- 200: OK
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Unprocessable Entity (Validation Failed)
- 429: Too Many Requests
- 500: Internal Server Error


## Test Cases

Test cases are located under the `tests/` directory and include:

1. **Favorites Tests** (`test_favorites_api.py`)
   - CRUD operations for favorites
   - Category management
   - Data validation and error handling

2. **Likes Tests** (`test_likes_api.py`)
   - Like/Unlike operations
   - Like statistics retrieval
   - User like history

3. **History Tests** (`test_history_api.py`)
   - Action history recording
   - History retrieval and filtering
   - History cleanup functionality

## Project Structure

```
├── app/                          # Main application code
│   ├── api/                      # API route definitions
│   ├── core/                     # Core configurations and dependencies
│   ├── models/                   # Data models
│   ├── services/                 # Business logic services
│   ├── utils/                    # Utility functions
│   └── main.py                   # Application entry point
├── tests/                        # Test files
│   ├── test_favorites_api.py     # Favorites API tests
│   ├── test_likes_api.py        # Likes API tests
│   └── test_history_api.py       # History API tests
├── requirements.txt              # Project dependencies
├── start.sh                      # Startup script
├── Dockerfile                    # Docker build file
├── test_startup.py               # Startup test script
└── README_PROJECT.md             # Detailed project documentation
```

## Quick Start

### Using the Startup Script (Recommended)

```bash
# Add execution permission to the script
chmod +x start.sh

# Start the service
./start.sh
```

The startup script will:
1. Check Python environment
2. Create virtual environment (if needed)
3. Install dependencies
4. Check port availability
5. Start the service

### Manual Startup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

### Docker Deployment

```bash
# Build the image
docker build -t customization-api .

# Run the container
docker run -d -p 8082:8082 --name customization-api customization-api
```

## API Documentation

Once the service is started, you can access:

- **Interactive API Docs**: http://localhost:8082/docs
- **API Schema Definition**: http://localhost:8082/openapi.json
- **Health Check**: http://localhost:8082/health

## Development Guide

Refer to `README_PROJECT.md` for detailed development guides, including:
- Project structure details
- API usage examples
- Deployment guide
- Troubleshooting
- Contribution guide
