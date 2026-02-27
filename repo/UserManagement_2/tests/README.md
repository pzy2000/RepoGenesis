# ProjectC Test Documentation

## Test Overview

This directory contains the complete test suite for the ProjectC user management microservice, designed using Test-Driven Development (TDD) methodology.

## Test Structure

### Test Files
- `test_user_api.py`: Core API functionality tests
- `test_edge_cases.py`: Boundary conditions and exception handling tests
- `conftest.py`: Pytest configuration and test fixtures
- `pytest.ini`: Pytest configuration file
- `requirements.txt`: Test dependency packages

### Test Categories

#### 1. Functional Tests (test_user_api.py)
- **User Registration Tests**
  - Successful registration
  - Duplicate username registration
  - Invalid email registration
  - Password length validation

- **User Login Tests**
  - Successful login
  - Invalid credentials login

- **User Information Management Tests**
  - Get user information
  - Update user information
  - Delete user
  - Permission verification

#### 2. Boundary Tests (test_edge_cases.py)
- **Input Validation Tests**
  - Empty request body
  - Field length limits
  - Special character handling
  - Malformed data

- **Security Tests**
  - Unauthorized access
  - Cross-user data access
  - Token verification

- **Exception Handling Tests**
  - Non-existent resources
  - Unsupported HTTP methods
  - Invalid URL paths

## Running Tests

### Environment Setup
```bash
# Install test dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export API_BASE_URL=http://localhost:8080/api/v1
```

### Run All Tests
```bash
pytest
```

### Run Specific Tests
```bash
# Run functional tests
pytest test_user_api.py

# Run boundary tests
pytest test_edge_cases.py

# Skip slow tests
pytest -m "not slow"

# Run only fast tests
pytest -m "not slow and not integration"
```

### Generate Test Reports
```bash
# Generate coverage report
pytest --cov-report=html

# Generate JUnit format report
pytest --junitxml=test-results.xml
```

## Test Metrics

### Target Metrics
- **Test Coverage**: ≥ 80%
- **Test Pass Rate**: ≥ 95%
- **API Response Time**: < 200ms

### Test Data
- Test user: `testuser`
- Test email: `test@example.com`
- Test password: `password123`

## Notes

1. **Test Isolation**: Each test case is independent and does not depend on the state of other tests
2. **Data Cleanup**: Automatically clean up created test data after tests
3. **Service Dependency**: Tests require a running API service
4. **Concurrency Safety**: Supports parallel test execution

## Troubleshooting

### Common Issues
1. **Connection Refused**: Ensure API service is running on port 8080
2. **Authentication Failed**: Check JWT key configuration
3. **Database Error**: Ensure database connection is normal

### Debug Mode
```bash
# Verbose output
pytest -v -s

# Debug specific test
pytest -v -s test_user_api.py::TestUserAPI::test_user_registration_success
```
