# Spark Dashboard Backend Benchmark

## Project Overview
This project is a benchmark for a "Data Visualization Dashboard Backend" built using the Spark Java framework. It provides a set of RESTful APIs to manage dashboards, widgets, data sources, and datasets, as well as execute queries.

## Functional Requirements
The backend service should support the following core features:
1.  **User Authentication**: Simple login mechanism.
2.  **Dashboard Management**: Create, read, update, and delete dashboards.
3.  **Widget Management**: Add, update, and remove widgets from dashboards.
4.  **Data Source Management**: Manage connections to various data sources (mocked for this benchmark).
5.  **Dataset Management**: Define datasets derived from data sources.
6.  **Query Execution**: Execute queries against datasets to retrieve data for widgets.
7.  **User Profile**: View and update user profile information.

## API Definitions
The service listens on port `4567` (default for Spark Java).

### 1. User Login
- **Endpoint**: `POST /api/login`
- **Description**: Authenticates a user.
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
    "user": {
      "id": "string",
      "username": "string",
      "email": "string"
    }
  }
  ```

### 2. List Dashboards
- **Endpoint**: `GET /api/dashboards`
- **Description**: Retrieves a list of all dashboards.
- **Input Schema**: None
- **Output Schema**:
  ```json
  [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "created_at": "string",
      "updated_at": "string"
    }
  ]
  ```

### 3. Create Dashboard
- **Endpoint**: `POST /api/dashboards`
- **Description**: Creates a new dashboard.
- **Input Schema**:
  ```json
  {
    "title": "string",
    "description": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "created_at": "string",
    "updated_at": "string"
  }
  ```

### 4. Get Dashboard Details
- **Endpoint**: `GET /api/dashboards/:id`
- **Description**: Retrieves detailed information about a specific dashboard, including its widgets.
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "widgets": [
      {
        "id": "string",
        "type": "string",
        "title": "string",
        "config": {}
      }
    ],
    "created_at": "string",
    "updated_at": "string"
  }
  ```

### 5. Update Dashboard
- **Endpoint**: `PUT /api/dashboards/:id`
- **Description**: Updates an existing dashboard's metadata.
- **Input Schema**:
  ```json
  {
    "title": "string",
    "description": "string"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "updated_at": "string"
  }
  ```

### 6. Delete Dashboard
- **Endpoint**: `DELETE /api/dashboards/:id`
- **Description**: Deletes a dashboard.
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "message": "Dashboard deleted successfully"
  }
  ```

### 7. Add Widget to Dashboard
- **Endpoint**: `POST /api/dashboards/:id/widgets`
- **Description**: Adds a new widget to a dashboard.
- **Input Schema**:
  ```json
  {
    "type": "string",
    "title": "string",
    "config": {
      "dataset_id": "string",
      "visualization_type": "string"
    }
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "string",
    "dashboard_id": "string",
    "type": "string",
    "title": "string",
    "config": {},
    "created_at": "string"
  }
  ```

### 8. Update Widget
- **Endpoint**: `PUT /api/widgets/:id`
- **Description**: Updates an existing widget.
- **Input Schema**:
  ```json
  {
    "title": "string",
    "config": {}
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "string",
    "title": "string",
    "config": {},
    "updated_at": "string"
  }
  ```

### 9. Delete Widget
- **Endpoint**: `DELETE /api/widgets/:id`
- **Description**: Deletes a widget.
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "message": "Widget deleted successfully"
  }
  ```

### 10. List Data Sources
- **Endpoint**: `GET /api/datasources`
- **Description**: Lists available data sources.
- **Input Schema**: None
- **Output Schema**:
  ```json
  [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "connection_details": {}
    }
  ]
  ```

### 11. Create Data Source
- **Endpoint**: `POST /api/datasources`
- **Description**: Creates a new data source connection.
- **Input Schema**:
  ```json
  {
    "name": "string",
    "type": "string",
    "connection_details": {
      "url": "string",
      "username": "string"
    }
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "string",
    "name": "string",
    "type": "string",
    "created_at": "string"
  }
  ```

### 12. List Datasets
- **Endpoint**: `GET /api/datasets`
- **Description**: Lists defined datasets.
- **Input Schema**: None
- **Output Schema**:
  ```json
  [
    {
      "id": "string",
      "name": "string",
      "datasource_id": "string",
      "query": "string"
    }
  ]
  ```

### 13. Execute Query
- **Endpoint**: `POST /api/query`
- **Description**: Executes a query against a dataset to fetch data.
- **Input Schema**:
  ```json
  {
    "dataset_id": "string",
    "filters": {}
  }
  ```
- **Output Schema**:
  ```json
  {
    "columns": ["string"],
    "data": [
      ["value1", "value2"]
    ]
  }
  ```

### 14. Get Current User Info
- **Endpoint**: `GET /api/users/me`
- **Description**: Retrieves information about the currently logged-in user.
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "string"
  }
  ```

### 15. Update User Profile
- **Endpoint**: `PUT /api/users/me`
- **Description**: Updates the current user's profile.
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
    "id": "string",
    "username": "string",
    "email": "string",
    "updated_at": "string"
  }
  ```

## Metrics
- **Test Case Pass Rate**: The percentage of automated test cases that pass.
- **Repo Pass Rate**: The percentage of repositories that successfully implement the required functionality (for benchmark evaluation).
