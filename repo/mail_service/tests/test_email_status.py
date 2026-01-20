"""
Test cases for email status query endpoint.
"""
import pytest
import requests
from datetime import datetime


BASE_URL = "http://localhost:8080"
SEND_EMAIL_URL = f"{BASE_URL}/api/v1/mail/send"
STATUS_URL = f"{BASE_URL}/api/v1/mail/status"


class TestEmailStatus:
    """Test cases for GET /api/v1/mail/status/{mail_id} endpoint."""
    
    def test_get_status_success(self):
        """Test successfully retrieving status of sent email."""
        # First send an email to get a mail_id
        send_payload = {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": "Test body"
        }
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        assert send_response.status_code == 200
        mail_id = send_response.json()["mail_id"]
        
        # Now query the status
        response = requests.get(f"{STATUS_URL}/{mail_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mail_id"] == mail_id
        assert "status" in data
        assert data["status"] in ["pending", "sent", "failed", "delivered", "bounced"]
        assert "to" in data
        assert "subject" in data
        assert "sent_at" in data
        assert "delivered_at" in data
        assert "error" in data
        
        # Verify timestamp format
        if data["sent_at"]:
            datetime.fromisoformat(data["sent_at"].replace('Z', '+00:00'))
    
    def test_get_status_nonexistent_mail_id(self):
        """Test retrieving status with non-existent mail_id returns 404."""
        fake_mail_id = "nonexistent-mail-id-12345"
        
        response = requests.get(f"{STATUS_URL}/{fake_mail_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_get_status_invalid_mail_id_format(self):
        """Test retrieving status with invalid mail_id format."""
        invalid_mail_id = "invalid@#$%"
        
        response = requests.get(f"{STATUS_URL}/{invalid_mail_id}")
        
        # Could be 400 or 404 depending on implementation
        assert response.status_code in [400, 404]
        data = response.json()
        assert "error" in data
    
    def test_get_status_empty_mail_id(self):
        """Test retrieving status with empty mail_id."""
        response = requests.get(f"{STATUS_URL}/")
        
        # Should return 404 or 400 as endpoint requires mail_id
        assert response.status_code in [400, 404, 405]
    
    def test_get_status_pending_email(self):
        """Test status of newly sent email should be pending or sent."""
        send_payload = {
            "to": ["user@example.com"],
            "subject": "Pending Test",
            "body": "Test body"
        }
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()["mail_id"]
        
        response = requests.get(f"{STATUS_URL}/{mail_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["pending", "sent"]
    
    def test_get_status_fields_presence(self):
        """Test that all required fields are present in status response."""
        send_payload = {
            "to": ["user@example.com"],
            "subject": "Field Test",
            "body": "Test body"
        }
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()["mail_id"]
        
        response = requests.get(f"{STATUS_URL}/{mail_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        required_fields = ["mail_id", "status", "to", "subject", "sent_at", "delivered_at", "error"]
        for field in required_fields:
            assert field in data
    
    def test_get_status_to_field_format(self):
        """Test that 'to' field is returned as a list."""
        send_payload = {
            "to": ["user1@example.com", "user2@example.com"],
            "subject": "Multi-recipient Test",
            "body": "Test body"
        }
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()["mail_id"]
        
        response = requests.get(f"{STATUS_URL}/{mail_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["to"], list)
        assert len(data["to"]) == 2
    
    def test_get_status_error_field_null_on_success(self):
        """Test that error field is null when email is successful."""
        send_payload = {
            "to": ["user@example.com"],
            "subject": "Success Test",
            "body": "Test body"
        }
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()["mail_id"]
        
        response = requests.get(f"{STATUS_URL}/{mail_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Error should be null if status is not failed
        if data["status"] not in ["failed", "bounced"]:
            assert data["error"] is None or data["error"] == ""
    
    def test_get_status_multiple_queries_same_email(self):
        """Test querying same email status multiple times."""
        send_payload = {
            "to": ["user@example.com"],
            "subject": "Multiple Query Test",
            "body": "Test body"
        }
        send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
        mail_id = send_response.json()["mail_id"]
        
        # Query multiple times
        for _ in range(3):
            response = requests.get(f"{STATUS_URL}/{mail_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["mail_id"] == mail_id
    
    def test_get_status_different_emails(self):
        """Test querying status of different emails."""
        mail_ids = []
        
        # Send multiple emails
        for i in range(3):
            send_payload = {
                "to": [f"user{i}@example.com"],
                "subject": f"Email {i}",
                "body": f"Body {i}"
            }
            send_response = requests.post(SEND_EMAIL_URL, json=send_payload)
            mail_ids.append(send_response.json()["mail_id"])
        
        # Query each email's status
        for i, mail_id in enumerate(mail_ids):
            response = requests.get(f"{STATUS_URL}/{mail_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["mail_id"] == mail_id
            assert data["subject"] == f"Email {i}"

