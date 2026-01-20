# GameBackend - Game Backend Service

## Project Overview

GameBackend is a backend service system for multiplayer online games, providing room matching, leaderboard management, and game state synchronization functionality. The service adopts RESTful API design, supporting real-time game data management and player interaction.

## Service Configuration

- **Listening Port**: 8080
- **Service Address**: http://localhost:8080
- **API Version**: v1
- **Data Format**: JSON

## Functional Modules

### 1. Room Matching System

#### 1.1 Create Game Room
- **API**: `POST /api/v1/rooms`
- **Function**: Create new game room
- **Input Schema**:
```json
{
  "room_name": "string (required, max 50 chars)",
  "max_players": "integer (required, 2-8)",
  "game_type": "string (required, enum: ['battle', 'coop', 'puzzle'])",
  "password": "string (optional, max 20 chars)"
}
```
- **Output Schema**:
```json
{
  "room_id": "string (uuid)",
  "room_name": "string",
  "max_players": "integer",
  "current_players": "integer (default: 1)",
  "game_type": "string",
  "status": "string (enum: ['waiting', 'playing', 'finished'])",
  "created_at": "string (ISO 8601)",
  "creator_id": "string (uuid)"
}
```

#### 1.2 Join Game Room
- **API**: `POST /api/v1/rooms/{room_id}/join`
- **Function**: Player joins specified room
- **Input Schema**:
```json
{
  "player_id": "string (required, uuid)",
  "player_name": "string (required, max 30 chars)",
  "password": "string (optional, if room has password)"
}
```
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "room_info": {
    "room_id": "string",
    "room_name": "string",
    "current_players": "integer",
    "max_players": "integer",
    "players": [
      {
        "player_id": "string",
        "player_name": "string",
        "joined_at": "string (ISO 8601)"
      }
    ]
  }
}
```

#### 1.3 Get Room List
- **API**: `GET /api/v1/rooms`
- **Function**: Get available game rooms list
- **Query Parameters**:
  - `game_type`: Game type filter (optional)
  - `status`: Room status filter (optional, enum: ['waiting', 'playing'])
  - `page`: Page number (optional, default: 1)
  - `limit`: Items per page (optional, default: 10)
- **Output Schema**:
```json
{
  "rooms": [
    {
      "room_id": "string",
      "room_name": "string",
      "max_players": "integer",
      "current_players": "integer",
      "game_type": "string",
      "status": "string",
      "created_at": "string"
    }
  ],
  "pagination": {
    "page": "integer",
    "limit": "integer",
    "total": "integer",
    "total_pages": "integer"
  }
}
```

#### 1.4 Leave Room
- **API**: `POST /api/v1/rooms/{room_id}/leave`
- **Function**: Player leaves specified room
- **Input Schema**:
```json
{
  "player_id": "string (required, uuid)"
}
```
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string"
}
```

### 2. Leaderboard System

#### 2.1 Update Player Score
- **API**: `POST /api/v1/leaderboard/score`
- **Function**: Update player game score
- **Input Schema**:
```json
{
  "player_id": "string (required, uuid)",
  "player_name": "string (required, max 30 chars)",
  "score": "integer (required, >= 0)",
  "game_type": "string (required, enum: ['battle', 'coop', 'puzzle'])",
  "room_id": "string (optional, uuid)"
}
```
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "player_rank": "integer",
  "score": "integer"
}
```

#### 2.2 Get Leaderboard
- **API**: `GET /api/v1/leaderboard`
- **Function**: Get game leaderboard
- **Query Parameters**:
  - `game_type`: Game type (optional, default: all)
  - `time_range`: Time range (optional, enum: ['daily', 'weekly', 'monthly', 'all'], default: 'all')
  - `limit`: Return count (optional, default: 100, max: 1000)
- **Output Schema**:
```json
{
  "leaderboard": [
    {
      "rank": "integer",
      "player_id": "string",
      "player_name": "string",
      "score": "integer",
      "game_type": "string",
      "updated_at": "string (ISO 8601)"
    }
  ],
  "time_range": "string",
  "game_type": "string",
  "total_players": "integer"
}
```

#### 2.3 Get Player Rank
- **API**: `GET /api/v1/leaderboard/player/{player_id}`
- **Function**: Get specified player's ranking information
- **Query Parameters**:
  - `game_type`: Game type (optional)
- **Output Schema**:
```json
{
  "player_id": "string",
  "player_name": "string",
  "rank": "integer",
  "score": "integer",
  "game_type": "string",
  "updated_at": "string (ISO 8601)"
}
```

### 3. Game State Synchronization

#### 3.1 Update Game State
- **API**: `POST /api/v1/game/state`
- **Function**: Update room game state
- **Input Schema**:
```json
{
  "room_id": "string (required, uuid)",
  "player_id": "string (required, uuid)",
  "game_state": "object (required, game-specific state data)",
  "action": "string (required, enum: ['move', 'attack', 'defend', 'end_turn', 'game_over'])",
  "timestamp": "string (required, ISO 8601)"
}
```
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "game_state": "object",
  "next_player": "string (uuid, optional)",
  "room_status": "string (enum: ['playing', 'finished'])"
}
```

#### 3.2 Get Game State
- **API**: `GET /api/v1/game/state/{room_id}`
- **Function**: Get current game state of specified room
- **Output Schema**:
```json
{
  "room_id": "string",
  "game_state": "object",
  "current_player": "string (uuid)",
  "status": "string (enum: ['waiting', 'playing', 'finished'])",
  "last_updated": "string (ISO 8601)",
  "players": [
    {
      "player_id": "string",
      "player_name": "string",
      "is_ready": "boolean"
    }
  ]
}
```

#### 3.3 Player Ready Status
- **API**: `POST /api/v1/game/ready`
- **Function**: Set player ready status
- **Input Schema**:
```json
{
  "room_id": "string (required, uuid)",
  "player_id": "string (required, uuid)",
  "is_ready": "boolean (required)"
}
```
- **Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "all_ready": "boolean",
  "game_started": "boolean"
}
```

## Error Handling

All API interfaces return unified error format:
```json
{
  "error": {
    "code": "string (error code)",
    "message": "string (error description)",
    "details": "object (optional, additional error info)"
  }
}
```

Common Error Codes:
- `400`: Request parameter error
- `401`: Unauthorized access
- `403`: Forbidden access
- `404`: Resource not found
- `409`: Resource conflict
- `429`: Request rate limit
- `500`: Internal server error

## Performance Metrics

### Response Time Requirements
- Room operation APIs: < 200ms
- Leaderboard query APIs: < 300ms
- Game state synchronization APIs: < 100ms

### Concurrency Requirements
- Support concurrent online players: 10,000+
- Support concurrent game rooms: 1,000+
- Support requests per second: 5,000+

## Deployment Instructions

1. Ensure Python 3.8+ environment
2. Install dependencies: `pip install -r requirements.txt`
3. Start service: `python app.py`
4. Service will start at http://localhost:8080

## Development Standards

- Follow RESTful API design principles
- Use JSON format for data exchange
- Implement complete error handling mechanisms
- Provide detailed API documentation
- Ensure code testability and maintainability
