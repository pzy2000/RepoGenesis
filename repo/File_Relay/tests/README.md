# File Relay API Tests

## Overview

This test suite validates the File Relay API implementation according to the specifications in the main README.md. The tests cover all API endpoints, edge cases, and security considerations.

## Test Structure

### Test Files

1. **test_file_api.py** - Core functionality tests
   - Health check
   - User authentication (registration and login)
   - File upload (text, images, PDF documents)
   - File listing and pagination
   - File information retrieval
   - File download
   - File deletion
   - File metadata updates
   - File search
   - Permission controls

2. **test_edge_cases.py** - Edge cases and security tests
   - Large file handling
   - File size limit enforcement
   - Special characters in filenames
   - Unicode filename support
   - Path traversal protection
   - SQL injection prevention
   - Concurrent uploads
   - Pagination boundary cases
   - Invalid input handling
   - Token validation
   - Double deletion
   - Unsupported file types
   - Duplicate filenames

### Configuration Files

- **conftest.py** - Pytest fixtures and configuration
  - Service availability checking
  - User registration and authentication
  - Sample file generation (text, image, PDF)
  - File upload/cleanup helpers
  - Multi-user testing support

- **pytest.ini** - Pytest configuration
  - Test markers definition
  - Output formatting
  - Timeout settings
  - Logging configuration

- **requirements.txt** - Test dependencies
  - pytest
  - requests
  - pytest-cov (for coverage reports)
  - pytest-xdist (for parallel test execution)

## Running the Tests

### Prerequisites

1. Ensure the File Relay API is running at `http://localhost:8085`
2. Install test dependencies:

```bash
cd tests
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest -v
```

### Run Specific Test Categories

```bash
# Run only authentication tests
pytest -v -m auth

# Run only upload tests
pytest -v -m upload

# Run only download tests
pytest -v -m download

# Run only edge case tests
pytest -v -m edge

# Run API functionality tests
pytest -v -m api
```

### Run Specific Test Files

```bash
# Run core API tests
pytest test_file_api.py -v

# Run edge case tests
pytest test_edge_cases.py -v
```

### Run Tests with Coverage

```bash
pytest --cov=.. --cov-report=html --cov-report=term
```

This generates a coverage report in the `htmlcov/` directory.

### Run Tests in Parallel

```bash
pytest -n auto
```

This uses pytest-xdist to run tests in parallel using all available CPU cores.

### Skip Slow Tests

```bash
pytest -v -m "not slow"
```

## Test Categories

### Markers

- `api` - Core API functionality tests
- `auth` - Authentication and authorization tests
- `upload` - File upload tests
- `download` - File download tests
- `edge` - Edge case and boundary tests
- `integration` - Integration tests
- `slow` - Tests that take longer to run (e.g., large file uploads)

## Test Coverage

The test suite covers:

### Functional Requirements
- ✅ Health check endpoint
- ✅ User registration with validation
- ✅ User login with token generation
- ✅ File upload with multiple file types
- ✅ File listing with pagination
- ✅ File filtering by type and uploader
- ✅ File information retrieval
- ✅ File download with proper headers
- ✅ File deletion with permission checks
- ✅ File metadata updates
- ✅ File search functionality

### Security & Edge Cases
- ✅ Authentication and authorization
- ✅ File size limits (max 100MB)
- ✅ File type validation
- ✅ Special characters in filenames
- ✅ Unicode filename support
- ✅ Path traversal prevention
- ✅ SQL injection prevention
- ✅ Concurrent operations
- ✅ Invalid input handling
- ✅ Permission enforcement
- ✅ Token validation
- ✅ Resource cleanup (deletion)

### HTTP Status Codes
- ✅ 200 OK - Successful requests
- ✅ 201 Created - Resource creation
- ✅ 400 Bad Request - Invalid input
- ✅ 401 Unauthorized - Missing/invalid auth
- ✅ 403 Forbidden - Insufficient permissions
- ✅ 404 Not Found - Resource not found
- ✅ 409 Conflict - Resource already exists
- ✅ 413 Payload Too Large - File size exceeded
- ✅ 415 Unsupported Media Type - Invalid file type

## Expected Test Results

A fully compliant implementation should pass all tests with 100% pass rate.

### Critical Tests
These tests MUST pass for a valid implementation:
- Health check availability
- User registration and login
- File upload (at least text and image files)
- File download
- File listing
- Authentication enforcement
- Permission controls (owner-only deletion)

### Optional Enhanced Features
Some tests check for enhanced features that may be implementation-dependent:
- Advanced file type filtering
- Full Unicode filename support
- File size limit enforcement at exactly 100MB
- Unsupported file type rejection

## Troubleshooting

### Service Not Available
If tests fail with "File Relay API server not available":
- Ensure the API is running at `http://localhost:8085`
- Check the API health endpoint manually: `curl http://localhost:8085/api/v1/health`
- Verify no firewall is blocking the connection

### Authentication Failures
If authentication tests fail:
- Check that user registration is working correctly
- Verify token generation in login response
- Ensure tokens are being validated properly

### File Upload Failures
If file upload tests fail:
- Check file size limits are properly configured
- Verify multipart/form-data handling
- Ensure file storage directory has write permissions

### Timeout Errors
If tests timeout:
- Increase timeout values in pytest.ini
- Check server performance
- Skip slow tests: `pytest -m "not slow"`

## Custom Configuration

You can customize the API base URL using an environment variable:

```bash
export API_BASE_URL=http://custom-host:8085/api/v1
pytest -v
```

## Contributing Test Cases

When adding new test cases:
1. Follow the existing test structure
2. Use appropriate markers
3. Include docstrings explaining the test purpose
4. Clean up resources (uploaded files) after tests
5. Handle both success and failure scenarios
6. Test boundary conditions

## Test Metrics

The test suite evaluates:
- **Test Case Pass Rate**: Individual test pass percentage
- **Repository Pass Rate**: Overall repository compliance
- **Code Coverage**: Percentage of code exercised by tests

Success criteria:
- 100% test case pass rate for compliant implementations
- Clear error messages for non-compliant behavior
- Comprehensive coverage of specification requirements


