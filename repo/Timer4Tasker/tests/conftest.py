import pytest
import requests
import time
import json


BASE_URL = "http://localhost:8080/api/v1"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def check_server():
    max_retries = 5
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/stats", timeout=5)
            if response.status_code in [200, 404]:
                return True
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                pytest.fail(
                    f"Server not running or inaccessible: {BASE_URL}\n"
                    "Please start the service first: python app.py"
                )
    return True


@pytest.fixture
def api_client(base_url, check_server):
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            self.session.headers.update({"Content-Type": "application/json"})
        
        def get(self, endpoint, params=None):
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params)
            return response
        
        def post(self, endpoint, data=None):
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=data)
            return response
        
        def put(self, endpoint, data=None):
            url = f"{self.base_url}{endpoint}"
            response = self.session.put(url, json=data)
            return response
        
        def delete(self, endpoint):
            url = f"{self.base_url}{endpoint}"
            response = self.session.delete(url)
            return response
    
    return APIClient(base_url)


@pytest.fixture
def sample_task_data():
    return {
        "file_cleanup": {
            "name": "Clean temporary files",
            "description": "Clean temporary files every day at midnight",
            "task_type": "file_cleanup",
            "schedule": "0 0 * * *",
            "config": {
                "path": "/tmp/app_temp",
                "pattern": "*.tmp",
                "days": 7
            },
            "enabled": True
        },
        "data_summary": {
            "name": "Daily data summary",
            "description": "Daily data summary at 23:00",
            "task_type": "data_summary",
            "schedule": "0 23 * * *",
            "config": {
                "source": "transactions",
                "target": "daily_summary"
            },
            "enabled": True
        },
        "data_backup": {
            "name": "Database backup",
            "description": "Weekly database backup every Sunday at 2:00 AM",
            "task_type": "data_backup",
            "schedule": "0 2 * * 0",
            "config": {
                "source": "database",
                "target": "/backup/db"
            },
            "enabled": False
        }
    }


@pytest.fixture
def cleanup_tasks(api_client):
    created_task_ids = []
    
    yield created_task_ids
    
    for task_id in created_task_ids:
        try:
            api_client.delete(f"/tasks/{task_id}")
        except Exception:
            pass


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: integration test"
    )
    config.addinivalue_line(
        "markers", "slow: slow test"
    )

