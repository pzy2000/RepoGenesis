"""
Pytest configuration and fixtures for Task Management API tests.

This module provides common fixtures and configuration for all test modules.
"""

import pytest
import requests
import time
import subprocess
import os
import signal
from typing import Generator


@pytest.fixture(scope="session")
def api_server():
    """
    Fixture to start and stop the API server for testing.
    
    This fixture ensures the API server is running during test execution
    and properly shuts it down after all tests are complete.
    """
    # Check if server is already running
    try:
        response = requests.get("http://localhost:8080/api/v1/health", timeout=5)
        if response.status_code == 200:
            yield "http://localhost:8080"
            return
    except requests.exceptions.RequestException:
        pass
    
    # Server not running, need to start it
    # Note: This is a placeholder - actual implementation would depend on
    # the specific framework and deployment method used
    print("API server not running. Please start the server manually on port 8080")
    print("Example commands:")
    print("  - For Flask: python app.py")
    print("  - For FastAPI: uvicorn main:app --port 8080")
    print("  - For Django: python manage.py runserver 8080")
    
    # For now, just yield the expected URL
    # In a real implementation, you would start the server process here
    yield "http://localhost:8080"


@pytest.fixture(autouse=True)
def wait_for_server(api_server):
    """
    Fixture to wait for the API server to be ready before running tests.
    """
    max_retries = 30
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{api_server}/api/v1/health", timeout=5)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    pytest.skip("API server not available after waiting")


@pytest.fixture
def sample_task_data():
    """
    Fixture providing sample task data for testing.
    """
    return {
        "title": "Sample Task",
        "description": "This is a sample task for testing",
        "priority": "medium",
        "due_date": "2024-12-31T23:59:59Z"
    }


@pytest.fixture
def sample_tasks_data():
    """
    Fixture providing multiple sample tasks for testing.
    """
    return [
        {
            "title": "High Priority Task",
            "description": "This is a high priority task",
            "priority": "high",
            "due_date": "2024-12-25T12:00:00Z"
        },
        {
            "title": "Medium Priority Task",
            "description": "This is a medium priority task",
            "priority": "medium",
            "due_date": "2024-12-30T18:00:00Z"
        },
        {
            "title": "Low Priority Task",
            "description": "This is a low priority task",
            "priority": "low",
            "due_date": "2025-01-05T09:00:00Z"
        }
    ]


@pytest.fixture
def created_task(api_server, sample_task_data):
    """
    Fixture that creates a task and returns its data.
    The task is automatically cleaned up after the test.
    """
    response = requests.post(
        f"{api_server}/api/v1/tasks",
        json=sample_task_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 201:
        pytest.skip("Failed to create test task")
    
    task_data = response.json()
    task_id = task_data['id']
    
    yield task_data
    
    # Cleanup: delete the created task
    try:
        requests.delete(f"{api_server}/api/v1/tasks/{task_id}")
    except requests.exceptions.RequestException:
        pass  # Ignore cleanup errors


@pytest.fixture
def created_tasks(api_server, sample_tasks_data):
    """
    Fixture that creates multiple tasks and returns their data.
    The tasks are automatically cleaned up after the test.
    """
    created_tasks = []
    
    for task_data in sample_tasks_data:
        response = requests.post(
            f"{api_server}/api/v1/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            created_tasks.append(response.json())
    
    yield created_tasks
    
    # Cleanup: delete all created tasks
    for task in created_tasks:
        try:
            requests.delete(f"{api_server}/api/v1/tasks/{task['id']}")
        except requests.exceptions.RequestException:
            pass  # Ignore cleanup errors


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom settings.
    """
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test names.
    """
    for item in items:
        # Mark API tests
        if "test_task_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        
        # Mark integration tests
        if "workflow" in item.name or "integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if "pagination" in item.name or "workflow" in item.name:
            item.add_marker(pytest.mark.slow)


# Custom test data generators
class TaskDataGenerator:
    """Utility class for generating test task data"""
    
    @staticmethod
    def generate_valid_task(**overrides):
        """Generate a valid task with optional overrides"""
        default_task = {
            "title": "Generated Task",
            "description": "This is a generated task for testing",
            "priority": "medium",
            "due_date": "2024-12-31T23:59:59Z"
        }
        default_task.update(overrides)
        return default_task
    
    @staticmethod
    def generate_invalid_task():
        """Generate an invalid task for testing error handling"""
        return {
            "title": "",  # Empty title
            "priority": "invalid_priority",  # Invalid priority
            "description": "x" * 1001  # Description too long
        }
    
    @staticmethod
    def generate_tasks_batch(count=10):
        """Generate a batch of tasks for testing"""
        tasks = []
        for i in range(count):
            task = TaskDataGenerator.generate_valid_task(
                title=f"Batch Task {i+1}",
                priority=["low", "medium", "high"][i % 3]
            )
            tasks.append(task)
        return tasks


@pytest.fixture
def task_generator():
    """Fixture providing TaskDataGenerator instance"""
    return TaskDataGenerator
