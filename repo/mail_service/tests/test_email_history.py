"""
Test cases for email history query endpoint.
"""
import pytest
import requests
from datetime import datetime, timedelta
import time


BASE_URL = "http://localhost:8080"
SEND_EMAIL_URL = f"{BASE_URL}/api/v1/mail/send"
HISTORY_URL = f"{BASE_URL}/api/v1/mail/history"


class TestEmailHistory:
    """Test cases for GET /api/v1/mail/history endpoint."""
    
    def test_get_history_success(self):
        """Test successfully retrieving email history."""
        response = requests.get(HISTORY_URL)
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "emails" in data
        assert isinstance(data["emails"], list)
    
    def test_get_history_with_limit(self):
        """Test retrieving history with limit parameter."""
        limit = 10
        response = requests.get(HISTORY_URL, params={"limit": limit})
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == limit
        assert len(data["emails"]) <= limit
    
    def test_get_history_with_offset(self):
        """Test retrieving history with offset parameter."""
        # First get the first page
        response1 = requests.get(HISTORY_URL, params={"limit": 5, "offset": 0})
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Then get the second page
        response2 = requests.get(HISTORY_URL, params={"limit": 5, "offset": 5})
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert data2["offset"] == 5
        
        # If there are enough emails, the results should be different
        if len(data1["emails"]) == 5 and len(data2["emails"]) > 0:
            assert data1["emails"][0]["mail_id"] != data2["emails"][0]["mail_id"]
    
    def test_get_history_default_limit(self):
        """Test that default limit is 50."""
        response = requests.get(HISTORY_URL)
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 50
        assert len(data["emails"]) <= 50
    
    def test_get_history_max_limit(self):
        """Test that maximum limit is 100."""
        response = requests.get(HISTORY_URL, params={"limit": 150})
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] <= 100
    
    def test_get_history_invalid_limit(self):
        """Test retrieving history with invalid limit returns 400."""
        response = requests.get(HISTORY_URL, params={"limit": -1})
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_get_history_invalid_offset(self):
        """Test retrieving history with invalid offset returns 400."""
        response = requests.get(HISTORY_URL, params={"offset": -1})
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_get_history_filter_by_status(self):
        """Test filtering history by status."""
        statuses = ["pending", "sent", "failed", "delivered", "bounced"]
        
        for status in statuses:
            response = requests.get(HISTORY_URL, params={"status": status})
            
            assert response.status_code == 200
            data = response.json()
            
            # All returned emails should have the requested status
            for email in data["emails"]:
                assert email["status"] == status
    
    def test_get_history_invalid_status(self):
        """Test filtering with invalid status returns 400."""
        response = requests.get(HISTORY_URL, params={"status": "invalid_status"})
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_get_history_filter_by_date_range(self):
        """Test filtering history by date range."""
        # Send a test email first
        send_payload = {
            "to": ["test@example.com"],
            "subject": "Date Range Test",
            "body": "Test body"
        }
        requests.post(SEND_EMAIL_URL, json=send_payload)
        
        # Query with date range
        to_date = datetime.utcnow().isoformat() + "Z"
        from_date = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
        
        response = requests.get(HISTORY_URL, params={
            "from_date": from_date,
            "to_date": to_date
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
    
    def test_get_history_invalid_date_format(self):
        """Test filtering with invalid date format returns 400."""
        response = requests.get(HISTORY_URL, params={"from_date": "invalid-date"})
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_get_history_from_date_after_to_date(self):
        """Test filtering with from_date after to_date returns 400."""
        to_date = (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
        from_date = datetime.utcnow().isoformat() + "Z"
        
        response = requests.get(HISTORY_URL, params={
            "from_date": from_date,
            "to_date": to_date
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_get_history_email_fields(self):
        """Test that each email in history has required fields."""
        # Send an email first to ensure there's at least one in history
        send_payload = {
            "to": ["test@example.com"],
            "subject": "Field Test",
            "body": "Test body"
        }
        requests.post(SEND_EMAIL_URL, json=send_payload)
        
        response = requests.get(HISTORY_URL, params={"limit": 1})
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["emails"]) > 0:
            email = data["emails"][0]
            required_fields = ["mail_id", "to", "subject", "status", "sent_at", "delivered_at"]
            for field in required_fields:
                assert field in email
    
    def test_get_history_empty_result(self):
        """Test that history with filters that match nothing returns empty list."""
        # Query with a future date range
        from_date = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
        to_date = (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z"
        
        response = requests.get(HISTORY_URL, params={
            "from_date": from_date,
            "to_date": to_date
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["emails"]) == 0
    
    def test_get_history_pagination(self):
        """Test pagination through email history."""
        # Get first page
        response1 = requests.get(HISTORY_URL, params={"limit": 10, "offset": 0})
        assert response1.status_code == 200
        data1 = response1.json()
        
        total = data1["total"]
        
        # Get second page if there are enough emails
        if total > 10:
            response2 = requests.get(HISTORY_URL, params={"limit": 10, "offset": 10})
            assert response2.status_code == 200
            data2 = response2.json()
            
            # Total should be the same
            assert data2["total"] == total
            
            # mail_ids should be different
            if len(data2["emails"]) > 0:
                ids1 = [e["mail_id"] for e in data1["emails"]]
                ids2 = [e["mail_id"] for e in data2["emails"]]
                assert len(set(ids1) & set(ids2)) == 0  # No overlap
    
    def test_get_history_combined_filters(self):
        """Test using multiple filters together."""
        params = {
            "limit": 20,
            "offset": 0,
            "status": "sent"
        }
        
        response = requests.get(HISTORY_URL, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 20
        assert data["offset"] == 0
        
        # All emails should have sent status
        for email in data["emails"]:
            assert email["status"] == "sent"
    
    def test_get_history_ordering(self):
        """Test that emails are ordered by sent_at timestamp (most recent first)."""
        response = requests.get(HISTORY_URL, params={"limit": 10})
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["emails"]) >= 2:
            # Check that timestamps are in descending order
            for i in range(len(data["emails"]) - 1):
                time1 = data["emails"][i]["sent_at"]
                time2 = data["emails"][i + 1]["sent_at"]
                
                if time1 and time2:
                    dt1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
                    dt2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
                    assert dt1 >= dt2

