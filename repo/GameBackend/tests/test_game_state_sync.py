"""
Test cases for game state synchronization functionality.
"""
import pytest
import requests
import json
from conftest import (
    make_request, assert_response_success, assert_response_error,
    validate_uuid, validate_iso8601
)


class TestGameStateUpdate:
    """Test game state update functionality."""
    
    @pytest.mark.smoke
    @pytest.mark.game_state
    def test_update_game_state_success(self, api_base_url, sample_game_state):
        """Test successful game state update."""
        response = make_request("POST", f"{api_base_url}/game/state", json=sample_game_state)
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["success"] is True
        assert "game_state" in data
        assert "room_status" in data
        assert data["room_status"] in ["playing", "finished"]
    
    def test_update_game_state_with_next_player(self, api_base_url, sample_game_state):
        """Test game state update with next player specified."""
        game_state = sample_game_state.copy()
        game_state["action"] = "end_turn"
        
        response = make_request("POST", f"{api_base_url}/game/state", json=game_state)
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["success"] is True
        if "next_player" in data:
            assert validate_uuid(data["next_player"])
    
    def test_update_game_state_game_over(self, api_base_url, sample_game_state):
        """Test game state update with game over action."""
        game_state = sample_game_state.copy()
        game_state["action"] = "game_over"
        
        response = make_request("POST", f"{api_base_url}/game/state", json=game_state)
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["success"] is True
        assert data["room_status"] == "finished"
    
    def test_update_game_state_invalid_data(self, api_base_url):
        """Test game state update with invalid data."""
        invalid_data = {
            "room_id": "invalid-uuid",
            "player_id": "invalid-uuid",
            "game_state": "invalid-state",
            "action": "invalid-action",
            "timestamp": "invalid-timestamp"
        }
        response = make_request("POST", f"{api_base_url}/game/state", json=invalid_data)
        assert_response_error(response, 400)
    
    def test_update_game_state_missing_fields(self, api_base_url):
        """Test game state update with missing required fields."""
        incomplete_data = {
            "room_id": "00000000-0000-0000-0000-000000000000",
            "player_id": "00000000-0000-0000-0000-000000000000"
            # Missing game_state, action, timestamp
        }
        response = make_request("POST", f"{api_base_url}/game/state", json=incomplete_data)
        assert_response_error(response, 400)
    
    def test_update_game_state_invalid_action(self, api_base_url, sample_game_state):
        """Test game state update with invalid action."""
        game_state = sample_game_state.copy()
        game_state["action"] = "invalid_action"
        
        response = make_request("POST", f"{api_base_url}/game/state", json=game_state)
        assert_response_error(response, 400)
    
    def test_update_game_state_invalid_timestamp(self, api_base_url, sample_game_state):
        """Test game state update with invalid timestamp."""
        game_state = sample_game_state.copy()
        game_state["timestamp"] = "invalid-timestamp"
        
        response = make_request("POST", f"{api_base_url}/game/state", json=game_state)
        assert_response_error(response, 400)
    
    def test_update_game_state_different_actions(self, api_base_url, sample_game_state):
        """Test game state update with different valid actions."""
        valid_actions = ["move", "attack", "defend", "end_turn", "game_over"]
        
        for action in valid_actions:
            game_state = sample_game_state.copy()
            game_state["action"] = action
            
            response = make_request("POST", f"{api_base_url}/game/state", json=game_state)
            assert_response_success(response, 200)
            
            data = response.json()
            assert data["success"] is True


class TestGameStateRetrieval:
    """Test game state retrieval functionality."""
    
    def test_get_game_state_success(self, api_base_url, sample_game_state):
        """Test successful game state retrieval."""
        # First update a game state
        response = make_request("POST", f"{api_base_url}/game/state", json=sample_game_state)
        assert_response_success(response, 200)
        
        # Then retrieve it
        response = make_request("GET", f"{api_base_url}/game/state/{sample_game_state['room_id']}")
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["room_id"] == sample_game_state["room_id"]
        assert "game_state" in data
        assert "current_player" in data
        assert "status" in data
        assert "last_updated" in data
        assert "players" in data
        
        assert data["status"] in ["waiting", "playing", "finished"]
        assert validate_uuid(data["current_player"])
        assert validate_iso8601(data["last_updated"])
        assert isinstance(data["players"], list)
    
    def test_get_game_state_nonexistent_room(self, api_base_url):
        """Test getting game state for non-existent room."""
        fake_room_id = "00000000-0000-0000-0000-000000000000"
        response = make_request("GET", f"{api_base_url}/game/state/{fake_room_id}")
        assert_response_error(response, 404)
    
    def test_get_game_state_invalid_uuid(self, api_base_url):
        """Test getting game state with invalid UUID."""
        invalid_uuid = "invalid-uuid"
        response = make_request("GET", f"{api_base_url}/game/state/{invalid_uuid}")
        assert_response_error(response, 400)
    
    def test_get_game_state_structure(self, api_base_url, sample_game_state):
        """Test that retrieved game state has correct structure."""
        # Update game state
        response = make_request("POST", f"{api_base_url}/game/state", json=sample_game_state)
        assert_response_success(response, 200)
        
        # Retrieve game state
        response = make_request("GET", f"{api_base_url}/game/state/{sample_game_state['room_id']}")
        assert_response_success(response, 200)
        
        data = response.json()
        
        # Check players structure
        for player in data["players"]:
            assert "player_id" in player
            assert "player_name" in player
            assert "is_ready" in player
            
            assert validate_uuid(player["player_id"])
            assert isinstance(player["player_name"], str)
            assert isinstance(player["is_ready"], bool)


class TestPlayerReadyState:
    """Test player ready state functionality."""
    
    # def test_set_player_ready_success(self, api_base_url, sample_game_state):
    #     """Test successful player ready state setting."""
    #     ready_data = {
    #         "room_id": sample_game_state["room_id"],
    #         "player_id": sample_game_state["player_id"],
    #         "is_ready": True
    #     }
        
    #     response = make_request("POST", f"{api_base_url}/game/ready", json=ready_data)
    #     assert_response_success(response, 200)
        
    #     data = response.json()
    #     assert data["success"] is True
    #     assert "all_ready" in data
    #     assert "game_started" in data
    #     assert isinstance(data["all_ready"], bool)
    #     assert isinstance(data["game_started"], bool)
    
    # def test_set_player_not_ready(self, api_base_url, sample_game_state):
    #     """Test setting player as not ready."""
    #     ready_data = {
    #         "room_id": sample_game_state["room_id"],
    #         "player_id": sample_game_state["player_id"],
    #         "is_ready": False
    #     }
        
    #     response = make_request("POST", f"{api_base_url}/game/ready", json=ready_data)
    #     assert_response_success(response, 200)
        
    #     data = response.json()
    #     assert data["success"] is True
    #     assert data["all_ready"] is False
    
    def test_set_player_ready_invalid_data(self, api_base_url):
        """Test setting player ready with invalid data."""
        invalid_data = {
            "room_id": "invalid-uuid",
            "player_id": "invalid-uuid",
            "is_ready": "invalid-boolean"
        }
        response = make_request("POST", f"{api_base_url}/game/ready", json=invalid_data)
        assert_response_error(response, 400)
    
    def test_set_player_ready_missing_fields(self, api_base_url):
        """Test setting player ready with missing required fields."""
        incomplete_data = {
            "room_id": "00000000-0000-0000-0000-000000000000"
            # Missing player_id and is_ready
        }
        response = make_request("POST", f"{api_base_url}/game/ready", json=incomplete_data)
        assert_response_error(response, 400)
    
    def test_set_player_ready_nonexistent_room(self, api_base_url, sample_game_state):
        """Test setting player ready for non-existent room."""
        fake_room_id = "00000000-0000-0000-0000-000000000000"
        ready_data = {
            "room_id": fake_room_id,
            "player_id": sample_game_state["player_id"],
            "is_ready": True
        }
        
        response = make_request("POST", f"{api_base_url}/game/ready", json=ready_data)
        assert_response_error(response, 404)
    
    def test_set_player_ready_nonexistent_player(self, api_base_url, sample_game_state):
        """Test setting ready for non-existent player."""
        fake_player_id = "00000000-0000-0000-0000-000000000000"
        ready_data = {
            "room_id": sample_game_state["room_id"],
            "player_id": fake_player_id,
            "is_ready": True
        }
        
        response = make_request("POST", f"{api_base_url}/game/ready", json=ready_data)
        assert_response_error(response, 404)


class TestGameStateIntegration:
    """Integration tests for game state functionality."""
    
    @pytest.mark.integration
    @pytest.mark.game_state
    def test_game_state_consistency(self, api_base_url, sample_game_state):
        """Test that game state updates are consistent."""
        # Update game state
        response = make_request("POST", f"{api_base_url}/game/state", json=sample_game_state)
        assert_response_success(response, 200)
        
        # Retrieve game state
        response = make_request("GET", f"{api_base_url}/game/state/{sample_game_state['room_id']}")
        assert_response_success(response, 200)
        
        retrieved_data = response.json()
        
        # Check that the retrieved state is consistent
        assert retrieved_data["room_id"] == sample_game_state["room_id"]
        assert retrieved_data["status"] in ["waiting", "playing", "finished"]
    
    def test_multiple_state_updates(self, api_base_url, sample_game_state):
        """Test multiple game state updates."""
        # First update
        response = make_request("POST", f"{api_base_url}/game/state", json=sample_game_state)
        assert_response_success(response, 200)
        
        # Second update with different action
        updated_state = sample_game_state.copy()
        updated_state["action"] = "end_turn"
        updated_state["game_state"]["turn"] = 2
        
        response = make_request("POST", f"{api_base_url}/game/state", json=updated_state)
        assert_response_success(response, 200)
        
        # Retrieve final state
        response = make_request("GET", f"{api_base_url}/game/state/{sample_game_state['room_id']}")
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["room_id"] == sample_game_state["room_id"]
    
    # def test_ready_state_affects_game_start(self, api_base_url, sample_game_state):
    #     """Test that player ready states affect game start."""
    #     # Set player as ready
    #     ready_data = {
    #         "room_id": sample_game_state["room_id"],
    #         "player_id": sample_game_state["player_id"],
    #         "is_ready": True
    #     }
        
    #     response = make_request("POST", f"{api_base_url}/game/ready", json=ready_data)
    #     assert_response_success(response, 200)
        
    #     data = response.json()
    #     # Game might start if all players are ready, or might not if more players needed
    #     assert isinstance(data["game_started"], bool)
    
    def test_game_state_with_complex_data(self, api_base_url, sample_game_state):
        """Test game state with complex nested data."""
        complex_state = sample_game_state.copy()
        complex_state["game_state"] = {
            "board": [
                [{"type": "empty", "value": 0}, {"type": "player", "value": 1}],
                [{"type": "obstacle", "value": -1}, {"type": "empty", "value": 0}]
            ],
            "players": [
                {"id": "player1", "position": [0, 1], "health": 100},
                {"id": "player2", "position": [1, 0], "health": 80}
            ],
            "turn": 5,
            "phase": "combat",
            "settings": {
                "time_limit": 30,
                "difficulty": "hard"
            }
        }
        
        response = make_request("POST", f"{api_base_url}/game/state", json=complex_state)
        assert_response_success(response, 200)
        
        # Retrieve and verify
        response = make_request("GET", f"{api_base_url}/game/state/{sample_game_state['room_id']}")
        assert_response_success(response, 200)
        
        data = response.json()
        assert "game_state" in data
        assert isinstance(data["game_state"], dict)
