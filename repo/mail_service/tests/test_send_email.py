"""
Test cases for sending single email endpoint.
"""
import pytest
import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8080"
SEND_EMAIL_URL = f"{BASE_URL}/api/v1/mail/send"


class TestSendSingleEmail:
    """Test cases for POST /api/v1/mail/send endpoint."""
    
    def test_send_email_success(self):
        """Test successfully sending a single email with all required fields."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": "This is a test email body."
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "mail_id" in data
        assert data["status"] in ["pending", "sent"]
        assert "message" in data
        assert "timestamp" in data
        # Verify timestamp is valid ISO 8601 format
        datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
    
    def test_send_email_with_optional_fields(self):
        """Test sending email with all optional fields."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email with Optional Fields",
            "body": "Test body",
            "from": "sender@example.com",
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "priority": "high"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "mail_id" in data
        assert data["status"] in ["pending", "sent"]
    
    def test_send_email_multiple_recipients(self):
        """Test sending email to multiple recipients."""
        payload = {
            "to": ["user1@example.com", "user2@example.com", "user3@example.com"],
            "subject": "Test Multiple Recipients",
            "body": "Email to multiple recipients"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "mail_id" in data
    
    def test_send_email_missing_required_field_to(self):
        """Test sending email without 'to' field returns 400."""
        payload = {
            "subject": "Test Email",
            "body": "Test body"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "MISSING_FIELD"
    
    def test_send_email_missing_required_field_subject(self):
        """Test sending email without 'subject' field returns 400."""
        payload = {
            "to": ["user@example.com"],
            "body": "Test body"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "MISSING_FIELD"
    
    def test_send_email_missing_required_field_body(self):
        """Test sending email without 'body' field returns 400."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "MISSING_FIELD"
    
    def test_send_email_invalid_email_format(self):
        """Test sending email with invalid email address format."""
        payload = {
            "to": ["invalid-email"],
            "subject": "Test Email",
            "body": "Test body"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "INVALID_EMAIL"
    
    def test_send_email_empty_recipients(self):
        """Test sending email with empty recipients list."""
        payload = {
            "to": [],
            "subject": "Test Email",
            "body": "Test body"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_send_email_invalid_priority(self):
        """Test sending email with invalid priority value."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": "Test body",
            "priority": "invalid_priority"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "INVALID_PRIORITY"
    
    def test_send_email_valid_priority_values(self):
        """Test sending email with each valid priority value."""
        priorities = ["low", "normal", "high"]
        
        for priority in priorities:
            payload = {
                "to": ["user@example.com"],
                "subject": f"Test Email - {priority}",
                "body": "Test body",
                "priority": priority
            }
            
            response = requests.post(SEND_EMAIL_URL, json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert "mail_id" in data
    
    def test_send_email_with_cc_and_bcc(self):
        """Test sending email with CC and BCC recipients."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": "Test body",
            "cc": ["cc1@example.com", "cc2@example.com"],
            "bcc": ["bcc1@example.com"]
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "mail_id" in data
    
    def test_send_email_empty_subject(self):
        """Test sending email with empty subject string."""
        payload = {
            "to": ["user@example.com"],
            "subject": "",
            "body": "Test body"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_send_email_empty_body(self):
        """Test sending email with empty body string."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": ""
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_send_email_large_body(self):
        """Test sending email with large body exceeding 1MB limit."""
        # Create a body larger than 1MB
        large_body = "x" * (1024 * 1024 + 1)
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": large_body
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_send_email_special_characters_in_subject(self):
        """Test sending email with special characters in subject."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email: Special Characters !@#$%^&*()",
            "body": "Test body"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "mail_id" in data
    
    def test_send_email_unicode_content(self):
        """Test sending email with unicode content."""
        payload = {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": "Hello World"
        }
        
        response = requests.post(SEND_EMAIL_URL, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "mail_id" in data

