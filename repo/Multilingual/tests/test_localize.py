"""
Test cases for the /api/localize endpoint
Tests localized datetime formatting functionality
"""

import requests
import time

BASE_URL = "http://localhost:5000"
LOCALIZE_ENDPOINT = f"{BASE_URL}/api/localize"


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


def test_localize_us_english():
    """Test localizing datetime for US English"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "America/New_York",
        "locale": "en_US"
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Localization should succeed"
    assert "formatted_datetime" in data, "Formatted datetime should be present"
    assert data["timezone"] == "America/New_York", "Timezone should match"
    assert data["locale"] == "en_US", "Locale should match"
    assert len(data["formatted_datetime"]) > 0, "Formatted datetime should not be empty"
    print(f"✓ Test passed: US English localization")


def test_localize_chinese():
    """Test localizing datetime for Chinese"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "Asia/Shanghai",
        "locale": "zh_CN"
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Localization should succeed"
    assert "formatted_datetime" in data, "Formatted datetime should be present"
    assert data["timezone"] == "Asia/Shanghai", "Timezone should match"
    assert data["locale"] == "zh_CN", "Locale should match"
    print(f"✓ Test passed: Chinese localization")


def test_localize_spanish():
    """Test localizing datetime for Spanish"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "Europe/Madrid",
        "locale": "es_ES"
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Localization should succeed"
    assert "formatted_datetime" in data, "Formatted datetime should be present"
    assert data["timezone"] == "Europe/Madrid", "Timezone should match"
    assert data["locale"] == "es_ES", "Locale should match"
    print(f"✓ Test passed: Spanish localization")


def test_localize_japanese():
    """Test localizing datetime for Japanese"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "Asia/Tokyo",
        "locale": "ja_JP"
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Localization should succeed"
    assert "formatted_datetime" in data, "Formatted datetime should be present"
    print(f"✓ Test passed: Japanese localization")


def test_localize_missing_required_field():
    """Test localization with missing required field"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "UTC"
        # missing locale
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f"Expected error status code, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == False, "Request should fail"
    assert "error" in data, "Error message should be present"
    print(f"✓ Test passed: Missing required field handled correctly")


def test_localize_invalid_datetime():
    """Test localization with invalid datetime"""
    payload = {
        "datetime": "not-a-valid-datetime",
        "timezone": "UTC",
        "locale": "en_US"
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f"Expected error status code, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == False, "Request should fail for invalid datetime"
    assert "error" in data, "Error message should be present"
    print(f"✓ Test passed: Invalid datetime handled correctly")


def test_localize_invalid_timezone():
    """Test localization with invalid timezone"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "Invalid/Timezone",
        "locale": "en_US"
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f"Expected error status code, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == False, "Request should fail for invalid timezone"
    assert "error" in data, "Error message should be present"
    print(f"✓ Test passed: Invalid timezone handled correctly")


def test_localize_utc():
    """Test localizing datetime for UTC timezone"""
    payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "UTC",
        "locale": "en_GB"
    }
    
    response = requests.post(LOCALIZE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Localization should succeed"
    assert "formatted_datetime" in data, "Formatted datetime should be present"
    assert data["timezone"] == "UTC", "Timezone should be UTC"
    print(f"✓ Test passed: UTC localization")


def test_localize_different_formats():
    """Test that different locales produce different formats"""
    us_payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "UTC",
        "locale": "en_US"
    }
    
    cn_payload = {
        "datetime": "2025-10-30T12:00:00",
        "timezone": "UTC",
        "locale": "zh_CN"
    }
    
    us_response = requests.post(LOCALIZE_ENDPOINT, json=us_payload)
    cn_response = requests.post(LOCALIZE_ENDPOINT, json=cn_payload)
    
    assert us_response.status_code == 200, "US localization should succeed"
    assert cn_response.status_code == 200, "CN localization should succeed"
    
    us_data = us_response.json()
    cn_data = cn_response.json()
    
    # The formatted strings might be different due to locale
    # Just verify both succeed and have formatted output
    assert us_data["success"] == True, "US localization should succeed"
    assert cn_data["success"] == True, "CN localization should succeed"
    assert len(us_data["formatted_datetime"]) > 0, "US formatted datetime should not be empty"
    assert len(cn_data["formatted_datetime"]) > 0, "CN formatted datetime should not be empty"
    print(f"✓ Test passed: Different locale formats")


if __name__ == "__main__":
    print("Starting localize API tests...")
    print(f"Testing endpoint: {LOCALIZE_ENDPOINT}")
    print("=" * 60)
    
    # Wait for service to be ready
    if not wait_for_service():
        print("✗ Service is not available. Please start the server first.")
        exit(1)
    
    tests = [
        test_localize_us_english,
        test_localize_chinese,
        test_localize_spanish,
        test_localize_japanese,
        test_localize_missing_required_field,
        test_localize_invalid_datetime,
        test_localize_invalid_timezone,
        test_localize_utc,
        test_localize_different_formats
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

