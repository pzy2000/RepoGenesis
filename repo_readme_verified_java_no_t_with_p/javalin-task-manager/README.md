# Javalin Task Manager Benchmark

## Project Description
This is a lightweight project task management system based on the Javalin framework. It allows users to manage projects, tasks, and comments.

## Functional Requirements
- **User Management**: Register and login users.
- **Project Management**: Create, read, update, and delete projects.
- **Task Management**: Create, read, update, and delete tasks within projects.
- **Comment Management**: Add and view comments on tasks.

## Metrics
- **Test Case Pass Rate**: The percentage of passed test cases in the `tests/` directory.
- **Repo Pass Rate**: The percentage of passed test cases across the entire repository.

## API Definitions
The server should listen on port `7000`.

### 1. Register User
- **Interface**: `POST /users`
- **Input Schema**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "username": "string",
    "email": "string"
  }
  ```

### 2. Login User
- **Interface**: `POST /users/login`
- **Input Schema**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "token": "string"
  }
  ```

### 3. List Projects
- **Interface**: `GET /projects`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "ownerId": "integer"
    }
  ]
  ```

### 4. Create Project
- **Interface**: `POST /projects`
- **Input Schema**: (Headers: `Authorization: Bearer <token>`)
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "ownerId": "integer"
  }
  ```

### 5. Get Project Details
- **Interface**: `GET /projects/{id}`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "ownerId": "integer"
  }
  ```

### 6. Update Project
- **Interface**: `PUT /projects/{id}`
- **Input Schema**: (Headers: `Authorization: Bearer <token>`)
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "ownerId": "integer"
  }
  ```

### 7. Delete Project
- **Interface**: `DELETE /projects/{id}`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**: `204 No Content`

### 8. Get Tasks for Project
- **Interface**: `GET /projects/{id}/tasks`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**:
  ```json
  [
    {
      "id": "integer",
      "title": "string",
      "description": "string",
      "status": "string",
      "projectId": "integer",
      "assigneeId": "integer"
    }
  ]
  ```

### 9. Create Task in Project
- **Interface**: `POST /projects/{id}/tasks`
- **Input Schema**: (Headers: `Authorization: Bearer <token>`)
  ```json
  {
    "title": "string",
    "description": "string",
    "assigneeId": "integer"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "description": "string",
    "status": "string",
    "projectId": "integer",
    "assigneeId": "integer"
  }
  ```

### 10. Get Task Details
- **Interface**: `GET /tasks/{id}`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "description": "string",
    "status": "string",
    "projectId": "integer",
    "assigneeId": "integer"
  }
  ```

### 11. Update Task
- **Interface**: `PUT /tasks/{id}`
- **Input Schema**: (Headers: `Authorization: Bearer <token>`)
  ```json
  {
    "title": "string",
    "description": "string",
    "status": "string",
    "assigneeId": "integer"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "description": "string",
    "status": "string",
    "projectId": "integer",
    "assigneeId": "integer"
  }
  ```

### 12. Delete Task
- **Interface**: `DELETE /tasks/{id}`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**: `204 No Content`

### 13. Add Comment to Task
- **Interface**: `POST /tasks/{id}/comments`
- **Input Schema**: (Headers: `Authorization: Bearer <token>`)
  ```json
  {
    "content": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "integer",
    "content": "string",
    "taskId": "integer",
    "authorId": "integer",
    "createdAt": "string"
  }
  ```

### 14. Get Comments for Task
- **Interface**: `GET /tasks/{id}/comments`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**:
  ```json
  [
    {
      "id": "integer",
      "content": "string",
      "taskId": "integer",
      "authorId": "integer",
      "createdAt": "string"
    }
  ]
  ```

### 15. Get Tasks Assigned to User
- **Interface**: `GET /users/{id}/tasks`
- **Input Schema**: None (Headers: `Authorization: Bearer <token>`)
- **Output Schema**:
  ```json
  [
    {
      "id": "integer",
      "title": "string",
      "description": "string",
      "status": "string",
      "projectId": "integer",
      "assigneeId": "integer"
    }
  ]
  ```
