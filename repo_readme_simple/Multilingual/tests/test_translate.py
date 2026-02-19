"""
Test cases for the /api/translate endpoint
Tests translation functionality between different languages
"""

import requests
import time

BASE_URL = "http://localhost:5000"
TRANSLATE_ENDPOINT = f"{BASE_URL}/api/translate"


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


def test_translate_english_to_chinese():
    """Test translating English text to Chinese"""
    payload = {
        "text": "Hello",
        "source_lang": "en",
        "target_lang": "zh-cn"
    }
    
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Translation should succeed"
    assert data["original_text"] == "Hello", "Original text should match"
    assert data["source_lang"] == "en", "Source language should be 'en'"
    assert data["target_lang"] == "zh-cn", "Target language should be 'zh-cn'"
    assert len(data["translated_text"]) > 0, "Translated text should not be empty"
    print(f"✓ Test passed: English to Chinese translation")


def test_translate_chinese_to_english():
    """Test translating Chinese text to English"""
    payload = {
        "text": "你好",
        "source_lang": "zh-cn",
        "target_lang": "en"
    }
    
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Translation should succeed"
    assert data["original_text"] == "你好", "Original text should match"
    assert data["source_lang"] == "zh-cn", "Source language should be 'zh-cn'"
    assert data["target_lang"] == "en", "Target language should be 'en'"
    assert len(data["translated_text"]) > 0, "Translated text should not be empty"
    print(f"✓ Test passed: Chinese to English translation")


def test_translate_spanish_to_english():
    """Test translating Spanish text to English"""
    payload = {
        "text": "Hola",
        "source_lang": "es",
        "target_lang": "en"
    }
    
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Translation should succeed"
    assert data["original_text"] == "Hola", "Original text should match"
    assert len(data["translated_text"]) > 0, "Translated text should not be empty"
    print(f"✓ Test passed: Spanish to English translation")


def test_translate_missing_required_field():
    """Test translation with missing required field"""
    payload = {
        "text": "Hello",
        "source_lang": "en"
        # missing target_lang
    }
    
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code in [400, 500], f"Expected error status code, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == False, "Request should fail"
    assert "error" in data, "Error message should be present"
    print(f"✓ Test passed: Missing required field handled correctly")


def test_translate_empty_text():
    """Test translation with empty text"""
    payload = {
        "text": "",
        "source_lang": "en",
        "target_lang": "zh-cn"
    }
    
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    # Should either succeed with empty result or fail gracefully
    assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"
    
    data = response.json()
    if response.status_code == 400:
        assert data["success"] == False, "Request should fail for empty text"
    print(f"✓ Test passed: Empty text handled correctly")


def test_translate_invalid_language_code():
    """Test translation with invalid language code"""
    payload = {
        "text": "Hello",
        "source_lang": "invalid_lang",
        "target_lang": "en"
    }
    
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    # Should handle invalid language gracefully
    data = response.json()
    # Either success=False or it might auto-detect, both acceptable
    assert "success" in data, "Response should contain success field"
    print(f"✓ Test passed: Invalid language code handled")


def test_translate_long_text():
    """Test translation with longer text"""
    payload = {
        "text": "This is a longer text that contains multiple words and should be translated correctly.",
        "source_lang": "en",
        "target_lang": "es"
    }
    
    response = requests.post(TRANSLATE_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Translation should succeed"
    assert len(data["translated_text"]) > 0, "Translated text should not be empty"
    print(f"✓ Test passed: Long text translation")


if __name__ == "__main__":
    print("Starting translation API tests...")
    print(f"Testing endpoint: {TRANSLATE_ENDPOINT}")
    print("=" * 60)
    
    # Wait for service to be ready
    if not wait_for_service():
        print("✗ Service is not available. Please start the server first.")
        exit(1)
    
    tests = [
        test_translate_english_to_chinese,
        test_translate_chinese_to_english,
        test_translate_spanish_to_english,
        test_translate_missing_required_field,
        test_translate_empty_text,
        test_translate_invalid_language_code,
        test_translate_long_text
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

