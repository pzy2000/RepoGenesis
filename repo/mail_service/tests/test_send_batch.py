"""
Test cases for batch email sending endpoint.
"""
import pytest
import requests
from datetime import datetime


BASE_URL = "http://localhost:8080"
SEND_BATCH_URL = f"{BASE_URL}/api/v1/mail/send-batch"


class TestSendBatchEmails:
    """Test cases for POST /api/v1/mail/send-batch endpoint."""
    
    def test_send_batch_success(self):
        """Test successfully sending a batch of emails."""
        payload = {
            "emails": [
                {
                    "to": ["user1@example.com"],
                    "subject": "Email 1",
                    "body": "Body 1"
                },
                {
                    "to": ["user2@example.com"],
                    "subject": "Email 2",
                    "body": "Body 2"
                },
                {
                    "to": ["user3@example.com"],
                    "subject": "Email 3",
                    "body": "Body 3"
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert data["total"] == 3
        assert "queued" in data
        assert "failed" in data
        assert data["queued"] + data["failed"] == 3
        assert "results" in data
        assert len(data["results"]) == 3
        assert "timestamp" in data
        
        # Verify each result has required fields
        for result in data["results"]:
            assert "mail_id" in result
            assert "status" in result
            assert "message" in result
    
    def test_send_batch_single_email(self):
        """Test sending batch with single email."""
        payload = {
            "emails": [
                {
                    "to": ["user@example.com"],
                    "subject": "Single Email Batch",
                    "body": "Test body"
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
    
    def test_send_batch_with_optional_fields(self):
        """Test sending batch with optional fields."""
        payload = {
            "emails": [
                {
                    "to": ["user1@example.com"],
                    "subject": "Email 1",
                    "body": "Body 1",
                    "from": "sender@example.com",
                    "cc": ["cc@example.com"],
                    "priority": "high"
                },
                {
                    "to": ["user2@example.com"],
                    "subject": "Email 2",
                    "body": "Body 2",
                    "bcc": ["bcc@example.com"],
                    "priority": "low"
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
    
    def test_send_batch_maximum_size(self):
        """Test sending batch with maximum allowed size (100 emails)."""
        emails = []
        for i in range(100):
            emails.append({
                "to": [f"user{i}@example.com"],
                "subject": f"Email {i}",
                "body": f"Body {i}"
            })
        
        payload = {"emails": emails}
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert len(data["results"]) == 100
    
    def test_send_batch_exceeds_maximum_size(self):
        """Test sending batch exceeding maximum size returns 400."""
        emails = []
        for i in range(101):
            emails.append({
                "to": [f"user{i}@example.com"],
                "subject": f"Email {i}",
                "body": f"Body {i}"
            })
        
        payload = {"emails": emails}
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "BATCH_TOO_LARGE"
    
    def test_send_batch_empty_list(self):
        """Test sending empty batch list returns 400."""
        payload = {"emails": []}
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_send_batch_missing_emails_field(self):
        """Test sending batch without emails field returns 400."""
        payload = {}
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "MISSING_FIELD"
    
    def test_send_batch_partial_failure(self):
        """Test batch with some invalid emails, check partial success."""
        payload = {
            "emails": [
                {
                    "to": ["valid@example.com"],
                    "subject": "Valid Email",
                    "body": "Valid body"
                },
                {
                    "to": ["invalid-email"],
                    "subject": "Invalid Email",
                    "body": "Invalid body"
                },
                {
                    "to": ["valid2@example.com"],
                    "subject": "Valid Email 2",
                    "body": "Valid body 2"
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["failed"] >= 1  # At least one should fail
        assert data["queued"] >= 2  # At least two should succeed
        
        # Check that results reflect individual statuses
        failed_count = sum(1 for r in data["results"] if r["status"] == "failed")
        assert failed_count >= 1
    
    def test_send_batch_email_missing_required_field(self):
        """Test batch where an email is missing required field."""
        payload = {
            "emails": [
                {
                    "to": ["user1@example.com"],
                    "subject": "Email 1",
                    "body": "Body 1"
                },
                {
                    "to": ["user2@example.com"],
                    "body": "Body 2"  # Missing subject
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["failed"] >= 1
        
        # Check that at least one result indicates failure
        failed_results = [r for r in data["results"] if r["status"] == "failed"]
        assert len(failed_results) >= 1
    
    def test_send_batch_all_invalid(self):
        """Test batch where all emails are invalid."""
        payload = {
            "emails": [
                {
                    "to": ["invalid1"],
                    "subject": "Email 1",
                    "body": "Body 1"
                },
                {
                    "to": ["invalid2"],
                    "subject": "Email 2",
                    "body": "Body 2"
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["failed"] == 2
        assert data["queued"] == 0
    
    def test_send_batch_mixed_priorities(self):
        """Test batch with emails of different priorities."""
        payload = {
            "emails": [
                {
                    "to": ["user1@example.com"],
                    "subject": "High Priority",
                    "body": "Body",
                    "priority": "high"
                },
                {
                    "to": ["user2@example.com"],
                    "subject": "Normal Priority",
                    "body": "Body",
                    "priority": "normal"
                },
                {
                    "to": ["user3@example.com"],
                    "subject": "Low Priority",
                    "body": "Body",
                    "priority": "low"
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
    
    def test_send_batch_duplicate_recipients(self):
        """Test batch sending same email to same recipient multiple times."""
        payload = {
            "emails": [
                {
                    "to": ["same@example.com"],
                    "subject": "Email 1",
                    "body": "Body 1"
                },
                {
                    "to": ["same@example.com"],
                    "subject": "Email 2",
                    "body": "Body 2"
                }
            ]
        }
        
        response = requests.post(SEND_BATCH_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        # Both should succeed as they are separate emails
        assert len(data["results"]) == 2

