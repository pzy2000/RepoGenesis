# Web Chatroom Service

## Functionality Description

A simple web chatroom microservice that supports room management and message sending/receiving:

- Health check and service information
- User registration and login (based on simple tokens)
- Room creation, listing, joining/leaving
- Sending and pulling messages within rooms (in chronological order)

This project only contains requirement documentation and test cases for benchmark evaluation.

## API Definition

### Service Listening
- Port: 8083
- Base path: `/api/v1`

### Health Check
- API Name: `GET /api/v1/health`
- Input: None
- Output Schema:
  - `status` string, fixed "ok"
  - `service` string, service name
  - `version` string, semantic version

### Register User
- API Name: `POST /api/v1/auth/register`
- Input Schema (JSON):
  - `username` string, length 3-32, alphanumeric and underscores
  - `password` string, length ≥ 8
- Output Schema:
  - `id` string, unique user identifier
  - `username` string

### User Login
- API Name: `POST /api/v1/auth/login`
- Input Schema (JSON):
  - `username` string
  - `password` string
- Output Schema:
  - `access_token` string, Bearer Token

### Create Room
- API Name: `POST /api/v1/rooms`
- Auth: `Authorization: Bearer <token>`
- Input Schema (JSON):
  - `name` string, length 1-64, unique
- Output Schema:
  - `id` string
  - `name` string
  - `created_at` ISO8601 string

### Room List
- API Name: `GET /api/v1/rooms`
- Query: `page` int≥1, `page_size` 1-100 (default 20)
- Output Schema:
  - `rooms` array[{`id`, `name`}]
  - `page` int
  - `page_size` int
  - `total` int

### Join Room
- API Name: `POST /api/v1/rooms/{room_id}/join`
- Auth: Bearer Token
- Input: None
- Output: `{ "joined": true }`

### Leave Room
- API Name: `POST /api/v1/rooms/{room_id}/leave`
- Auth: Bearer Token
- Input: None
- Output: `{ "left": true }`

### Send Message
- API Name: `POST /api/v1/rooms/{room_id}/messages`
- Auth: Bearer Token (must have joined the room)
- Input Schema (JSON):
  - `content` string, 1-1000 characters
- Output Schema:
  - `id` string
  - `room_id` string
  - `sender` string (username)
  - `content` string
  - `timestamp` ISO8601 string

### Pull Messages
- API Name: `GET /api/v1/rooms/{room_id}/messages`
- Auth: Bearer Token (must have joined the room)
- Query: `since` ISO8601, optional; `limit` 1-100, default 50
- Output Schema:
  - `messages` array[{`id`,`sender`,`content`,`timestamp`}]

## Error Codes and Conventions

- 400: Request body or parameter validation failed
- 401: Unauthenticated or invalid token
- 403: Attempting to send/pull messages without joining room
- 404: Resource not found (room)
- 409: Resource conflict (username or room name already exists)

## Evaluation Metrics

- **Test case pass rate**: Pass rate using this project's test suite
- **Repo pass rate**: Aggregated pass rate of all project tests in current repository

## Test Instructions

Tests are located in the `tests/` directory, based on pytest and requests, covering:

- Health check
- Registration/login
- Rooms (creation, listing, joining/leaving)
- Messages (sending, pulling, ordering)
- Typical errors and boundary scenarios (unauthenticated, not joined, duplicate names, Unicode, pagination boundaries, length limits)

Ensure the service is running at `http://localhost:8083` before running tests.

```bash
pip install -r tests/requirements.txt
pytest -q
```


