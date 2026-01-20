"""
Pytest configuration and shared fixtures for mail service tests.
"""
import pytest
import requests
import time


BASE_URL = "http://localhost:8080"


@pytest.fixture(scope="session", autouse=True)
def check_service_running():
    """
    Check if the mail service is running before running tests.
    This fixture runs once per test session.
    """
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code not in [200, 404]:
            pytest.exit("Mail service is not responding correctly. Please start the service.")
    except requests.exceptions.RequestException:
        pytest.exit(
            "Mail service is not running. Please start the service on port 8080 before running tests."
        )


@pytest.fixture
def send_test_email():
    """
    Fixture to send a test email and return its mail_id.
    Useful for tests that need to query status or history.
    """
    def _send(to=None, subject=None, body=None, **kwargs):
        payload = {
            "to": to or ["test@example.com"],
            "subject": subject or "Test Email",
            "body": body or "Test body"
        }
        payload.update(kwargs)
        
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", json=payload)
        if response.status_code == 200:
            return response.json()["mail_id"]
        return None
    
    return _send


@pytest.fixture
def wait_for_email_processing():
    """
    Fixture to wait for email processing.
    Some tests may need to wait for emails to be processed.
    """
    def _wait(seconds=1):
        time.sleep(seconds)
    
    return _wait

