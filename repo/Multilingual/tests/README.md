# Test Suite for Multilingual API

This directory contains comprehensive test cases for all API endpoints of the Multilingual and Multi-Timezone Support Service.

## Test Structure

The test suite is organized into separate files for each API endpoint:

- `test_translate.py` - Tests for the `/api/translate` endpoint (7 test cases)
- `test_timezone.py` - Tests for the `/api/timezone` endpoint (8 test cases)
- `test_localize.py` - Tests for the `/api/localize` endpoint (9 test cases)
- `test_languages.py` - Tests for the `/api/languages` endpoint (9 test cases)
- `run_all_tests.py` - Comprehensive test runner with metrics calculation

**Total: 33 test cases across 4 endpoints**

## Prerequisites

1. Install required dependencies:
```bash
pip install -r ../requirements.txt
```

2. Start the API service:
```bash
cd ..
python app.py
```

The service should be running on `http://localhost:5000`

## Running Tests

### Option 1: Run All Tests with Metrics

Use the comprehensive test runner to execute all tests and see detailed metrics:

```bash
cd tests
python run_all_tests.py
```

This will:
- Check service availability
- Run all test files sequentially
- Calculate test case pass rate
- Calculate repository pass rate
- Display a comprehensive summary

### Option 2: Run Individual Test Files

Run tests for a specific endpoint:

```bash
cd tests
python test_translate.py    # Test translation endpoint
python test_timezone.py     # Test timezone conversion endpoint
python test_localize.py     # Test localization endpoint
python test_languages.py    # Test languages query endpoint
```

### Option 3: Use pytest

Run with pytest for detailed output:

```bash
cd tests
pytest test_translate.py -v
pytest test_timezone.py -v
pytest test_localize.py -v
pytest test_languages.py -v

# Or run all tests at once
pytest -v
```

## Test Coverage

### Translation Endpoint (`/api/translate`)
- ✓ English to Chinese translation
- ✓ Chinese to English translation
- ✓ Spanish to English translation
- ✓ Missing required field handling
- ✓ Empty text handling
- ✓ Invalid language code handling
- ✓ Long text translation

### Timezone Endpoint (`/api/timezone`)
- ✓ UTC to Shanghai conversion
- ✓ New York to London conversion
- ✓ Same timezone conversion
- ✓ Missing required field handling
- ✓ Invalid datetime format handling
- ✓ Invalid timezone name handling
- ✓ Midnight edge case
- ✓ Cross-date boundary conversion

### Localization Endpoint (`/api/localize`)
- ✓ US English localization
- ✓ Chinese localization
- ✓ Spanish localization
- ✓ Japanese localization
- ✓ Missing required field handling
- ✓ Invalid datetime handling
- ✓ Invalid timezone handling
- ✓ UTC timezone localization
- ✓ Different locale format verification

### Languages Endpoint (`/api/languages`)
- ✓ GET request handling
- ✓ Common languages present
- ✓ Response format validation
- ✓ Response structure validation
- ✓ Consistency across requests
- ✓ English language present
- ✓ Reasonable language count
- ✓ No empty values
- ✓ JSON serialization

## Metrics

### Test Case Pass Rate
Calculated as:
```
Test Case Pass Rate = (Passed Tests / Total Tests) × 100%
```

This metric measures the percentage of individual test cases that pass.

### Repository Pass Rate
Calculated as:
```
Repository Pass Rate = (Test Files with All Tests Passing / Total Test Files) × 100%
```

This metric measures the percentage of test files where all tests pass. A single failed test in a file means that file is counted as failed.

## Expected Output

When all tests pass, you should see output similar to:

```
======================================================================
MULTILINGUAL API TEST SUITE
======================================================================
Target URL: http://localhost:5000
...

======================================================================
TEST SUMMARY
======================================================================
✓ PASS | test_translate.py
       | Passed: 7, Failed: 0
✓ PASS | test_timezone.py
       | Passed: 8, Failed: 0
✓ PASS | test_localize.py
       | Passed: 9, Failed: 0
✓ PASS | test_languages.py
       | Passed: 9, Failed: 0

======================================================================
METRICS
======================================================================
Test Case Pass Rate:
  - Total Tests: 33
  - Passed: 33
  - Failed: 0
  - Pass Rate: 100.00%

Repository Pass Rate:
  - Total Test Files: 4
  - Passed: 4
  - Failed: 0
  - Pass Rate: 100.00%
======================================================================

✓ All tests passed!
```

## Test Design Principles

1. **No Mocking**: All tests hit the actual HTTP endpoints on the real port (5000)
2. **Comprehensive Coverage**: Tests cover happy paths, error cases, and edge cases
3. **Independent Tests**: Each test is self-contained and can run independently
4. **Clear Assertions**: Each test has clear, specific assertions
5. **Informative Output**: Tests provide detailed pass/fail information

## Troubleshooting

### Service Not Available
If tests fail with "Service is not available":
1. Check if the service is running: `curl http://localhost:5000/api/languages`
2. Start the service: `python app.py` (from project root)
3. Check if port 5000 is already in use

### Connection Refused
- Ensure no firewall is blocking localhost connections
- Verify the service is listening on the correct port

### Import Errors
- Ensure all dependencies are installed: `pip install -r ../requirements.txt`

### Timeout Errors
- The service might be slow to start or respond
- Wait a few seconds and try again
- Check system resources

## Notes

- Tests are designed to be simple and straightforward
- Each test file can be run independently
- Tests use standard HTTP requests via the `requests` library
- No database or external service dependencies (except the API itself)
- All datetime and timezone operations use standard formats

