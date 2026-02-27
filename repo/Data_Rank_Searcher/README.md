# Data Rank Searcher

## Description

Data Rank Searcher is a data management service that supports pagination, sorting, searching, and fuzzy queries. The service provides RESTful API interfaces for managing data records and supporting flexible query functionalities.

### Core Features

1. **Data Management**: Add, query, and delete data records.
2. **Pagination**: Supports data pagination by page number and items per page.
3. **Sorting**: Supports ascending or descending sorting by specified fields.
4. **Exact Search**: Supports exact match queries by field.
5. **Fuzzy Query**: Supports fuzzy match queries by field.

## Interface Definitions

### Service Configuration

- **Listening Port**: 8080
- **Base URL**: `http://localhost:8080`

### API Interfaces

#### 1. Add Data Record

- **Interface Name**: `POST /api/data`
- **Description**: Adds a new data record.
- **Input Schema**:
```json
{
  "name": "string (required)",
  "category": "string (required)",
  "score": "number (required)",
  "description": "string (optional)",
  "tags": "array of strings (optional)"
}
```
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "data": {
    "id": "string",
    "name": "string",
    "category": "string",
    "score": "number",
    "description": "string",
    "tags": "array of strings",
    "created_at": "string (ISO 8601 format)"
  }
}
```

#### 2. Query Data Records

- **Interface Name**: `GET /api/data`
- **Description**: Queries data records with support for pagination, sorting, exact search, and fuzzy queries.
- **Query Parameters**:
  - `page`: Page number, starting from 1 (default: 1)
  - `page_size`: Number of items per page (default: 10, max: 100)
  - `sort_by`: Sorting field (optional values: name, category, score, created_at)
  - `sort_order`: Sorting order (optional values: asc, desc, default: asc)
  - `search_field`: Field name for exact search
  - `search_value`: Value for exact search
  - `fuzzy_field`: Field name for fuzzy query
  - `fuzzy_value`: Value for fuzzy query
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "category": "string",
        "score": "number",
        "description": "string",
        "tags": "array of strings",
        "created_at": "string"
      }
    ],
    "pagination": {
      "page": "number",
      "page_size": "number",
      "total_items": "number",
      "total_pages": "number"
    }
  }
}
```

#### 3. Get Single Data Record

- **Interface Name**: `GET /api/data/{id}`
- **Description**: Retrieves a single data record by ID.
- **Path Parameters**:
  - `id`: Data record ID
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "data": {
    "id": "string",
    "name": "string",
    "category": "string",
    "score": "number",
    "description": "string",
    "tags": "array of strings",
    "created_at": "string"
  }
}
```

#### 4. Delete Data Record

- **Interface Name**: `DELETE /api/data/{id}`
- **Description**: Deletes a data record by ID.
- **Path Parameters**:
  - `id`: Data record ID
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string"
}
```

## Implementation Requirements

1. The service should correctly handle all defined interfaces.
2. All responses should conform to the defined schemas.
3. Support concurrent request processing.
4. Error handling should return appropriate HTTP status codes and error messages.
5. Data persistence (can use in-memory storage or a database).

## Testing Instructions

Test cases are located under the `tests/` directory. All tests are real interface tests and do not use mocks. Ensure the service is started and listening on port 8080 before running tests.
