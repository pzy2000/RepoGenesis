#!/usr/bin/env python3
"""
Test suite for Simple RBAC Service
Tests real HTTP endpoints without mocking
"""

import json
import requests
import sys
from typing import Dict, List, Any


# Service configuration
BASE_URL = "http://localhost:8080"
API_PREFIX = "/api"


class RBACServiceTester:
    """Test class for RBAC Service API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = {
            "test_name": test_name,
            "status": status,
            "message": message
        }
        self.test_results.append(result)
        
        if passed:
            self.passed += 1
            print(f"✓ {test_name}")
        else:
            self.failed += 1
            print(f"✗ {test_name}: {message}")
    
    def test_create_role(self):
        """Test Case 1: Create a new role"""
        test_name = "test_create_role"
        
        try:
            response = requests.post(
                f"{self.base_url}{API_PREFIX}/roles",
                json={"role_name": "admin"},
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_test(test_name, False, f"Expected status 200, got {response.status_code}")
                return None
            
            data = response.json()
            
            if data.get("status") != "success":
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return None
            
            if "role_id" not in data or "role_name" not in data:
                self.log_test(test_name, False, "Missing required fields in response")
                return None
            
            if data["role_name"] != "admin":
                self.log_test(test_name, False, f"Expected role_name 'admin', got {data['role_name']}")
                return None
            
            self.log_test(test_name, True)
            return data["role_id"]
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return None
    
    def test_create_multiple_roles(self):
        """Test Case 2: Create multiple roles"""
        test_name = "test_create_multiple_roles"
        
        roles = ["editor", "viewer", "moderator"]
        role_ids = {}
        
        try:
            for role_name in roles:
                response = requests.post(
                    f"{self.base_url}{API_PREFIX}/roles",
                    json={"role_name": role_name},
                    timeout=5
                )
                
                if response.status_code != 200:
                    self.log_test(test_name, False, f"Failed to create role '{role_name}'")
                    return None
                
                data = response.json()
                if data.get("status") != "success":
                    self.log_test(test_name, False, f"Failed to create role '{role_name}'")
                    return None
                
                role_ids[role_name] = data["role_id"]
            
            self.log_test(test_name, True)
            return role_ids
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return None
    
    def test_assign_permissions_to_role(self, role_id: str):
        """Test Case 3: Assign permissions to a role"""
        test_name = "test_assign_permissions_to_role"
        
        if not role_id:
            self.log_test(test_name, False, "No role_id provided (dependency failed)")
            return False
        
        try:
            permissions = ["read", "write", "delete"]
            response = requests.post(
                f"{self.base_url}{API_PREFIX}/roles/{role_id}/permissions",
                json={"permissions": permissions},
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_test(test_name, False, f"Expected status 200, got {response.status_code}")
                return False
            
            data = response.json()
            
            if data.get("status") != "success":
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            
            if data.get("role_id") != role_id:
                self.log_test(test_name, False, "Role ID mismatch")
                return False
            
            returned_permissions = data.get("permissions", [])
            if not all(p in returned_permissions for p in permissions):
                self.log_test(test_name, False, "Not all permissions were assigned")
                return False
            
            self.log_test(test_name, True)
            return True
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def test_assign_role_to_user(self, role_ids: List[str], user_id: str = "user123"):
        """Test Case 4: Assign roles to a user"""
        test_name = "test_assign_role_to_user"
        
        if not role_ids:
            self.log_test(test_name, False, "No role_ids provided (dependency failed)")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}{API_PREFIX}/users/{user_id}/roles",
                json={"role_ids": role_ids},
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_test(test_name, False, f"Expected status 200, got {response.status_code}")
                return False
            
            data = response.json()
            
            if data.get("status") != "success":
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            
            if data.get("user_id") != user_id:
                self.log_test(test_name, False, "User ID mismatch")
                return False
            
            returned_role_ids = data.get("role_ids", [])
            if not all(rid in returned_role_ids for rid in role_ids):
                self.log_test(test_name, False, "Not all roles were assigned")
                return False
            
            self.log_test(test_name, True)
            return True
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def test_check_user_permissions(self, user_id: str, expected_permissions: List[str]):
        """Test Case 5: Check user permissions"""
        test_name = "test_check_user_permissions"
        
        try:
            response = requests.get(
                f"{self.base_url}{API_PREFIX}/users/{user_id}/permissions",
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_test(test_name, False, f"Expected status 200, got {response.status_code}")
                return False
            
            data = response.json()
            
            if data.get("status") != "success":
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            
            if data.get("user_id") != user_id:
                self.log_test(test_name, False, "User ID mismatch")
                return False
            
            permissions = data.get("permissions", [])
            if not all(p in permissions for p in expected_permissions):
                self.log_test(test_name, False, 
                             f"Missing permissions. Expected: {expected_permissions}, Got: {permissions}")
                return False
            
            self.log_test(test_name, True)
            return True
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def test_multiple_roles_permissions(self):
        """Test Case 6: User with multiple roles gets combined permissions"""
        test_name = "test_multiple_roles_permissions"
        
        try:
            # Create two roles with different permissions
            role1_response = requests.post(
                f"{self.base_url}{API_PREFIX}/roles",
                json={"role_name": "role1"},
                timeout=5
            )
            role1_id = role1_response.json()["role_id"]
            
            role2_response = requests.post(
                f"{self.base_url}{API_PREFIX}/roles",
                json={"role_name": "role2"},
                timeout=5
            )
            role2_id = role2_response.json()["role_id"]
            
            # Assign different permissions to each role
            requests.post(
                f"{self.base_url}{API_PREFIX}/roles/{role1_id}/permissions",
                json={"permissions": ["read", "write"]},
                timeout=5
            )
            
            requests.post(
                f"{self.base_url}{API_PREFIX}/roles/{role2_id}/permissions",
                json={"permissions": ["delete", "admin"]},
                timeout=5
            )
            
            # Assign both roles to a user
            user_id = "multi_role_user"
            requests.post(
                f"{self.base_url}{API_PREFIX}/users/{user_id}/roles",
                json={"role_ids": [role1_id, role2_id]},
                timeout=5
            )
            
            # Check user has all permissions
            response = requests.get(
                f"{self.base_url}{API_PREFIX}/users/{user_id}/permissions",
                timeout=5
            )
            
            permissions = response.json().get("permissions", [])
            expected = ["read", "write", "delete", "admin"]
            
            if not all(p in permissions for p in expected):
                self.log_test(test_name, False, 
                             f"Missing permissions. Expected: {expected}, Got: {permissions}")
                return False
            
            self.log_test(test_name, True)
            return True
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def test_duplicate_role_error(self):
        """Test Case 7: Creating duplicate role should fail"""
        test_name = "test_duplicate_role_error"
        
        try:
            role_name = "duplicate_role"
            
            # Create first role
            response1 = requests.post(
                f"{self.base_url}{API_PREFIX}/roles",
                json={"role_name": role_name},
                timeout=5
            )
            
            if response1.status_code != 200:
                self.log_test(test_name, False, "Failed to create first role")
                return False
            
            # Try to create duplicate
            response2 = requests.post(
                f"{self.base_url}{API_PREFIX}/roles",
                json={"role_name": role_name},
                timeout=5
            )
            
            # Should get error (status != success or status_code != 200)
            if response2.status_code == 200:
                data = response2.json()
                if data.get("status") == "success":
                    self.log_test(test_name, False, "Duplicate role was allowed")
                    return False
            
            self.log_test(test_name, True)
            return True
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def test_invalid_role_id(self):
        """Test Case 8: Assigning permissions to non-existent role should fail"""
        test_name = "test_invalid_role_id"
        
        try:
            response = requests.post(
                f"{self.base_url}{API_PREFIX}/roles/nonexistent_role_id/permissions",
                json={"permissions": ["read"]},
                timeout=5
            )
            
            # Should get error
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.log_test(test_name, False, "Non-existent role_id was accepted")
                    return False
            
            self.log_test(test_name, True)
            return True
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def test_user_without_roles(self):
        """Test Case 9: User without roles should have no permissions"""
        test_name = "test_user_without_roles"
        
        try:
            user_id = "user_no_roles"
            response = requests.get(
                f"{self.base_url}{API_PREFIX}/users/{user_id}/permissions",
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_test(test_name, False, f"Expected status 200, got {response.status_code}")
                return False
            
            data = response.json()
            permissions = data.get("permissions", [])
            
            if len(permissions) != 0:
                self.log_test(test_name, False, f"User without roles should have no permissions, got {permissions}")
                return False
            
            self.log_test(test_name, True)
            return True
            
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary and metrics"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        repo_pass = 1 if self.failed == 0 else 0
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"\nMetrics:")
        print(f"  Test Case Pass Rate: {pass_rate:.2f}%")
        print(f"  Repository Pass Rate: {repo_pass}")
        print("="*60)
        
        return repo_pass
    
    def run_all_tests(self):
        """Run all test cases in sequence"""
        print("Starting RBAC Service Tests...")
        print(f"Testing service at: {self.base_url}\n")
        
        # Basic tests
        admin_role_id = self.test_create_role()
        role_ids_dict = self.test_create_multiple_roles()
        
        # Permission assignment tests
        if admin_role_id:
            self.test_assign_permissions_to_role(admin_role_id)
        
        # User role assignment tests
        if role_ids_dict and "editor" in role_ids_dict:
            editor_role_id = role_ids_dict["editor"]
            
            # Assign permissions to editor role
            requests.post(
                f"{self.base_url}{API_PREFIX}/roles/{editor_role_id}/permissions",
                json={"permissions": ["read", "write"]},
                timeout=5
            )
            
            # Assign role to user
            self.test_assign_role_to_user([editor_role_id], "test_user_1")
            
            # Check user permissions
            self.test_check_user_permissions("test_user_1", ["read", "write"])
        
        # Advanced tests
        self.test_multiple_roles_permissions()
        
        # Error handling tests
        self.test_duplicate_role_error()
        self.test_invalid_role_id()
        self.test_user_without_roles()
        
        # Print summary
        repo_pass = self.print_summary()
        
        return repo_pass


def main():
    """Main test runner"""
    # Check if service is reachable
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print(f"Service is reachable at {BASE_URL}\n")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Cannot reach service at {BASE_URL}")
        print(f"Please ensure the RBAC service is running on port 8080")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Run tests
    tester = RBACServiceTester(BASE_URL)
    repo_pass = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if repo_pass == 1 else 1)


if __name__ == "__main__":
    main()

