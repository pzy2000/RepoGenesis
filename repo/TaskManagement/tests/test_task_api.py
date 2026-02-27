"""
Task Management API Test Cases

This module contains comprehensive test cases for the Task Management Microservice API.
All tests follow the interface definitions specified in the README.md file.
"""

import pytest
import requests
import json
from datetime import datetime, timedelta


class TestTaskAPI:
    """Test suite for Task Management API endpoints"""
    
    BASE_URL = "http://localhost:8080/api/v1"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        # Clean up any existing tasks before each test
        try:
            response = requests.get(f"{self.BASE_URL}/tasks")
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    requests.delete(f"{self.BASE_URL}/tasks/{task['id']}")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert data['status'] == 'healthy'
    
    def test_create_task_success(self):
        """Test successful task creation"""
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "high",
            "due_date": "2024-12-31T23:59:59Z"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == task_data['title']
        assert data['description'] == task_data['description']
        assert data['priority'] == task_data['priority']
        assert data['status'] == 'pending'  # Default status
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_create_task_minimal_data(self):
        """Test task creation with minimal required data"""
        task_data = {
            "title": "Minimal Task",
            "priority": "medium"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == task_data['title']
        assert data['priority'] == task_data['priority']
        assert data['status'] == 'pending'
        assert data['description'] is None or data['description'] == ""
    
    def test_create_task_invalid_priority(self):
        """Test task creation with invalid priority"""
        task_data = {
            "title": "Test Task",
            "priority": "invalid_priority"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'validation_error'
    
    def test_create_task_missing_required_fields(self):
        """Test task creation with missing required fields"""
        task_data = {
            "description": "Missing title and priority"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_create_task_title_too_long(self):
        """Test task creation with title exceeding maximum length"""
        task_data = {
            "title": "x" * 201,  # Exceeds 200 character limit
            "priority": "high"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_get_tasks_list_empty(self):
        """Test getting tasks list when no tasks exist"""
        response = requests.get(f"{self.BASE_URL}/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert 'tasks' in data
        assert 'pagination' in data
        assert len(data['tasks']) == 0
        assert data['pagination']['total'] == 0
    
    def test_get_tasks_list_with_data(self):
        """Test getting tasks list with existing tasks"""
        # Create test tasks
        tasks_data = [
            {"title": "Task 1", "priority": "high"},
            {"title": "Task 2", "priority": "medium"},
            {"title": "Task 3", "priority": "low"}
        ]
        
        created_tasks = []
        for task_data in tasks_data:
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
            assert response.status_code == 201
            created_tasks.append(response.json())
        
        # Get tasks list
        response = requests.get(f"{self.BASE_URL}/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 3
        assert data['pagination']['total'] == 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 10
    
    def test_get_tasks_list_pagination(self):
        """Test tasks list pagination"""
        # Create 15 test tasks
        for i in range(15):
            task_data = {"title": f"Task {i+1}", "priority": "medium"}
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
            assert response.status_code == 201
        
        # Test first page
        response = requests.get(f"{self.BASE_URL}/tasks?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] == 15
        assert data['pagination']['pages'] == 2
        
        # Test second page
        response = requests.get(f"{self.BASE_URL}/tasks?page=2&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 5
        assert data['pagination']['page'] == 2
    
    def test_get_tasks_list_filter_by_status(self):
        """Test filtering tasks by status"""
        # Create tasks with different statuses
        task_data = {"title": "Test Task", "priority": "high"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        task_id = response.json()['id']
        
        # Update task status
        requests.put(
            f"{self.BASE_URL}/tasks/{task_id}",
            json={"status": "completed"},
            headers={'Content-Type': 'application/json'}
        )
        
        # Filter by completed status
        response = requests.get(f"{self.BASE_URL}/tasks?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['status'] == 'completed'
    
    def test_get_tasks_list_filter_by_priority(self):
        """Test filtering tasks by priority"""
        # Create tasks with different priorities
        priorities = ["high", "medium", "low"]
        for priority in priorities:
            task_data = {"title": f"Task {priority}", "priority": priority}
            requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
        
        # Filter by high priority
        response = requests.get(f"{self.BASE_URL}/tasks?priority=high")
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['priority'] == 'high'
    
    def test_get_single_task_success(self):
        """Test getting a single task by ID"""
        # Create a task
        task_data = {"title": "Single Task", "priority": "high"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        created_task = response.json()
        
        # Get the task by ID
        response = requests.get(f"{self.BASE_URL}/tasks/{created_task['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == created_task['id']
        assert data['title'] == created_task['title']
        assert data['priority'] == created_task['priority']
    
    def test_get_single_task_not_found(self):
        """Test getting a non-existent task"""
        response = requests.get(f"{self.BASE_URL}/tasks/99999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'
    
    def test_update_task_success(self):
        """Test successful task update"""
        # Create a task
        task_data = {"title": "Original Task", "priority": "low"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        task_id = response.json()['id']
        
        # Update the task
        update_data = {
            "title": "Updated Task",
            "description": "Updated description",
            "priority": "high",
            "status": "in_progress"
        }
        response = requests.put(
            f"{self.BASE_URL}/tasks/{task_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == update_data['title']
        assert data['description'] == update_data['description']
        assert data['priority'] == update_data['priority']
        assert data['status'] == update_data['status']
        assert data['id'] == task_id
    
    def test_update_task_partial(self):
        """Test partial task update"""
        # Create a task
        task_data = {
            "title": "Original Task",
            "description": "Original description",
            "priority": "low"
        }
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        task_id = response.json()['id']
        
        # Update only title
        update_data = {"title": "Updated Title Only"}
        response = requests.put(
            f"{self.BASE_URL}/tasks/{task_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == update_data['title']
        assert data['description'] == task_data['description']  # Should remain unchanged
        assert data['priority'] == task_data['priority']  # Should remain unchanged
    
    def test_update_task_invalid_status(self):
        """Test task update with invalid status"""
        # Create a task
        task_data = {"title": "Test Task", "priority": "high"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        task_id = response.json()['id']
        
        # Update with invalid status
        update_data = {"status": "invalid_status"}
        response = requests.put(
            f"{self.BASE_URL}/tasks/{task_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data
    
    def test_update_task_not_found(self):
        """Test updating a non-existent task"""
        update_data = {"title": "Updated Task"}
        response = requests.put(
            f"{self.BASE_URL}/tasks/99999",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'
    
    def test_delete_task_success(self):
        """Test successful task deletion"""
        # Create a task
        task_data = {"title": "Task to Delete", "priority": "medium"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        task_id = response.json()['id']
        
        # Delete the task
        response = requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        
        # Verify task is deleted
        response = requests.get(f"{self.BASE_URL}/tasks/{task_id}")
        assert response.status_code == 404
    
    def test_delete_task_not_found(self):
        """Test deleting a non-existent task"""
        response = requests.delete(f"{self.BASE_URL}/tasks/99999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data
        assert error_data['error']['code'] == 'not_found'
    
    def test_task_workflow_complete(self):
        """Test complete task workflow: create -> update -> complete -> delete"""
        # Create task
        task_data = {
            "title": "Workflow Task",
            "description": "Complete workflow test",
            "priority": "high",
            "due_date": "2024-12-31T23:59:59Z"
        }
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        task_id = response.json()['id']
        
        # Update to in_progress
        response = requests.put(
            f"{self.BASE_URL}/tasks/{task_id}",
            json={"status": "in_progress"},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'in_progress'
        
        # Complete the task
        response = requests.put(
            f"{self.BASE_URL}/tasks/{task_id}",
            json={"status": "completed"},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'completed'
        
        # Verify in completed tasks list
        response = requests.get(f"{self.BASE_URL}/tasks?status=completed")
        assert response.status_code == 200
        completed_tasks = response.json()['tasks']
        assert len(completed_tasks) == 1
        assert completed_tasks[0]['id'] == task_id
        
        # Delete the task
        response = requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
        assert response.status_code == 200
        
        # Verify deletion
        response = requests.get(f"{self.BASE_URL}/tasks/{task_id}")
        assert response.status_code == 404
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request body"""
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            data="invalid json",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data
    
    def test_missing_content_type_header(self):
        """Test handling of missing Content-Type header"""
        task_data = {"title": "Test Task", "priority": "high"}
        response = requests.post(f"{self.BASE_URL}/tasks", json=task_data)
        
        # Should still work as requests library sets Content-Type automatically
        assert response.status_code in [201, 400]  # Depends on implementation
    
    def test_large_pagination_limit(self):
        """Test pagination with limit exceeding maximum"""
        response = requests.get(f"{self.BASE_URL}/tasks?limit=1000")
        
        # Should either return max allowed limit or error
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100  # Should be capped at max
