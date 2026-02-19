# RBAC Service Test Suite

This directory contains the test suite for the Simple RBAC Service.

## Prerequisites

1. Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Tests

1. **Start the RBAC service** on `http://localhost:8080`
   
   The service must be running before executing the tests.

2. **Execute the test suite**:
   ```bash
   python test_rbac_service.py
   ```

## Test Cases

The test suite includes 9 test cases:

1. **test_create_role**: Tests basic role creation
2. **test_create_multiple_roles**: Tests creating multiple roles
3. **test_assign_permissions_to_role**: Tests assigning permissions to a role
4. **test_assign_role_to_user**: Tests assigning roles to users
5. **test_check_user_permissions**: Tests retrieving user permissions
6. **test_multiple_roles_permissions**: Tests that users with multiple roles get combined permissions
7. **test_duplicate_role_error**: Tests error handling for duplicate roles
8. **test_invalid_role_id**: Tests error handling for invalid role IDs
9. **test_user_without_roles**: Tests that users without roles have no permissions

## Expected Output

The test runner will print:
- ✓ for passed tests
- ✗ for failed tests with error messages

At the end, a summary is displayed with:
- Total number of tests
- Number of passed/failed tests
- Test Case Pass Rate (percentage)
- Repository Pass Rate (1 if all tests pass, 0 otherwise)

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

## Notes

- Tests use real HTTP requests (no mocking)
- Tests expect the service to run on port 8080
- Each test is independent but some tests depend on previous test results
- The service should reset to a clean state between test runs for consistent results

