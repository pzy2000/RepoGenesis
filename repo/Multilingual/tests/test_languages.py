"""
Test cases for the /api/languages endpoint
Tests supported languages query functionality
"""

import requests
import time

BASE_URL = "http://localhost:5000"
LANGUAGES_ENDPOINT = f"{BASE_URL}/api/languages"


def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    for _ in range(max_retries):
        try:
            response = requests.get(LANGUAGES_ENDPOINT, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(delay)
    return False


def test_languages_get_request():
    """Test GET request to languages endpoint"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Request should succeed"
    assert "languages" in data, "Languages should be present in response"
    print(f"✓ Test passed: GET request to languages endpoint")


def test_languages_contains_common_languages():
    """Test that response contains common languages"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    languages = data["languages"]
    
    assert isinstance(languages, dict), "Languages should be a dictionary"
    assert len(languages) > 0, "Languages dictionary should not be empty"
    
    # Check for some common languages
    common_lang_codes = ["en", "zh-cn", "es", "fr", "de"]
    found_languages = [lang for lang in common_lang_codes if lang in languages]
    
    assert len(found_languages) >= 3, f"Should contain at least 3 common languages, found: {found_languages}"
    print(f"✓ Test passed: Contains common languages ({len(found_languages)} found)")


def test_languages_format():
    """Test that languages response has correct format"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    languages = data["languages"]
    
    # Check format: each entry should be language_code: language_name
    for code, name in languages.items():
        assert isinstance(code, str), f"Language code should be string, got {type(code)}"
        assert isinstance(name, str), f"Language name should be string, got {type(name)}"
        assert len(code) > 0, "Language code should not be empty"
        assert len(name) > 0, "Language name should not be empty"
    
    print(f"✓ Test passed: Languages format is correct")


def test_languages_response_structure():
    """Test the overall response structure"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    
    # Check required fields
    assert "success" in data, "Response should contain 'success' field"
    assert "languages" in data, "Response should contain 'languages' field"
    
    # Check types
    assert isinstance(data["success"], bool), "'success' should be boolean"
    assert isinstance(data["languages"], dict), "'languages' should be a dictionary"
    
    print(f"✓ Test passed: Response structure is correct")


def test_languages_consistency():
    """Test that multiple requests return consistent results"""
    response1 = requests.get(LANGUAGES_ENDPOINT)
    response2 = requests.get(LANGUAGES_ENDPOINT)
    
    assert response1.status_code == 200, "First request should succeed"
    assert response2.status_code == 200, "Second request should succeed"
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Check that both responses have the same structure
    assert data1["success"] == data2["success"], "Success status should be consistent"
    assert len(data1["languages"]) == len(data2["languages"]), "Number of languages should be consistent"
    
    print(f"✓ Test passed: Responses are consistent")


def test_languages_english_present():
    """Test that English is always present in supported languages"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    languages = data["languages"]
    
    # English should be present (either as 'en' or 'english')
    has_english = any(code.lower() in ['en', 'english'] for code in languages.keys())
    assert has_english, "English should be in supported languages"
    
    print(f"✓ Test passed: English is present in supported languages")


def test_languages_count():
    """Test that a reasonable number of languages are supported"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    languages = data["languages"]
    
    lang_count = len(languages)
    assert lang_count >= 5, f"Should support at least 5 languages, got {lang_count}"
    assert lang_count <= 200, f"Language count seems unreasonable: {lang_count}"
    
    print(f"✓ Test passed: Reasonable number of languages ({lang_count})")


def test_languages_no_empty_values():
    """Test that there are no empty language codes or names"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    languages = data["languages"]
    
    for code, name in languages.items():
        assert code.strip() != "", f"Language code should not be empty"
        assert name.strip() != "", f"Language name should not be empty for code '{code}'"
    
    print(f"✓ Test passed: No empty language codes or names")


def test_languages_json_serializable():
    """Test that response is valid JSON"""
    response = requests.get(LANGUAGES_ENDPOINT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # If we got here, JSON parsing already succeeded
    data = response.json()
    
    # Try to serialize it back
    import json
    try:
        json_str = json.dumps(data)
        assert len(json_str) > 0, "JSON serialization should produce non-empty string"
    except Exception as e:
        assert False, f"Failed to serialize response to JSON: {e}"
    
    print(f"✓ Test passed: Response is valid JSON")


if __name__ == "__main__":
    print("Starting languages API tests...")
    print(f"Testing endpoint: {LANGUAGES_ENDPOINT}")
    print("=" * 60)
    
    # Wait for service to be ready
    if not wait_for_service():
        print("✗ Service is not available. Please start the server first.")
        exit(1)
    
    tests = [
        test_languages_get_request,
        test_languages_contains_common_languages,
        test_languages_format,
        test_languages_response_structure,
        test_languages_consistency,
        test_languages_english_present,
        test_languages_count,
        test_languages_no_empty_values,
        test_languages_json_serializable
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

