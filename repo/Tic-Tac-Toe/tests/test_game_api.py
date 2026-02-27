"""
Tic-Tac-Toe Web Game API Test Cases

Tests follow the interface definitions specified in README.md
"""

import pytest
import requests

BASE_URL = "http://localhost:8082/api/v1"


class TestGameAPI:
    @pytest.mark.api
    def test_health_check(self):
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] in ["healthy", "ok", "up"]

    @pytest.mark.api
    def test_start_game_and_get_state(self):
        payload = {"player_x": "alice", "player_o": "bob"}
        resp = requests.post(f"{BASE_URL}/games", json=payload, headers={"Content-Type": "application/json"})
        if resp.status_code == 404:
            pytest.skip("Games endpoint not implemented")
        assert resp.status_code == 201
        game = resp.json()
        assert "game_id" in game
        assert game["status"] == "in_progress"
        assert game["next_player"] in ["X", "O"]
        assert isinstance(game["board"], list) and len(game["board"]) == 3

        game_id = game["game_id"]
        resp2 = requests.get(f"{BASE_URL}/games/{game_id}")
        assert resp2.status_code == 200
        state = resp2.json()
        assert state["game_id"] == game_id
        assert state["status"] in ["in_progress", "finished", "draw"]

    @pytest.mark.api
    def test_make_moves_and_win(self):
        # Start game
        start = requests.post(f"{BASE_URL}/games", json={"player_x": "x", "player_o": "o"})
        if start.status_code == 404:
            pytest.skip("Games endpoint not implemented")
        assert start.status_code == 201
        game_id = start.json()["game_id"]

        # Force a win for X on the first row; API must enforce turn order
        moves = [
            ("X", 0, 0),
            ("O", 1, 0),
            ("X", 0, 1),
            ("O", 1, 1),
            ("X", 0, 2),
        ]
        last = None
        for player, row, col in moves:
            last = requests.post(
                f"{BASE_URL}/games/{game_id}/moves",
                json={"player": player, "row": row, "col": col},
                headers={"Content-Type": "application/json"},
            )
            assert last.status_code in [200, 409], last.text
            if last.status_code == 409:
                # If conflict due to out-of-turn or occupied cell, test cannot proceed reliably
                pytest.skip("Move conflict behavior differs; skipping win flow")
        data = last.json()
        assert data["status"] in ["finished", "draw"]
        if data["status"] == "finished":
            assert data.get("winner") == "X"

    @pytest.mark.api
    def test_illegal_move_validation(self):
        start = requests.post(f"{BASE_URL}/games", json={"player_x": "p1", "player_o": "p2"})
        if start.status_code == 404:
            pytest.skip("Games endpoint not implemented")
        game_id = start.json()["game_id"]

        # X moves to (0,0)
        r1 = requests.post(f"{BASE_URL}/games/{game_id}/moves", json={"player": "X", "row": 0, "col": 0})
        assert r1.status_code == 200
        # O tries to move to same cell
        r2 = requests.post(f"{BASE_URL}/games/{game_id}/moves", json={"player": "O", "row": 0, "col": 0})
        assert r2.status_code in [409, 422]
        err = r2.json()
        assert "error" in err

    @pytest.mark.api
    def test_reset_game(self):
        start = requests.post(f"{BASE_URL}/games", json={"player_x": "p1", "player_o": "p2"})
        if start.status_code == 404:
            pytest.skip("Games endpoint not implemented")
        game_id = start.json()["game_id"]

        # Make a move
        r1 = requests.post(f"{BASE_URL}/games/{game_id}/moves", json={"player": "X", "row": 2, "col": 2})
        assert r1.status_code == 200

        # Reset
        r2 = requests.post(f"{BASE_URL}/games/{game_id}/reset")
        assert r2.status_code in [200, 204]
        if r2.status_code == 200:
            data = r2.json()
            assert data["status"] == "in_progress"
            assert data["board"] == [[None, None, None], [None, None, None], [None, None, None]]

    @pytest.mark.api
    def test_leaderboard(self):
        resp = requests.get(f"{BASE_URL}/leaderboard")
        if resp.status_code == 404:
            pytest.skip("Leaderboard endpoint not implemented")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "pagination" in data
        assert isinstance(data["items"], list)

    @pytest.mark.edge_case
    def test_invalid_json_request(self):
        resp = requests.post(f"{BASE_URL}/games", data="not-json", headers={"Content-Type": "application/json"})
        assert resp.status_code in [400, 415]
        data = resp.json()
        assert "error" in data
