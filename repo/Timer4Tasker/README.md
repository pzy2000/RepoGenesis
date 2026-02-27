# Timer4Tasker - Scheduled Task Management System

## Project Overview

Timer4Tasker is a lightweight scheduled task management system providing RESTful API interfaces for creating, managing, and executing scheduled tasks. The system supports various types of scheduled tasks, including file cleanup, data summary, and data backup.

## Feature Description

### Core Features

1. **Scheduled Task Management**
   - Create scheduled tasks
   - Query task list
   - Query task details
   - Update task configuration
   - Delete tasks
   - Start/Stop tasks

2. **Task Types**
   - File Cleanup Task: Regularly clean up expired files in specified directories
   - Data Summary Task: Regularly perform statistical analysis and summary of data
   - Data Backup Task: Regularly back up specified data

3. **Task Execution Logs**
   - Query task execution history
   - Query task execution status
   - Retrieve task execution results

## API Interface Definition

### Service Configuration

- **Listening Port**: 8080
- **Base URL**: `http://localhost:8080/api/v1`
- **Content-Type**: `application/json`

### Interface List

#### 1. Create Scheduled Task

**Endpoint**: `POST /tasks`

**Input Schema**:
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "task_type": "string (required, enum: ['file_cleanup', 'data_summary', 'data_backup'])",
  "schedule": "string (required, cron expression)",
  "config": {
    "path": "string (optional, for file_cleanup)",
    "pattern": "string (optional, for file_cleanup)",
    "days": "integer (optional, for file_cleanup)",
    "source": "string (optional, for data_summary/data_backup)",
    "target": "string (optional, for data_backup)"
  },
  "enabled": "boolean (optional, default: true)"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "name": "string",
    "task_type": "string",
    "schedule": "string",
    "enabled": "boolean",
    "created_at": "string (ISO 8601 format)"
  },
  "message": "string (optional)"
}
```

#### 2. Get Task List

**Endpoint**: `GET /tasks`

**Query Parameters**:
- `task_type`: string (optional, filter by task type)
- `enabled`: boolean (optional, filter by enabled status)
- `page`: integer (optional, default: 1)
- `page_size`: integer (optional, default: 10)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "tasks": [
      {
        "task_id": "string",
        "name": "string",
        "task_type": "string",
        "schedule": "string",
        "enabled": "boolean",
        "created_at": "string",
        "last_run": "string (optional)"
      }
    ],
    "total": "integer",
    "page": "integer",
    "page_size": "integer"
  },
  "message": "string (optional)"
}
```

#### 3. Get Task Details

**Endpoint**: `GET /tasks/{task_id}`

**Path Parameters**:
- `task_id`: string (required)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "name": "string",
    "description": "string",
    "task_type": "string",
    "schedule": "string",
    "config": "object",
    "enabled": "boolean",
    "created_at": "string",
    "updated_at": "string",
    "last_run": "string (optional)",
    "next_run": "string (optional)"
  },
  "message": "string (optional)"
}
```

#### 4. Update Task

**Endpoint**: `PUT /tasks/{task_id}`

**Path Parameters**:
- `task_id`: string (required)

**Input Schema**:
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "schedule": "string (optional)",
  "config": "object (optional)",
  "enabled": "boolean (optional)"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "name": "string",
    "task_type": "string",
    "schedule": "string",
    "enabled": "boolean",
    "updated_at": "string"
  },
  "message": "string (optional)"
}
```

#### 5. Delete Task

**Endpoint**: `DELETE /tasks/{task_id}`

**Path Parameters**:
- `task_id`: string (required)

**Output Schema**:
```json
{
  "success": "boolean",
  "message": "string"
}
```

#### 6. Toggle Task (Start/Stop)

**Endpoint**: `POST /tasks/{task_id}/toggle`

**Path Parameters**:
- `task_id`: string (required)

**Input Schema**:
```json
{
  "enabled": "boolean (required)"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "enabled": "boolean"
  },
  "message": "string (optional)"
}
```

#### 7. Execute Task Manually

**Endpoint**: `POST /tasks/{task_id}/execute`

**Path Parameters**:
- `task_id`: string (required)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "execution_id": "string",
    "task_id": "string",
    "status": "string (enum: ['running', 'completed', 'failed'])",
    "started_at": "string"
  },
  "message": "string (optional)"
}
```

#### 8. Get Task Execution History

**Endpoint**: `GET /tasks/{task_id}/executions`

**Path Parameters**:
- `task_id`: string (required)

**Query Parameters**:
- `limit`: integer (optional, default: 20)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "executions": [
      {
        "execution_id": "string",
        "task_id": "string",
        "status": "string",
        "started_at": "string",
        "completed_at": "string (optional)",
        "result": "object (optional)",
        "error": "string (optional)"
      }
    ]
  },
  "message": "string (optional)"
}
```

#### 9. Get System Statistics

**Endpoint**: `GET /stats`

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "total_tasks": "integer",
    "active_tasks": "integer",
    "total_executions": "integer",
    "successful_executions": "integer",
    "failed_executions": "integer"
  },
  "message": "string (optional)"
}
```

## Error Codes Description

| HTTP Status Code | Description |
|-----------------|------|
| 200 | Request Successful |
| 201 | Created Successfully |
| 400 | Request Parameter Error |
| 404 | Resource Not Found |
| 500 | Internal Server Error |

## Technical Requirements

1. Developed using Python 3.8+
2. Built web services using FastAPI or Flask framework
3. Implement scheduled task scheduling using APScheduler or Celery
4. Use SQLite or other databases for data persistence
5. Provide complete unit tests and integration tests

## Deployment Instructions

```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
python app.py

# The service will start at http://localhost:8080
```

## Testing Instructions

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_task_management.py

# Check test coverage
pytest --cov=. tests/
```
