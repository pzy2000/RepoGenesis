# Task Management Microservice

## Functionality Description

This is a RESTful API-based task management microservice that provides complete task CRUD operations and status management functionality. The service allows users to create, view, update, and delete tasks, while supporting task status tracking and priority management.

## API Definition

### Service Configuration
- **Listening Port**: 8080
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`

### API Interfaces

#### 1. Create Task
- **API Name**: `POST /api/v1/tasks`
- **Function**: Create new task
- **Input Schema**:
```json
{
  "title": "string (required, max 200 chars)",
  "description": "string (optional, max 1000 chars)",
  "priority": "string (required, enum: ['low', 'medium', 'high'])",
  "due_date": "string (optional, ISO 8601 format)"
}
```
- **Output Schema**:
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "priority": "string",
  "status": "string",
  "due_date": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

#### 2. Get Task List
- **API Name**: `GET /api/v1/tasks`
- **Function**: Get all tasks list with pagination and filtering
- **Query Parameters**:
  - `page`: integer (optional, default: 1)
  - `limit`: integer (optional, default: 10, max: 100)
  - `status`: string (optional, enum: ['pending', 'in_progress', 'completed'])
  - `priority`: string (optional, enum: ['low', 'medium', 'high'])
- **Output Schema**:
```json
{
  "tasks": [
    {
      "id": "integer",
      "title": "string",
      "description": "string",
      "priority": "string",
      "status": "string",
      "due_date": "string",
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

#### 3. Get Single Task
- **API Name**: `GET /api/v1/tasks/{task_id}`
- **Function**: Get detailed information of specific task by task ID
- **Path Parameters**:
  - `task_id`: integer (required)
- **Output Schema**:
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "priority": "string",
  "status": "string",
  "due_date": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

#### 4. Update Task
- **API Name**: `PUT /api/v1/tasks/{task_id}`
- **Function**: Update specified task information
- **Path Parameters**:
  - `task_id`: integer (required)
- **Input Schema**:
```json
{
  "title": "string (optional, max 200 chars)",
  "description": "string (optional, max 1000 chars)",
  "priority": "string (optional, enum: ['low', 'medium', 'high'])",
  "status": "string (optional, enum: ['pending', 'in_progress', 'completed'])",
  "due_date": "string (optional, ISO 8601 format)"
}
```
- **Output Schema**:
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "priority": "string",
  "status": "string",
  "due_date": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

#### 5. Delete Task
- **API Name**: `DELETE /api/v1/tasks/{task_id}`
- **Function**: Delete specified task
- **Path Parameters**:
  - `task_id`: integer (required)
- **Output Schema**:
```json
{
  "message": "string"
}
```

#### 6. Health Check
- **API Name**: `GET /api/v1/health`
- **Function**: Check service health status
- **Output Schema**:
```json
{
  "status": "string",
  "timestamp": "string",
  "version": "string"
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
- `404`: Resource not found
- `422`: Data validation failed
- `500`: Internal server error

## Data Model

### Task Entity
- `id`: Primary key, auto-increment integer
- `title`: Task title, required, max 200 characters
- `description`: Task description, optional, max 1000 characters
- `priority`: Priority, enum values ['low', 'medium', 'high']
- `status`: Status, enum values ['pending', 'in_progress', 'completed'], default 'pending'
- `due_date`: Due date, optional, ISO 8601 format
- `created_at`: Creation time, auto-generated
- `updated_at`: Update time, auto-updated

## Technical Specifications

- **Framework**: Supports mainstream web frameworks (Flask, FastAPI, Django, etc.)
- **Database**: Supports relational databases (SQLite, PostgreSQL, MySQL, etc.)
- **Data Validation**: Strict input data validation and type checking
- **Error Handling**: Complete error handling and user-friendly error messages
- **Logging**: Complete operation logging
- **API Documentation**: Auto-generated API documentation (Swagger/OpenAPI)

## Deployment Requirements

- **Port**: Service must listen on port 8080
- **Environment Variables**: Support configuration of database connections and other parameters through environment variables
- **Health Check**: Provide health check endpoint for service monitoring
- **Containerization**: Support Docker containerized deployment
