# Instant Chat Message Gateway Service

## Functional Description
This project implements an Instant Chat Message Gateway Service based on the Spring Boot framework. It provides a set of RESTful APIs to handle real-time messaging, user presence management, and group chat functionalities. The service is designed to be a lightweight gateway that routes messages and manages user sessions.

Key features include:
- **User Management**: Registration, login, and status updates (online/offline/away).
- **Private Messaging**: Sending and retrieving private messages between users.
- **Group Messaging**: Creating groups, joining/leaving groups, and sending messages to groups.
- **System Monitoring**: Basic health check endpoint.

## API Definitions

The service listens on a configurable port (default: 8080).

### 1. Register User
- **Endpoint**: `POST /api/users/register`
- **Description**: Registers a new user.
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
    "userId": "string",
    "username": "string",
    "createdAt": "long"
  }
  ```

### 2. User Login
- **Endpoint**: `POST /api/users/login`
- **Description**: Authenticates a user and returns a session token.
- **Input Schema**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "token": "string",
    "userId": "string",
    "expiresIn": "long"
  }
  ```

### 3. Get User Status
- **Endpoint**: `GET /api/users/{userId}/status`
- **Description**: Retrieves the current status of a user.
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "userId": "string",
    "status": "string", // "ONLINE", "OFFLINE", "AWAY"
    "lastActive": "long"
  }
  ```

### 4. Update User Status
- **Endpoint**: `PUT /api/users/{userId}/status`
- **Description**: Updates the current status of a user.
- **Input Schema**:
  ```json
  {
    "status": "string" // "ONLINE", "OFFLINE", "AWAY"
  }
  ```
- **Output Schema**:
  ```json
  {
    "userId": "string",
    "status": "string",
    "updatedAt": "long"
  }
  ```

### 5. Send Private Message
- **Endpoint**: `POST /api/messages/send`
- **Description**: Sends a private message to another user.
- **Input Schema**:
  ```json
  {
    "senderId": "string",
    "recipientId": "string",
    "content": "string",
    "type": "string" // "TEXT", "IMAGE", "FILE"
  }
  ```
- **Output Schema**:
  ```json
  {
    "messageId": "string",
    "timestamp": "long",
    "status": "string" // "SENT", "DELIVERED"
  }
  ```

### 6. Get Message History
- **Endpoint**: `GET /api/messages/history`
- **Description**: Retrieves message history between two users.
- **Input Schema**: Query Params: `userId1`, `userId2`, `limit` (optional), `before` (optional timestamp)
- **Output Schema**:
  ```json
  {
    "messages": [
      {
        "messageId": "string",
        "senderId": "string",
        "recipientId": "string",
        "content": "string",
        "timestamp": "long"
      }
    ]
  }
  ```

### 7. Create Group
- **Endpoint**: `POST /api/groups/create`
- **Description**: Creates a new chat group.
- **Input Schema**:
  ```json
  {
    "creatorId": "string",
    "name": "string",
    "description": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "groupId": "string",
    "name": "string",
    "createdAt": "long"
  }
  ```

### 8. Join Group
- **Endpoint**: `POST /api/groups/{groupId}/join`
- **Description**: Adds a user to a group.
- **Input Schema**:
  ```json
  {
    "userId": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "groupId": "string",
    "userId": "string",
    "role": "string", // "MEMBER"
    "joinedAt": "long"
  }
  ```

### 9. Leave Group
- **Endpoint**: `POST /api/groups/{groupId}/leave`
- **Description**: Removes a user from a group.
- **Input Schema**:
  ```json
  {
    "userId": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "success": "boolean",
    "message": "string"
  }
  ```

### 10. Send Group Message
- **Endpoint**: `POST /api/groups/{groupId}/messages`
- **Description**: Sends a message to a group.
- **Input Schema**:
  ```json
  {
    "senderId": "string",
    "content": "string",
    "type": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "messageId": "string",
    "groupId": "string",
    "timestamp": "long"
  }
  ```

### 11. List Group Members
- **Endpoint**: `GET /api/groups/{groupId}/members`
- **Description**: Lists all members of a group.
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "groupId": "string",
    "members": [
      {
        "userId": "string",
        "username": "string",
        "role": "string"
      }
    ]
  }
  ```

### 12. System Health Check
- **Endpoint**: `GET /api/system/health`
- **Description**: Checks the health status of the service.
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "status": "string", // "UP", "DOWN"
    "uptime": "long",
    "version": "string"
  }
  ```

## Metrics
- **Test Case Pass Rate**: The percentage of automated test cases that pass.
- **Repo Pass Rate**: The percentage of repositories that successfully implement the required features.
