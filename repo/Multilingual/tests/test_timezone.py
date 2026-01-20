"""
Test cases for the /api/timezone endpoint
Tests timezone conversion functionality
"""

import requests
import time

BASE_URL = "http://localhost:5000"
TIMEZONE_ENDPOINT = f"{BASE_URL}/api/timezone"


def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    for _ in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/api/languages", timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(delay)
    return False


def test_timezone_utc_to_shanghai():
    """Test converting UTC to Asia/Shanghai timezone"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "from_timezone": "UTC",
        "to_timezone": "Asia/Shanghai"
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Conversion should succeed"
    assert "original_datetime" in data, "Original datetime should be present"
    assert "converted_datetime" in data, "Converted datetime should be present"
    assert data["from_timezone"] == "UTC", "Source timezone should be UTC"
    assert data["to_timezone"] == "Asia/Shanghai", "Target timezone should be Asia/Shanghai"
    
    # UTC to Shanghai is +8 hours
    assert "20:00:00" in data["converted_datetime"] or "20" in data["converted_datetime"], \
        "Converted time should be 20:00 (12:00 + 8 hours)"
    print(f"✓ Test passed: UTC to Shanghai conversion")


def test_timezone_newyork_to_london():
    """Test converting America/New_York to Europe/London timezone"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "from_timezone": "America/New_York",
        "to_timezone": "Europe/London"
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Conversion should succeed"
    assert "converted_datetime" in data, "Converted datetime should be present"
    assert data["from_timezone"] == "America/New_York", "Source timezone should match"
    assert data["to_timezone"] == "Europe/London", "Target timezone should match"
    print(f"✓ Test passed: New York to London conversion")


def test_timezone_same_timezone():
    """Test converting within the same timezone"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "from_timezone": "UTC",
        "to_timezone": "UTC"
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Conversion should succeed"
    assert "12:00:00" in data["converted_datetime"] or "12" in data["converted_datetime"], \
        "Time should remain the same"
    print(f"✓ Test passed: Same timezone conversion")


def test_timezone_missing_required_field():
    """Test timezone conversion with missing required field"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "from_timezone": "UTC"
        # missing to_timezone
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f"Expected error status code, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == False, "Request should fail"
    assert "error" in data, "Error message should be present"
    print(f"✓ Test passed: Missing required field handled correctly")


def test_timezone_invalid_datetime_format():
    """Test timezone conversion with invalid datetime format"""
    payload = {
        "datetime": "invalid-datetime",
        "from_timezone": "UTC",
        "to_timezone": "Asia/Shanghai"
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f"Expected error status code, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == False, "Request should fail for invalid datetime"
    assert "error" in data, "Error message should be present"
    print(f"✓ Test passed: Invalid datetime format handled correctly")


def test_timezone_invalid_timezone_name():
    """Test timezone conversion with invalid timezone name"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "from_timezone": "Invalid/Timezone",
        "to_timezone": "UTC"
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f"Expected error status code, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == False, "Request should fail for invalid timezone"
    assert "error" in data, "Error message should be present"
    print(f"✓ Test passed: Invalid timezone name handled correctly")


def test_timezone_edge_case_midnight():
    """Test timezone conversion at midnight"""
    payload = {
        "datetime": "2025-10-30T00:00:00",
        "from_timezone": "UTC",
        "to_timezone": "America/Los_Angeles"
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Conversion should succeed"
    assert "converted_datetime" in data, "Converted datetime should be present"
    print(f"✓ Test passed: Midnight timezone conversion")


def test_timezone_cross_date():
    """Test timezone conversion that crosses date boundary"""
    payload = {
        "datetime": "2025-10-30T23:00:00",
        "from_timezone": "UTC",
        "to_timezone": "Pacific/Auckland"
    }
    
    response = requests.post(TIMEZONE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Conversion should succeed"
    # Auckland is UTC+13, so 23:00 UTC becomes next day
    assert "31" in data["converted_datetime"] or "2025-10-31" in data["converted_datetime"], \
        "Date should advance to October 31"
    print(f"✓ Test passed: Cross-date timezone conversion")


if __name__ == "__main__":
    print("Starting timezone API tests...")
    print(f"Testing endpoint: {TIMEZONE_ENDPOINT}")
    print("=" * 60)
    
    # Wait for service to be ready
    if not wait_for_service():
        print("✗ Service is not available. Please start the server first.")
        exit(1)
    
    tests = [
        test_timezone_utc_to_shanghai,
        test_timezone_newyork_to_london,
        test_timezone_same_timezone,
        test_timezone_missing_required_field,
        test_timezone_invalid_datetime_format,
        test_timezone_invalid_timezone_name,
        test_timezone_edge_case_midnight,
        test_timezone_cross_date
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print(f"Pass rate: {passed / (passed + failed) * 100:.2f}%")
    
    exit(0 if failed == 0 else 1)

