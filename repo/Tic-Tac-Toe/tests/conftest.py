"""
Pytest configuration and fixtures for Tic-Tac-Toe Web Game API tests
"""

import pytest
import requests


@pytest.fixture(scope="session")
def api_base_url():
    return "http://localhost:8082/api/v1"


@pytest.fixture(scope="session")
def api_health_check(api_base_url):
    try:
        resp = requests.get(f"{api_base_url}/health", timeout=5)
        if resp.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    pytest.skip("API server not running on localhost:8082")


@pytest.fixture(autouse=True)
def cleanup_games(api_base_url, api_health_check):
    # Best-effort cleanup if API exposes list endpoint; otherwise no-op
    yield
