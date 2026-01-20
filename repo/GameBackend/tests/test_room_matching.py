"""
Test cases for room matching functionality.
"""
import pytest
import requests
import json
from conftest import (
    make_request, assert_response_success, assert_response_error,
    validate_uuid, validate_iso8601
)


class TestRoomCreation:
    """Test room creation functionality."""
    
    @pytest.mark.smoke
    @pytest.mark.room_matching
    def test_create_room_success(self, api_base_url, sample_room_data):
        """Test successful room creation."""
        response = make_request("POST", f"{api_base_url}/rooms", json=sample_room_data)
        assert_response_success(response, 201)
        
        data = response.json()
        assert "room_id" in data
        assert validate_uuid(data["room_id"])
        assert data["room_name"] == sample_room_data["room_name"]
        assert data["max_players"] == sample_room_data["max_players"]
        assert data["current_players"] == 1
        assert data["game_type"] == sample_room_data["game_type"]
        assert data["status"] == "waiting"
        assert "created_at" in data
        assert validate_iso8601(data["created_at"])
        assert "creator_id" in data
        assert validate_uuid(data["creator_id"])
    
    def test_create_room_with_password(self, api_base_url, sample_room_with_password):
        """Test room creation with password."""
        response = make_request("POST", f"{api_base_url}/rooms", json=sample_room_with_password)
        assert_response_success(response, 201)
        
        data = response.json()
        assert data["room_name"] == sample_room_with_password["room_name"]
        assert data["max_players"] == sample_room_with_password["max_players"]
        assert data["game_type"] == sample_room_with_password["game_type"]
    
    def test_create_room_invalid_data(self, api_base_url):
        """Test room creation with invalid data."""
        invalid_data = {
            "room_name": "",  # Empty name
            "max_players": 1,  # Too few players
            "game_type": "invalid"  # Invalid game type
        }
        response = make_request("POST", f"{api_base_url}/rooms", json=invalid_data)
        assert_response_error(response, 400)
    
    def test_create_room_missing_fields(self, api_base_url):
        """Test room creation with missing required fields."""
        incomplete_data = {
            "room_name": "Test Room"
            # Missing max_players and game_type
        }
        response = make_request("POST", f"{api_base_url}/rooms", json=incomplete_data)
        assert_response_error(response, 400)
    
    def test_create_room_max_players_boundary(self, api_base_url):
        """Test room creation with boundary values for max_players."""
        # Test minimum valid value
        min_data = {
            "room_name": "Min Room",
            "max_players": 2,
            "game_type": "battle"
        }
        response = make_request("POST", f"{api_base_url}/rooms", json=min_data)
        assert_response_success(response, 201)
        
        # Test maximum valid value
        max_data = {
            "room_name": "Max Room",
            "max_players": 8,
            "game_type": "battle"
        }
        response = make_request("POST", f"{api_base_url}/rooms", json=max_data)
        assert_response_success(response, 201)
        
        # Test invalid minimum
        invalid_min = {
            "room_name": "Invalid Min",
            "max_players": 1,
            "game_type": "battle"
        }
        response = make_request("POST", f"{api_base_url}/rooms", json=invalid_min)
        assert_response_error(response, 400)
        
        # Test invalid maximum
        invalid_max = {
            "room_name": "Invalid Max",
            "max_players": 9,
            "game_type": "battle"
        }
        response = make_request("POST", f"{api_base_url}/rooms", json=invalid_max)
        assert_response_error(response, 400)


class TestRoomJoining:
    """Test room joining functionality."""
    
    @pytest.mark.smoke
    @pytest.mark.room_matching
    def test_join_room_success(self, api_base_url, created_room, sample_player_data):
        """Test successful room joining."""
        if not created_room:
            pytest.skip("No room created for testing")
        
        join_data = {
            "player_id": sample_player_data["player_id"],
            "player_name": sample_player_data["player_name"]
        }
        
        response = make_request(
            "POST", 
            f"{api_base_url}/rooms/{created_room['room_id']}/join",
            json=join_data
        )
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["success"] is True
        assert "room_info" in data
        room_info = data["room_info"]
        assert room_info["room_id"] == created_room["room_id"]
        assert room_info["current_players"] == 2  # Creator + joiner
        assert len(room_info["players"]) == 2
        
        # Check player in list
        player_ids = [p["player_id"] for p in room_info["players"]]
        assert sample_player_data["player_id"] in player_ids
    
    def test_join_room_with_password(self, api_base_url, sample_room_with_password, sample_player_data):
        """Test joining room with correct password."""
        # Create room with password
        room_response = make_request("POST", f"{api_base_url}/rooms", json=sample_room_with_password)
        assert_response_success(room_response, 201)
        room_data = room_response.json()
        
        # Join with correct password
        join_data = {
            "player_id": sample_player_data["player_id"],
            "player_name": sample_player_data["player_name"],
            "password": sample_room_with_password["password"]
        }
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{room_data['room_id']}/join",
            json=join_data
        )
        assert_response_success(response, 200)
    
    def test_join_room_wrong_password(self, api_base_url, sample_room_with_password, sample_player_data):
        """Test joining room with wrong password."""
        # Create room with password
        room_response = make_request("POST", f"{api_base_url}/rooms", json=sample_room_with_password)
        assert_response_success(room_response, 201)
        room_data = room_response.json()
        
        # Join with wrong password
        join_data = {
            "player_id": sample_player_data["player_id"],
            "player_name": sample_player_data["player_name"],
            "password": "wrongpassword"
        }
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{room_data['room_id']}/join",
            json=join_data
        )
        assert_response_error(response, 403)
    
    def test_join_nonexistent_room(self, api_base_url, sample_player_data):
        """Test joining non-existent room."""
        fake_room_id = "00000000-0000-0000-0000-000000000000"
        join_data = {
            "player_id": sample_player_data["player_id"],
            "player_name": sample_player_data["player_name"]
        }
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{fake_room_id}/join",
            json=join_data
        )
        assert_response_error(response, 404)
    
    @pytest.mark.integration
    @pytest.mark.room_matching
    def test_join_full_room(self, api_base_url, sample_room_data, multiple_players):
        """Test joining a full room."""
        # Create room with max 2 players
        room_data = {
            "room_name": "Full Room",
            "max_players": 2,
            "game_type": "battle"
        }
        room_response = make_request("POST", f"{api_base_url}/rooms", json=room_data)
        assert_response_success(room_response, 201)
        room = room_response.json()
        
        # Join with first player (creator is already in)
        join_data = {
            "player_id": multiple_players[0]["player_id"],
            "player_name": multiple_players[0]["player_name"]
        }
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{room['room_id']}/join",
            json=join_data
        )
        assert_response_success(response, 200)
        
        # Try to join with second player (should fail - room is full)
        join_data = {
            "player_id": multiple_players[1]["player_id"],
            "player_name": multiple_players[1]["player_name"]
        }
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{room['room_id']}/join",
            json=join_data
        )
        assert_response_error(response, 409)
    
    def test_join_room_already_joined(self, api_base_url, created_room, sample_player_data):
        """Test joining room when already joined."""
        if not created_room:
            pytest.skip("No room created for testing")
        
        join_data = {
            "player_id": sample_player_data["player_id"],
            "player_name": sample_player_data["player_name"]
        }
        
        # First join
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{created_room['room_id']}/join",
            json=join_data
        )
        assert_response_success(response, 200)
        
        # Try to join again
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{created_room['room_id']}/join",
            json=join_data
        )
        assert_response_error(response, 409)


class TestRoomListing:
    """Test room listing functionality."""
    
    def test_get_rooms_success(self, api_base_url):
        """Test successful room listing."""
        response = make_request("GET", f"{api_base_url}/rooms")
        assert_response_success(response, 200)
        
        data = response.json()
        assert "rooms" in data
        assert "pagination" in data
        assert isinstance(data["rooms"], list)
        
        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination
    
    def test_get_rooms_with_filters(self, api_base_url):
        """Test room listing with filters."""
        # Test game_type filter
        response = make_request("GET", f"{api_base_url}/rooms?game_type=battle")
        assert_response_success(response, 200)
        
        # Test status filter
        response = make_request("GET", f"{api_base_url}/rooms?status=waiting")
        assert_response_success(response, 200)
        
        # Test pagination
        response = make_request("GET", f"{api_base_url}/rooms?page=1&limit=5")
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 5
    
    def test_get_rooms_invalid_filters(self, api_base_url):
        """Test room listing with invalid filters."""
        # Invalid game_type
        response = make_request("GET", f"{api_base_url}/rooms?game_type=invalid")
        assert_response_error(response, 400)
        
        # Invalid status
        response = make_request("GET", f"{api_base_url}/rooms?status=invalid")
        assert_response_error(response, 400)
        
        # Invalid pagination
        response = make_request("GET", f"{api_base_url}/rooms?page=0")
        assert_response_error(response, 400)
        
        response = make_request("GET", f"{api_base_url}/rooms?limit=0")
        assert_response_error(response, 400)


class TestRoomLeaving:
    """Test room leaving functionality."""
    
    def test_leave_room_success(self, api_base_url, joined_room):
        """Test successful room leaving."""
        if not joined_room:
            pytest.skip("No joined room for testing")
        
        leave_data = {
            "player_id": joined_room["player"]["player_id"]
        }
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{joined_room['room']['room_id']}/leave",
            json=leave_data
        )
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["success"] is True
    
    def test_leave_nonexistent_room(self, api_base_url, sample_player_data):
        """Test leaving non-existent room."""
        fake_room_id = "00000000-0000-0000-0000-000000000000"
        leave_data = {
            "player_id": sample_player_data["player_id"]
        }
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{fake_room_id}/leave",
            json=leave_data
        )
        assert_response_error(response, 404)
    
    def test_leave_room_not_joined(self, api_base_url, created_room, sample_player_data):
        """Test leaving room when not joined."""
        if not created_room:
            pytest.skip("No room created for testing")
        
        leave_data = {
            "player_id": sample_player_data["player_id"]
        }
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{created_room['room_id']}/leave",
            json=leave_data
        )
        assert_response_error(response, 404)
    
    def test_leave_room_missing_player_id(self, api_base_url, created_room):
        """Test leaving room with missing player_id."""
        if not created_room:
            pytest.skip("No room created for testing")
        
        leave_data = {}  # Missing player_id
        
        response = make_request(
            "POST",
            f"{api_base_url}/rooms/{created_room['room_id']}/leave",
            json=leave_data
        )
        assert_response_error(response, 400)
