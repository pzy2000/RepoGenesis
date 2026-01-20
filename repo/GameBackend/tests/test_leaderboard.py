"""
Test cases for leaderboard functionality.
"""
import pytest
import requests
import json
from conftest import (
    make_request, assert_response_success, assert_response_error,
    validate_uuid, validate_iso8601
)


class TestScoreSubmission:
    """Test score submission functionality."""
    
    @pytest.mark.smoke
    @pytest.mark.leaderboard
    def test_submit_score_success(self, api_base_url, sample_score_data):
        """Test successful score submission."""
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=sample_score_data)
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["success"] is True
        assert "player_rank" in data
        assert data["score"] == sample_score_data["score"]
        assert isinstance(data["player_rank"], int)
        assert data["player_rank"] >= 1
    
    def test_submit_score_with_room_id(self, api_base_url, sample_score_data):
        """Test score submission with room_id."""
        score_data = sample_score_data.copy()
        score_data["room_id"] = "00000000-0000-0000-0000-000000000000"
        
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=score_data)
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["success"] is True
    
    def test_submit_score_invalid_data(self, api_base_url):
        """Test score submission with invalid data."""
        invalid_data = {
            "player_id": "invalid-uuid",
            "player_name": "",
            "score": -100,
            "game_type": "invalid"
        }
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=invalid_data)
        assert_response_error(response, 400)
    
    def test_submit_score_missing_fields(self, api_base_url):
        """Test score submission with missing required fields."""
        incomplete_data = {
            "player_id": "00000000-0000-0000-0000-000000000000",
            "score": 1000
            # Missing player_name and game_type
        }
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=incomplete_data)
        assert_response_error(response, 400)
    
    def test_submit_score_boundary_values(self, api_base_url, sample_score_data):
        """Test score submission with boundary values."""
        # Test minimum score (0)
        min_score_data = sample_score_data.copy()
        min_score_data["score"] = 0
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=min_score_data)
        assert_response_success(response, 200)
        
        # Test large score
        large_score_data = sample_score_data.copy()
        large_score_data["score"] = 999999
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=large_score_data)
        assert_response_success(response, 200)
        
        # Test negative score (should fail)
        negative_score_data = sample_score_data.copy()
        negative_score_data["score"] = -1
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=negative_score_data)
        assert_response_error(response, 400)
    
    def test_submit_score_different_game_types(self, api_base_url, sample_score_data):
        """Test score submission for different game types."""
        game_types = ["battle", "coop", "puzzle"]
        
        for game_type in game_types:
            score_data = sample_score_data.copy()
            score_data["game_type"] = game_type
            score_data["player_id"] = f"00000000-0000-0000-0000-00000000000{game_types.index(game_type)}"
            
            response = make_request("POST", f"{api_base_url}/leaderboard/score", json=score_data)
            assert_response_success(response, 200)
            
            data = response.json()
            assert data["success"] is True


class TestLeaderboardRetrieval:
    """Test leaderboard retrieval functionality."""
    
    def test_get_leaderboard_success(self, api_base_url):
        """Test successful leaderboard retrieval."""
        response = make_request("GET", f"{api_base_url}/leaderboard")
        assert_response_success(response, 200)
        
        data = response.json()
        assert "leaderboard" in data
        assert "time_range" in data
        assert "game_type" in data
        assert "total_players" in data
        assert isinstance(data["leaderboard"], list)
        assert isinstance(data["total_players"], int)
    
    def test_get_leaderboard_with_filters(self, api_base_url):
        """Test leaderboard retrieval with filters."""
        # Test game_type filter
        response = make_request("GET", f"{api_base_url}/leaderboard?game_type=battle")
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["game_type"] == "battle"
        
        # Test time_range filter
        time_ranges = ["daily", "weekly", "monthly", "all"]
        for time_range in time_ranges:
            response = make_request("GET", f"{api_base_url}/leaderboard?time_range={time_range}")
            assert_response_success(response, 200)
            
            data = response.json()
            assert data["time_range"] == time_range
        
        # Test limit filter
        response = make_request("GET", f"{api_base_url}/leaderboard?limit=10")
        assert_response_success(response, 200)
        
        data = response.json()
        assert len(data["leaderboard"]) <= 10
    
    def test_get_leaderboard_invalid_filters(self, api_base_url):
        """Test leaderboard retrieval with invalid filters."""
        # Invalid game_type
        response = make_request("GET", f"{api_base_url}/leaderboard?game_type=invalid")
        assert_response_error(response, 400)
        
        # Invalid time_range
        response = make_request("GET", f"{api_base_url}/leaderboard?time_range=invalid")
        assert_response_error(response, 400)
        
        # Invalid limit (too high)
        response = make_request("GET", f"{api_base_url}/leaderboard?limit=2000")
        assert_response_error(response, 400)
        
        # Invalid limit (negative)
        response = make_request("GET", f"{api_base_url}/leaderboard?limit=-1")
        assert_response_error(response, 400)
    
    def test_get_leaderboard_ranking_order(self, api_base_url, sample_leaderboard_data):
        """Test that leaderboard returns scores in correct ranking order."""
        # Submit multiple scores
        for i, score_data in enumerate(sample_leaderboard_data):
            response = make_request("POST", f"{api_base_url}/leaderboard/score", json=score_data)
            assert_response_success(response, 200)
        
        # Get leaderboard
        response = make_request("GET", f"{api_base_url}/leaderboard")
        assert_response_success(response, 200)
        
        data = response.json()
        leaderboard = data["leaderboard"]
        
        # Check that scores are in descending order
        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]["score"] >= leaderboard[i + 1]["score"]
        
        # Check that ranks are sequential
        for i, entry in enumerate(leaderboard):
            assert entry["rank"] == i + 1
    
    def test_get_leaderboard_entry_structure(self, api_base_url, sample_score_data):
        """Test that leaderboard entries have correct structure."""
        # Submit a score
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=sample_score_data)
        assert_response_success(response, 200)
        
        # Get leaderboard
        response = make_request("GET", f"{api_base_url}/leaderboard")
        assert_response_success(response, 200)
        
        data = response.json()
        leaderboard = data["leaderboard"]
        
        if leaderboard:
            entry = leaderboard[0]
            assert "rank" in entry
            assert "player_id" in entry
            assert "player_name" in entry
            assert "score" in entry
            assert "game_type" in entry
            assert "updated_at" in entry
            
            assert isinstance(entry["rank"], int)
            assert validate_uuid(entry["player_id"])
            assert isinstance(entry["player_name"], str)
            assert isinstance(entry["score"], int)
            assert entry["game_type"] in ["battle", "coop", "puzzle"]
            assert validate_iso8601(entry["updated_at"])


class TestPlayerRanking:
    """Test individual player ranking functionality."""
    
    def test_get_player_rank_success(self, api_base_url, sample_score_data):
        """Test successful player rank retrieval."""
        # Submit a score first
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=sample_score_data)
        assert_response_success(response, 200)
        
        # Get player rank
        response = make_request("GET", f"{api_base_url}/leaderboard/player/{sample_score_data['player_id']}")
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["player_id"] == sample_score_data["player_id"]
        assert data["player_name"] == sample_score_data["player_name"]
        assert "rank" in data
        assert "score" in data
        assert "game_type" in data
        assert "updated_at" in data
        
        assert isinstance(data["rank"], int)
        assert data["rank"] >= 1
        assert data["score"] == sample_score_data["score"]
        assert validate_iso8601(data["updated_at"])
    
    def test_get_player_rank_with_game_type(self, api_base_url, sample_score_data):
        """Test player rank retrieval with game_type filter."""
        # Submit a score first
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=sample_score_data)
        assert_response_success(response, 200)
        
        # Get player rank with game_type filter
        response = make_request(
            "GET", 
            f"{api_base_url}/leaderboard/player/{sample_score_data['player_id']}?game_type={sample_score_data['game_type']}"
        )
        assert_response_success(response, 200)
        
        data = response.json()
        assert data["game_type"] == sample_score_data["game_type"]
    
    # def test_get_player_rank_nonexistent_player(self, api_base_url):
    #     """Test getting rank for non-existent player."""
    #     fake_player_id = "00000000-0000-0000-0000-000000000000"
    #     response = make_request("GET", f"{api_base_url}/leaderboard/player/{fake_player_id}")
    #     assert_response_error(response, 404)
    
    def test_get_player_rank_invalid_uuid(self, api_base_url):
        """Test getting rank with invalid UUID."""
        invalid_uuid = "invalid-uuid"
        response = make_request("GET", f"{api_base_url}/leaderboard/player/{invalid_uuid}")
        assert_response_error(response, 400)
    
    def test_get_player_rank_invalid_game_type(self, api_base_url, sample_score_data):
        """Test getting player rank with invalid game_type filter."""
        # Submit a score first
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=sample_score_data)
        assert_response_success(response, 200)
        
        # Get player rank with invalid game_type
        response = make_request(
            "GET",
            f"{api_base_url}/leaderboard/player/{sample_score_data['player_id']}?game_type=invalid"
        )
        assert_response_error(response, 400)


class TestLeaderboardIntegration:
    """Integration tests for leaderboard functionality."""
    
    @pytest.mark.integration
    @pytest.mark.leaderboard
    def test_score_update_affects_ranking(self, api_base_url, sample_score_data):
        """Test that updating a score affects the player's ranking."""
        # Submit initial score
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=sample_score_data)
        assert_response_success(response, 200)
        initial_rank = response.json()["player_rank"]
        
        # Submit higher score
        higher_score_data = sample_score_data.copy()
        higher_score_data["score"] = sample_score_data["score"] + 1000
        
        response = make_request("POST", f"{api_base_url}/leaderboard/score", json=higher_score_data)
        assert_response_success(response, 200)
        new_rank = response.json()["player_rank"]
        
        # New rank should be better (lower number) or same
        assert new_rank <= initial_rank
    
    def test_multiple_players_ranking(self, api_base_url, sample_leaderboard_data):
        """Test ranking with multiple players."""
        # Submit scores for multiple players
        for score_data in sample_leaderboard_data:
            response = make_request("POST", f"{api_base_url}/leaderboard/score", json=score_data)
            assert_response_success(response, 200)
        
        # Get leaderboard
        response = make_request("GET", f"{api_base_url}/leaderboard")
        assert_response_success(response, 200)
        
        data = response.json()
        leaderboard = data["leaderboard"]
        
        # Check that all submitted players are in the leaderboard
        submitted_player_ids = {score_data["player_id"] for score_data in sample_leaderboard_data}
        leaderboard_player_ids = {entry["player_id"] for entry in leaderboard}
        
        assert submitted_player_ids.issubset(leaderboard_player_ids)
    
    def test_game_type_separation(self, api_base_url, sample_leaderboard_data):
        """Test that different game types have separate leaderboards."""
        # Submit scores for different game types
        for score_data in sample_leaderboard_data:
            response = make_request("POST", f"{api_base_url}/leaderboard/score", json=score_data)
            assert_response_success(response, 200)
        
        # Get leaderboard for each game type
        game_types = set(score_data["game_type"] for score_data in sample_leaderboard_data)
        
        for game_type in game_types:
            response = make_request("GET", f"{api_base_url}/leaderboard?game_type={game_type}")
            assert_response_success(response, 200)
            
            data = response.json()
            leaderboard = data["leaderboard"]
            
            # All entries should be of the specified game type
            for entry in leaderboard:
                assert entry["game_type"] == game_type
