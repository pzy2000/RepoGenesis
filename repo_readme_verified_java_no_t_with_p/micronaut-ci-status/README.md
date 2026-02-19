# Micronaut CI Status Benchmark

## Project Description
This project is a benchmark for a Continuous Integration (CI) Build Status Query service built using the Micronaut framework. It simulates a system where users can manage projects, trigger builds, view build status, and manage build agents.

## Functional Requirements
The service must expose a RESTful API on port **8080** to handle the following operations:
- **Project Management**: Create, read, update, and delete projects.
- **Build Management**: Trigger builds, cancel builds, view build details, and logs.
- **Agent Management**: Register build agents and update their status.
- **User Management**: Manage users of the CI system.
- **System Monitoring**: View system health, version, and statistics.

## Metrics
- **Test Case Pass Rate**: The percentage of API tests that pass against the running service.
- **Repo Pass Rate**: The overall success rate of the benchmark implementation.

## API Definitions
The service listens on `http://localhost:8080`. All request and response bodies are in JSON format.

### 1. List All Projects
- **Method**: `GET`
- **Path**: `/projects`
- **Output**: `[{"id": "string", "name": "string", "repoUrl": "string"}]`

### 2. Create Project
- **Method**: `POST`
- **Path**: `/projects`
- **Input**: `{"name": "string", "repoUrl": "string"}`
- **Output**: `{"id": "string", "name": "string", "repoUrl": "string"}` (201 Created)

### 3. Get Project Details
- **Method**: `GET`
- **Path**: `/projects/{id}`
- **Output**: `{"id": "string", "name": "string", "repoUrl": "string", "createdAt": "string"}`

### 4. Update Project
- **Method**: `PUT`
- **Path**: `/projects/{id}`
- **Input**: `{"name": "string", "repoUrl": "string"}`
- **Output**: `{"id": "string", "name": "string", "repoUrl": "string"}`

### 5. Delete Project
- **Method**: `DELETE`
- **Path**: `/projects/{id}`
- **Output**: 204 No Content

### 6. Trigger Build
- **Method**: `POST`
- **Path**: `/projects/{id}/builds`
- **Input**: `{"branch": "string", "commitHash": "string"}`
- **Output**: `{"id": "string", "projectId": "string", "status": "QUEUED"}` (201 Created)

### 7. List Builds for Project
- **Method**: `GET`
- **Path**: `/projects/{id}/builds`
- **Output**: `[{"id": "string", "status": "string", "startTime": "string"}]`

### 8. Get Build Details
- **Method**: `GET`
- **Path**: `/builds/{id}`
- **Output**: `{"id": "string", "projectId": "string", "status": "string", "result": "string", "startTime": "string", "endTime": "string"}`

### 9. Get Build Status
- **Method**: `GET`
- **Path**: `/builds/{id}/status`
- **Output**: `{"status": "string"}` (e.g., RUNNING, SUCCESS, FAILURE)

### 10. Cancel Build
- **Method**: `POST`
- **Path**: `/builds/{id}/cancel`
- **Output**: `{"id": "string", "status": "CANCELLED"}`

### 11. Get Build Logs
- **Method**: `GET`
- **Path**: `/builds/{id}/logs`
- **Output**: `{"logs": ["line1", "line2"]}`

### 12. List Build Artifacts
- **Method**: `GET`
- **Path**: `/builds/{id}/artifacts`
- **Output**: `[{"name": "string", "url": "string", "size": 1234}]`

### 13. List Build Agents
- **Method**: `GET`
- **Path**: `/agents`
- **Output**: `[{"id": "string", "name": "string", "status": "string"}]`

### 14. Register Agent
- **Method**: `POST`
- **Path**: `/agents`
- **Input**: `{"name": "string", "capabilities": ["java", "docker"]}`
- **Output**: `{"id": "string", "token": "string"}` (201 Created)

### 15. Get Agent Details
- **Method**: `GET`
- **Path**: `/agents/{id}`
- **Output**: `{"id": "string", "name": "string", "status": "string", "lastHeartbeat": "string"}`

### 16. Update Agent Status
- **Method**: `PUT`
- **Path**: `/agents/{id}/status`
- **Input**: `{"status": "IDLE"}` (or BUSY, OFFLINE)
- **Output**: `{"id": "string", "status": "IDLE"}`

### 17. Get Build Queue
- **Method**: `GET`
- **Path**: `/queue`
- **Output**: `[{"buildId": "string", "priority": 1}]`

### 18. List Users
- **Method**: `GET`
- **Path**: `/users`
- **Output**: `[{"id": "string", "username": "string", "role": "string"}]`

### 19. Create User
- **Method**: `POST`
- **Path**: `/users`
- **Input**: `{"username": "string", "email": "string", "role": "USER"}`
- **Output**: `{"id": "string", "username": "string"}` (201 Created)

### 20. Get User Details
- **Method**: `GET`
- **Path**: `/users/{id}`
- **Output**: `{"id": "string", "username": "string", "email": "string", "role": "string"}`

### 21. Get Daily Statistics
- **Method**: `GET`
- **Path**: `/statistics/daily`
- **Output**: `{"date": "string", "totalBuilds": 100, "successRate": 0.95}`

### 22. System Health Check
- **Method**: `GET`
- **Path**: `/system/health`
- **Output**: `{"status": "UP", "db": "UP", "queue": "UP"}`

### 23. System Version
- **Method**: `GET`
- **Path**: `/system/version`
- **Output**: `{"version": "1.0.0", "buildDate": "string"}`

### 24. Git Webhook Receiver
- **Method**: `POST`
- **Path**: `/webhooks/git`
- **Input**: `{"ref": "refs/heads/main", "repository": {"url": "string"}}`
- **Output**: `{"received": true}`

### 25. Get Latest Report
- **Method**: `GET`
- **Path**: `/reports/latest`
- **Output**: `{"reportId": "string", "summary": "string"}`
