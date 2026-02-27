"""
Test configuration and fixtures for GameBackend API tests.
"""
import pytest
import requests
import json
import uuid
from typing import Dict, Any, List


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the GameBackend API."""
    return "http://localhost:8080"


@pytest.fixture(scope="session")
def api_version():
    """API version."""
    return "v1"


@pytest.fixture(scope="session")
def api_base_url(base_url, api_version):
    """Complete API base URL."""
    return f"{base_url}/api/{api_version}"


@pytest.fixture
def sample_player_data():
    """Sample player data for testing."""
    return {
        "player_id": str(uuid.uuid4()),
        "player_name": "TestPlayer"
    }


@pytest.fixture
def sample_room_data():
    """Sample room creation data."""
    return {
        "room_name": "Test Room",
        "max_players": 4,
        "game_type": "battle"
    }


@pytest.fixture
def sample_room_with_password():
    """Sample room with password."""
    return {
        "room_name": "Private Room",
        "max_players": 2,
        "game_type": "coop",
        "password": "secret123"
    }


@pytest.fixture
def sample_score_data():
    """Sample score submission data."""
    return {
        "player_id": str(uuid.uuid4()),
        "player_name": "ScorePlayer",
        "score": 1500,
        "game_type": "battle"
    }


@pytest.fixture
def sample_game_state():
    """Sample game state data."""
    return {
        "room_id": str(uuid.uuid4()),
        "player_id": str(uuid.uuid4()),
        "game_state": {
            "board": [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
            "turn": 1,
            "moves": 5
        },
        "action": "move",
        "timestamp": "2024-01-01T12:00:00Z"
    }


@pytest.fixture
def created_room(api_base_url, sample_room_data):
    """Create a room for testing and return room data."""
    try:
        response = make_request("POST", f"{api_base_url}/rooms", json=sample_room_data)
        if response.status_code == 201:
            return response.json()
    except Exception:
        pass  # Service might not be running
    return None


@pytest.fixture
def joined_room(api_base_url, created_room, sample_player_data):
    """Create a room and join it with a player."""
    if not created_room:
        return None
    
    try:
        join_data = {
            "player_id": sample_player_data["player_id"],
            "player_name": sample_player_data["player_name"]
        }
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{created_room['room_id']}/join",
            json=join_data
        )
        
        if response.status_code == 200:
            return {
                "room": created_room,
                "player": sample_player_data,
                "join_response": response.json()
            }
    except Exception:
        pass  # Service might not be running
    return None


@pytest.fixture
def multiple_players():
    """Create multiple player data for testing."""
    return [
        {
            "player_id": str(uuid.uuid4()),
            "player_name": f"Player{i}"
        }
        for i in range(1, 6)
    ]


@pytest.fixture
def sample_leaderboard_data():
    """Sample leaderboard entries for testing."""
    return [
        {
            "player_id": str(uuid.uuid4()),
            "player_name": "TopPlayer1",
            "score": 2000,
            "game_type": "battle"
        },
        {
            "player_id": str(uuid.uuid4()),
            "player_name": "TopPlayer2",
            "score": 1800,
            "game_type": "battle"
        },
        {
            "player_id": str(uuid.uuid4()),
            "player_name": "CoopPlayer1",
            "score": 1500,
            "game_type": "coop"
        }
    ]


def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request with error handling."""
    try:
        response = requests.request(method, url, **kwargs)
        return response
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {e}")


def assert_response_success(response: requests.Response, expected_status: int = 200):
    """Assert response is successful."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"


def assert_response_error(response: requests.Response, expected_status: int):
    """Assert response is an error."""
    assert response.status_code == expected_status, f"Expected error {expected_status}, got {response.status_code}. Response: {response.text}"
    
    try:
        error_data = response.json()
        assert "error" in error_data, "Error response should contain 'error' field"
        assert "code" in error_data["error"], "Error should contain 'code' field"
        assert "message" in error_data["error"], "Error should contain 'message' field"
    except json.JSONDecodeError:
        pytest.fail(f"Invalid JSON in error response: {response.text}")


def validate_uuid(uuid_string: str) -> bool:
    """Validate if string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def validate_iso8601(date_string: str) -> bool:
    """Validate if string is a valid ISO 8601 date."""
    try:
        from datetime import datetime
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False
