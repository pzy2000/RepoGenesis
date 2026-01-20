"""
Edge Cases and Boundary Tests for Task Management API

This module contains tests for edge cases, boundary conditions, and error scenarios
that might not be covered in the main API test suite.
"""

import pytest
import requests
import json
from datetime import datetime, timedelta


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    
    BASE_URL = "http://localhost:8080/api/v1"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f"{self.BASE_URL}/tasks")
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    requests.delete(f"{self.BASE_URL}/tasks/{task['id']}")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")
    
    def test_task_title_boundary_values(self):
        """Test task title at boundary values"""
        # Test exactly 200 characters (maximum allowed)
        max_title = "x" * 200
        task_data = {"title": max_title, "priority": "high"}
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == max_title
        
        # Test 201 characters (should fail)
        too_long_title = "x" * 201
        task_data = {"title": too_long_title, "priority": "high"}
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
    
    def test_task_description_boundary_values(self):
        """Test task description at boundary values"""
        # Test exactly 1000 characters (maximum allowed)
        max_description = "x" * 1000
        task_data = {
            "title": "Test Task",
            "description": max_description,
            "priority": "high"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['description'] == max_description
        
        # Test 1001 characters (should fail)
        too_long_description = "x" * 1001
        task_data = {
            "title": "Test Task",
            "description": too_long_description,
            "priority": "high"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
    
    def test_unicode_characters_in_task(self):
        """Test handling of Unicode characters in task data"""
        unicode_task = {
            "title": "Test Mission 🚀",
            "description": "This is a task description containing Unicode characters: Chinese, emoji, special symbols @#$%",
            "priority": "high"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=unicode_task,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == unicode_task['title']
        assert data['description'] == unicode_task['description']
    
    def test_special_characters_in_task(self):
        """Test handling of special characters in task data"""
        special_chars_task = {
            "title": "Task with Special Chars: @#$%^&*()_+-=[]{}|;':\",./<>?",
            "description": "Description with newlines\nand tabs\tand quotes\"'",
            "priority": "medium"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=special_chars_task,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['title'] == special_chars_task['title']
        assert data['description'] == special_chars_task['description']
    
    def test_date_formats(self):
        """Test various date formats for due_date"""
        date_formats = [
            "2024-12-31T23:59:59Z",
            "2024-12-31T23:59:59.000Z",
            "2024-12-31T23:59:59+00:00",
            "2024-12-31T23:59:59-05:00",
            "2024-12-31"
        ]
        
        for date_format in date_formats:
            task_data = {
                "title": f"Task with date {date_format}",
                "priority": "high",
                "due_date": date_format
            }
            
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should either succeed or fail gracefully
            assert response.status_code in [201, 422]
            
            if response.status_code == 201:
                # Clean up successful task
                task_id = response.json()['id']
                requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
    
    def test_invalid_date_formats(self):
        """Test invalid date formats"""
        invalid_dates = [
            "not-a-date",
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "2024/12/31",  # Wrong separator
            "31-12-2024",  # Wrong order
            ""
        ]
        
        for invalid_date in invalid_dates:
            task_data = {
                "title": "Task with invalid date",
                "priority": "high",
                "due_date": invalid_date
            }
            
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 422
    
    def test_empty_strings(self):
        """Test handling of empty strings"""
        # Empty title should fail
        task_data = {"title": "", "priority": "high"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
        
        # Empty description should be allowed
        task_data = {
            "title": "Valid Task",
            "description": "",
            "priority": "high"
        }
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
    
    def test_whitespace_only_strings(self):
        """Test handling of whitespace-only strings"""
        # Whitespace-only title should fail
        task_data = {"title": "   ", "priority": "high"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
        
        # Whitespace-only description should be allowed or normalized
        task_data = {
            "title": "Valid Task",
            "description": "   ",
            "priority": "high"
        }
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 422]
    
    def test_null_values(self):
        """Test handling of null values"""
        task_data = {
            "title": "Valid Task",
            "description": None,
            "priority": "high",
            "due_date": None
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 422]
    
    def test_extra_fields(self):
        """Test handling of extra fields in request"""
        task_data = {
            "title": "Valid Task",
            "priority": "high",
            "extra_field": "should be ignored",
            "another_field": 123
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        # Extra fields should not be in response
        assert 'extra_field' not in data
        assert 'another_field' not in data
    
    def test_case_sensitivity(self):
        """Test case sensitivity of enum values"""
        # Test priority case sensitivity
        task_data = {"title": "Test Task", "priority": "HIGH"}
        response = requests.post(
            f"{self.BASE_URL}/tasks",
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        # Should either accept or reject consistently
        assert response.status_code in [201, 422]
        
        if response.status_code == 201:
            task_id = response.json()['id']
            requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
    
    def test_large_numbers(self):
        """Test handling of large numbers in pagination"""
        # Test very large page number
        response = requests.get(f"{self.BASE_URL}/tasks?page=999999")
        assert response.status_code in [200, 422]
        
        # Test very large limit
        response = requests.get(f"{self.BASE_URL}/tasks?limit=999999")
        assert response.status_code in [200, 422]
    
    def test_negative_numbers(self):
        """Test handling of negative numbers"""
        # Test negative page number
        response = requests.get(f"{self.BASE_URL}/tasks?page=-1")
        assert response.status_code in [200, 422]
        
        # Test negative limit
        response = requests.get(f"{self.BASE_URL}/tasks?limit=-1")
        assert response.status_code in [200, 422]
    
    def test_zero_values(self):
        """Test handling of zero values"""
        # Test zero page number
        response = requests.get(f"{self.BASE_URL}/tasks?page=0")
        assert response.status_code in [200, 422]
        
        # Test zero limit
        response = requests.get(f"{self.BASE_URL}/tasks?limit=0")
        assert response.status_code in [200, 422]
    
    def test_sql_injection_attempts(self):
        """Test protection against SQL injection attempts"""
        malicious_titles = [
            "'; DROP TABLE tasks; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM tasks; --"
        ]
        
        for malicious_title in malicious_titles:
            task_data = {"title": malicious_title, "priority": "high"}
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should either create the task with escaped content or reject it
            assert response.status_code in [201, 422]
            
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
    
    def test_xss_attempts(self):
        """Test protection against XSS attempts"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            task_data = {"title": payload, "priority": "high"}
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should either create the task with escaped content or reject it
            assert response.status_code in [201, 422]
            
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_task(thread_id):
            try:
                task_data = {
                    "title": f"Concurrent Task {thread_id}",
                    "priority": "medium"
                }
                response = requests.post(
                    f"{self.BASE_URL}/tasks",
                    json=task_data,
                    headers={'Content-Type': 'application/json'}
                )
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_task, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent requests: {errors}"
        assert len(results) == 5
        
        # All requests should succeed
        for thread_id, status_code in results:
            assert status_code == 201
        
        # Clean up created tasks
        response = requests.get(f"{self.BASE_URL}/tasks")
        if response.status_code == 200:
            tasks = response.json().get('tasks', [])
            for task in tasks:
                if task['title'].startswith('Concurrent Task'):
                    requests.delete(f"{self.BASE_URL}/tasks/{task['id']}")
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_jsons = [
            '{"title": "Test", "priority": "high"',  # Missing closing brace
            '{"title": "Test", "priority": "high",}',  # Trailing comma
            '{"title": "Test", "priority": high}',  # Unquoted string
            '{"title": "Test", "priority": "high" "extra": "value"}',  # Missing comma
            '{"title": "Test", "priority": "high", "status": }',  # Missing value
        ]
        
        for malformed_json in malformed_jsons:
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                data=malformed_json,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 400
    
    def test_content_type_variations(self):
        """Test handling of different content types"""
        task_data = {"title": "Test Task", "priority": "high"}
        
        content_types = [
            'application/json',
            'application/json; charset=utf-8',
            'application/json;charset=utf-8',
            'text/json',
            'text/plain'
        ]
        
        for content_type in content_types:
            response = requests.post(
                f"{self.BASE_URL}/tasks",
                json=task_data,
                headers={'Content-Type': content_type}
            )
            
            # Should either succeed or fail gracefully
            assert response.status_code in [201, 400, 415]
            
            if response.status_code == 201:
                task_id = response.json()['id']
                requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
    
    def test_missing_headers(self):
        """Test handling of missing headers"""
        task_data = {"title": "Test Task", "priority": "high"}
        
        # Test without Content-Type header
        response = requests.post(f"{self.BASE_URL}/tasks", json=task_data)
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 400, 415]
        
        if response.status_code == 201:
            task_id = response.json()['id']
            requests.delete(f"{self.BASE_URL}/tasks/{task_id}")
    
    def test_very_long_url(self):
        """Test handling of very long URLs"""
        # Create a very long query string
        long_params = "&".join([f"param{i}=value{i}" for i in range(100)])
        response = requests.get(f"{self.BASE_URL}/tasks?{long_params}")
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 414, 400]
