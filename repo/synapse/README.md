## Microservice Requirements Document: Synapse Message Service (Benchmark Version)

This requirement is for benchmark evaluation, defining only the external web microservice interface contracts and acceptance criteria, enabling any implementation to be compared and tested according to unified standards. The document does not involve any function names or internal implementation details.

### Service Information
- Service Name: Synapse Message Service (Benchmark Version)
- Listening Port: 8080 (can be overridden via environment variables, tests default to `http://localhost:8080`)
- Base Path: /

### Authentication Convention
- Uses Bearer Token-based authentication scheme.
- All interfaces except health check, registration, and login require `Authorization: Bearer <token>` in the request header.

### Interface Overview
1) Health Check
- Interface Name: HealthCheck
- Method and Path: GET /health
- Input: None
- Output: JSON, see output schema below

2) User Registration
- Interface Name: RegisterUser
- Method and Path: POST /register
- Input: JSON, see input schema below
- Output: JSON, see output schema below

3) User Login
- Interface Name: LoginUser
- Method and Path: POST /login
- Input: JSON, see input schema below
- Output: JSON, see output schema below (includes token)

4) Send Message
- Interface Name: SendMessage
- Method and Path: POST /rooms/{room_id}/messages
- Authentication: Required
- Input: JSON, see input schema below
- Output: JSON, see output schema below

5) Get Message List
- Interface Name: ListMessages
- Method and Path: GET /rooms/{room_id}/messages
- Query Parameters: `limit` (optional, integer, default 20, range 1..100)
- Authentication: Required
- Input: None (query parameters only)
- Output: JSON, see output schema below

### Input and Output Schemas (JSON Schema 2020-12 Compatible)

1) HealthCheck Output Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["status", "service", "time"],
  "properties": {
    "status": {"type": "string", "enum": ["ok"]},
    "service": {"type": "string", "const": "synapse-benchmark"},
    "time": {"type": "string", "format": "date-time"}
  },
  "additionalProperties": false
}
```

2) RegisterUser Input Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["username", "password"],
  "properties": {
    "username": {"type": "string", "minLength": 3, "maxLength": 64},
    "password": {"type": "string", "minLength": 6, "maxLength": 128},
    "display_name": {"type": "string", "minLength": 1, "maxLength": 128}
  },
  "additionalProperties": false
}
```

RegisterUser Output Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["user_id"],
  "properties": {
    "user_id": {"type": "string", "pattern": "^@[^:]+:[^:]+$"}
  },
  "additionalProperties": false
}
```

3) LoginUser Input Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["username", "password"],
  "properties": {
    "username": {"type": "string"},
    "password": {"type": "string"}
  },
  "additionalProperties": false
}
```

LoginUser Output Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["access_token", "token_type", "expires_in"],
  "properties": {
    "access_token": {"type": "string", "minLength": 8},
    "token_type": {"type": "string", "const": "Bearer"},
    "expires_in": {"type": "integer", "minimum": 60}
  },
  "additionalProperties": false
}
```

4) SendMessage Input Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["type", "content"],
  "properties": {
    "type": {"type": "string", "enum": ["m.text"]},
    "content": {
      "type": "object",
      "required": ["body"],
      "properties": {
        "body": {"type": "string", "minLength": 1, "maxLength": 4000}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

SendMessage Output Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["event_id", "room_id", "ts"],
  "properties": {
    "event_id": {"type": "string", "pattern": "^\$[A-Za-z0-9]+$"},
    "room_id": {"type": "string", "pattern": "^![A-Za-z0-9]+:[^:]+$"},
    "ts": {"type": "integer", "minimum": 0}
  },
  "additionalProperties": false
}
```

5) ListMessages Output Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["room_id", "messages"],
  "properties": {
    "room_id": {"type": "string", "pattern": "^![A-Za-z0-9]+:[^:]+$"},
    "messages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["event_id", "sender", "type", "content", "ts"],
        "properties": {
          "event_id": {"type": "string", "pattern": "^\$[A-Za-z0-9]+$"},
          "sender": {"type": "string", "pattern": "^@[^:]+:[^:]+$"},
          "type": {"type": "string", "enum": ["m.text"]},
          "content": {
            "type": "object",
            "required": ["body"],
            "properties": {
              "body": {"type": "string"}
            },
            "additionalProperties": false
          },
          "ts": {"type": "integer", "minimum": 0}
        },
        "additionalProperties": false
      }
    },
    "next_cursor": {"type": ["string", "null"]}
  },
  "additionalProperties": false
}
```

### Example Requests and Responses

HealthCheck
```http
GET /health HTTP/1.1
```

```json
{ "status": "ok", "service": "synapse-benchmark", "time": "2025-01-01T00:00:00Z" }
```

RegisterUser
```http
POST /register HTTP/1.1
Content-Type: application/json

{ "username": "alice", "password": "secret123", "display_name": "Alice" }
```

```json
{ "user_id": "@alice:example.org" }
```

LoginUser
```http
POST /login HTTP/1.1
Content-Type: application/json

{ "username": "alice", "password": "secret123" }
```

```json
{ "access_token": "token-xxx", "token_type": "Bearer", "expires_in": 3600 }
```

SendMessage
```http
POST /rooms/!room123:example.org/messages HTTP/1.1
Authorization: Bearer token-xxx
Content-Type: application/json

{ "type": "m.text", "content": { "body": "hello" } }
```

```json
{ "event_id": "$abc123", "room_id": "!room123:example.org", "ts": 1700000000 }
```

ListMessages
```http
GET /rooms/!room123:example.org/messages?limit=2 HTTP/1.1
Authorization: Bearer token-xxx
```

```json
{
  "room_id": "!room123:example.org",
  "messages": [
    {
      "event_id": "$abc123",
      "sender": "@alice:example.org",
      "type": "m.text",
      "content": { "body": "hello" },
      "ts": 1700000000
    }
  ],
  "next_cursor": null
}
```

### Testing Instructions
- Test cases default to `http://localhost:8080`, can be overridden via environment variable `SYNAPSE_BASE_URL`.
- When no available service is provided, tests will skip service interaction test cases and only perform contract and schema validation.
