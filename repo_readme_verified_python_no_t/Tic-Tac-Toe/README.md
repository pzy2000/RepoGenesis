# Web Game Microservice - Tic-Tac-Toe

## Functionality Description

This is a web game microservice that provides Tic-Tac-Toe functionality, implementing game start, moves, game state queries, game reset, and leaderboard queries through RESTful APIs. The service is stateless, with game states identified by `game_id` and stored on the server.

## API Definition

### Service Configuration
- **Listening Port**: 8082
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`

### Error Response Format

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
- `404`: Resource not found (e.g., `game_id` does not exist)
- `409`: Resource conflict (e.g., non-current player making move, position already occupied)
- `422`: Data validation failed
- `500`: Internal server error

### API Interfaces

#### Health Check
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

#### Start New Game
- **API Name**: `POST /api/v1/games`
- **Function**: Create a new game and return `game_id`
- **Input Schema**:
```json
{
  "player_x": "string (required, 1-50 chars)",
  "player_o": "string (required, 1-50 chars)"
}
```
- **Output Schema**:
```json
{
  "game_id": "string",
  "board": [
    ["string|null", "string|null", "string|null"],
    ["string|null", "string|null", "string|null"],
    ["string|null", "string|null", "string|null"]
  ],
  "next_player": "string (enum: ['X', 'O'])",
  "status": "string (enum: ['in_progress'])",
  "players": {"X": "string", "O": "string"},
  "created_at": "string",
  "updated_at": "string"
}
```

#### Query Game State
- **API Name**: `GET /api/v1/games/{game_id}`
- **Function**: Get current state of specified game
- **Path Parameters**:
  - `game_id`: string (required)
- **Output Schema**:
```json
{
  "game_id": "string",
  "board": [
    ["string|null", "string|null", "string|null"],
    ["string|null", "string|null", "string|null"],
    ["string|null", "string|null", "string|null"]
  ],
  "next_player": "string (enum: ['X', 'O', null])",
  "status": "string (enum: ['in_progress', 'draw', 'finished'])",
  "winner": "string|null (enum: ['X', 'O', null])",
  "players": {"X": "string", "O": "string"},
  "created_at": "string",
  "updated_at": "string"
}
```

#### Make Move
- **API Name**: `POST /api/v1/games/{game_id}/moves`
- **Function**: Make a move on the board
- **Path Parameters**:
  - `game_id`: string (required)
- **Input Schema**:
```json
{
  "player": "string (enum: ['X', 'O'])",
  "row": "integer (required, 0-2)",
  "col": "integer (required, 0-2)"
}
```
- **Output Schema**:
```json
{
  "game_id": "string",
  "board": [
    ["string|null", "string|null", "string|null"],
    ["string|null", "string|null", "string|null"],
    ["string|null", "string|null", "string|null"]
  ],
  "next_player": "string (enum: ['X', 'O', null])",
  "status": "string (enum: ['in_progress', 'draw', 'finished'])",
  "winner": "string|null (enum: ['X', 'O', null])",
  "last_move": {"player": "string", "row": "integer", "col": "integer"},
  "updated_at": "string"
}
```

Validation Rules:
- Moves only allowed when `status = in_progress`
- Must be the current `next_player` to make a move
- `row` and `col` must be within `[0,2]` range
- Target cell must be empty
- Automatically determine win/loss or draw after move

#### Reset Game
- **API Name**: `POST /api/v1/games/{game_id}/reset`
- **Function**: Reset specified game to initial state
- **Output Schema**:
```json
{
  "game_id": "string",
  "board": [[null, null, null],[null, null, null],[null, null, null]],
  "next_player": "string (enum: ['X', 'O'])",
  "status": "string (enum: ['in_progress'])",
  "updated_at": "string"
}
```

#### Leaderboard
- **API Name**: `GET /api/v1/leaderboard`
- **Function**: Query player win leaderboard in this service (sorted by wins descending, draws don't count)
- **Query Parameters**:
  - `limit`: integer (optional, default: 10, max: 100)
- **Output Schema**:
```json
{
  "items": [
    {"player": "string", "wins": "integer"}
  ],
  "pagination": {"limit": "integer", "total": "integer"}
}
```

## Technical Specifications

- Framework unlimited (Flask/FastAPI/Django, etc. all acceptable)
- Strict input validation
- Unified error responses
- Logging and timestamp fields as ISO 8601 strings

