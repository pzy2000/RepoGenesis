import pytest
import requests
import time
from typing import Generator


BASE_URL = "http://localhost:8080"
API_ENDPOINT = f"{BASE_URL}/api/data"


@pytest.fixture(scope="session", autouse=True)
def check_server_availability():
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=2)
            print(f"\nServer Connected: {BASE_URL}")
            return
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"\nTrying to connect to server ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                pytest.exit(
                    f"Failed to connect to server {BASE_URL}."
                    f"Please ensure the service is started and listening on port 8080.\n"
                    f"Error: {str(e)}"
                )


@pytest.fixture(scope="function")
def clean_test_data():
    created_ids = []
    
    def _register_id(data_id: str):
        created_ids.append(data_id)
    
    yield _register_id
    
    for data_id in created_ids:
        try:
            requests.delete(f"{API_ENDPOINT}/{data_id}", timeout=2)
        except:
            pass


@pytest.fixture(scope="function")
def sample_data():
    return [
        {
            "name": "Sample Item 1",
            "category": "Category A",
            "score": 85.0,
            "description": "This is a sample item for testing",
            "tags": ["test", "sample"]
        },
        {
            "name": "Sample Item 2",
            "category": "Category B",
            "score": 90.0,
            "description": "Another sample item",
            "tags": ["test", "example"]
        },
        {
            "name": "Sample Item 3",
            "category": "Category A",
            "score": 78.5,
            "description": "Third sample item",
            "tags": ["test"]
        }
    ]


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "integration: mark as integration test"
    )


def pytest_collection_modifyitems(config, items):
    for item in items:
        item.add_marker(pytest.mark.integration)

