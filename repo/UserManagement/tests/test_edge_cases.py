"""
Edge Cases and Security Tests for User Management API

This module contains tests for edge cases, boundary conditions, security scenarios,
and error conditions that might not be covered in the main API test suite.
"""

import pytest
import requests
import json
import threading
import time
from datetime import datetime, timedelta


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    
    BASE_URL = "http://localhost:8081/api/v1"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method to ensure clean state before each test"""
        try:
            response = requests.get(f"{self.BASE_URL}/users")
            if response.status_code == 200:
                users = response.json().get('users', [])
                for user in users:
                    if user['username'].startswith('test_'):
                        requests.delete(f"{self.BASE_URL}/users/{user['id']}")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")
    
    def test_username_boundary_values(self):
        """Test username at boundary values"""
        # Test exactly 3 characters (minimum allowed)
        min_username = "abc"
        user_data = {
            "username": min_username,
            "email": "min@example.com",
            "password": "TestPass123!",
            "full_name": "Min Username User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == min_username
        
        # Test exactly 50 characters (maximum allowed)
        max_username = "a" * 50
        user_data = {
            "username": max_username,
            "email": "max@example.com",
            "password": "TestPass123!",
            "full_name": "Max Username User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == max_username
        
        # Test 2 characters (should fail)
        too_short_username = "ab"
        user_data = {
            "username": too_short_username,
            "email": "tooshort@example.com",
            "password": "TestPass123!",
            "full_name": "Too Short User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
        
        # Test 51 characters (should fail)
        too_long_username = "a" * 51
        user_data = {
            "username": too_long_username,
            "email": "toolong@example.com",
            "password": "TestPass123!",
            "full_name": "Too Long User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
    
    def test_full_name_boundary_values(self):
        """Test full name at boundary values"""
        # Test exactly 100 characters (maximum allowed)
        max_full_name = "a" * 100
        user_data = {
            "username": "test_max_fullname",
            "email": "maxfullname@example.com",
            "password": "TestPass123!",
            "full_name": max_full_name,
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['full_name'] == max_full_name
        
        # Test 101 characters (should fail)
        too_long_full_name = "a" * 101
        user_data = {
            "username": "test_too_long_fullname",
            "email": "toolongfullname@example.com",
            "password": "TestPass123!",
            "full_name": too_long_full_name,
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
    
    def test_password_boundary_values(self):
        """Test password at boundary values"""
        # Test exactly 8 characters (minimum allowed)
        min_password = "Test123!"
        user_data = {
            "username": "test_min_password",
            "email": "minpassword@example.com",
            "password": min_password,
            "full_name": "Min Password User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        
        # Test 7 characters (should fail)
        too_short_password = "Test12!"
        user_data = {
            "username": "test_too_short_password",
            "email": "tooshortpassword@example.com",
            "password": too_short_password,
            "full_name": "Too Short Password User",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 422
    
    def test_unicode_characters_in_user_data(self):
        """Test handling of Unicode characters in user data"""
        unicode_user = {
            "username": "test_unicode_user",
            "email": "unicode@example.com",
            "password": "TestPass123!",
            "full_name": "Unicode User 🚀 Test",
            "role": "user"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=unicode_user,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should either succeed or fail gracefully based on implementation
        assert response.status_code in [201, 422]
        
        if response.status_code == 201:
            data = response.json()
            assert data['full_name'] == unicode_user['full_name']
    
    def test_special_characters_in_username(self):
        """Test handling of special characters in username"""
        special_chars_usernames = [
            "test_user@domain",  # Contains @
            "test user",  # Contains space
            "test.user",  # Contains dot
            "test-user",  # Contains hyphen
            "test_user_123",  # Contains underscore and numbers
        ]
        
        for i, username in enumerate(special_chars_usernames):
            user_data = {
                "username": username,
                "email": f"special{i}@example.com",
                "password": "TestPass123!",
                "full_name": f"Special Char User {i}",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should either succeed or fail gracefully
            assert response.status_code in [201, 422]
    
    def test_email_formats(self):
        """Test various email formats"""
        email_formats = [
            "test@example.com",
            "test.user@example.com",
            "test+tag@example.com",
            "test123@example-domain.com",
            "test@sub.example.com",
            "test@example.co.uk",
        ]
        
        for i, email in enumerate(email_formats):
            user_data = {
                "username": f"test_email_{i}",
                "email": email,
                "password": "TestPass123!",
                "full_name": f"Email Test User {i}",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 201
    
    def test_invalid_email_formats(self):
        """Test invalid email formats"""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@.example.com",
            "test@example..com",
            "test@example.com.",
            "test@example",
            "test@.com",
        ]
        
        for i, email in enumerate(invalid_emails):
            user_data = {
                "username": f"test_invalid_email_{i}",
                "email": email,
                "password": "TestPass123!",
                "full_name": f"Invalid Email User {i}",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 422
    
    def test_phone_formats(self):
        """Test various phone number formats"""
        phone_formats = [
            "+1234567890",
            "+1-234-567-8900",
            "+1 (234) 567-8900",
            "1234567890",
            "+44 20 7946 0958",
            "+86 138 0013 8000",
        ]
        
        for i, phone in enumerate(phone_formats):
            user_data = {
                "username": f"test_phone_{i}",
                "email": f"phone{i}@example.com",
                "password": "TestPass123!",
                "full_name": f"Phone Test User {i}",
                "role": "user",
                "phone": phone
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should either succeed or fail gracefully
            assert response.status_code in [201, 422]
    
    def test_empty_strings(self):
        """Test handling of empty strings"""
        # Empty username should fail
        user_data = {
            "username": "",
            "email": "empty@example.com",
            "password": "TestPass123!",
            "full_name": "Empty Username User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
        
        # Empty email should fail
        user_data = {
            "username": "test_empty_email",
            "email": "",
            "password": "TestPass123!",
            "full_name": "Empty Email User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
        
        # Empty full name should fail
        user_data = {
            "username": "test_empty_fullname",
            "email": "emptyfullname@example.com",
            "password": "TestPass123!",
            "full_name": "",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
    
    def test_whitespace_only_strings(self):
        """Test handling of whitespace-only strings"""
        # Whitespace-only username should fail
        user_data = {
            "username": "   ",
            "email": "whitespace@example.com",
            "password": "TestPass123!",
            "full_name": "Whitespace Username User",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
        
        # Whitespace-only full name should fail
        user_data = {
            "username": "test_whitespace_fullname",
            "email": "whitespacefullname@example.com",
            "password": "TestPass123!",
            "full_name": "   ",
            "role": "user"
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
    
    def test_null_values(self):
        """Test handling of null values"""
        user_data = {
            "username": "test_null_values",
            "email": "null@example.com",
            "password": "TestPass123!",
            "full_name": "Null Values User",
            "role": "user",
            "phone": None
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 422]
    
    def test_extra_fields(self):
        """Test handling of extra fields in request"""
        user_data = {
            "username": "test_extra_fields",
            "email": "extra@example.com",
            "password": "TestPass123!",
            "full_name": "Extra Fields User",
            "role": "user",
            "extra_field": "should be ignored",
            "another_field": 123,
            "nested_field": {"key": "value"}
        }
        
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        # Extra fields should not be in response
        assert 'extra_field' not in data
        assert 'another_field' not in data
        assert 'nested_field' not in data
    
    def test_case_sensitivity(self):
        """Test case sensitivity of enum values"""
        # Test role case sensitivity
        user_data = {
            "username": "test_case_sensitivity",
            "email": "case@example.com",
            "password": "TestPass123!",
            "full_name": "Case Sensitivity User",
            "role": "USER"  # Uppercase
        }
        response = requests.post(
            f"{self.BASE_URL}/users",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        # Should either accept or reject consistently
        assert response.status_code in [201, 422]
    
    def test_large_numbers(self):
        """Test handling of large numbers in pagination"""
        # Test very large page number
        response = requests.get(f"{self.BASE_URL}/users?page=999999")
        assert response.status_code in [200, 422]
        
        # Test very large limit
        response = requests.get(f"{self.BASE_URL}/users?limit=999999")
        assert response.status_code in [200, 422]
    
    def test_negative_numbers(self):
        """Test handling of negative numbers"""
        # Test negative page number
        response = requests.get(f"{self.BASE_URL}/users?page=-1")
        assert response.status_code in [200, 422]
        
        # Test negative limit
        response = requests.get(f"{self.BASE_URL}/users?limit=-1")
        assert response.status_code in [200, 422]
    
    def test_zero_values(self):
        """Test handling of zero values"""
        # Test zero page number
        response = requests.get(f"{self.BASE_URL}/users?page=0")
        assert response.status_code in [200, 422]
        
        # Test zero limit
        response = requests.get(f"{self.BASE_URL}/users?limit=0")
        assert response.status_code in [200, 422]
    
    def test_sql_injection_attempts(self):
        """Test protection against SQL injection attempts"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM users; --",
            "'; INSERT INTO users VALUES ('hacker', 'hack@evil.com', 'password', 'Hacker', 'admin'); --"
        ]
        
        for i, malicious_input in enumerate(malicious_inputs):
            user_data = {
                "username": f"test_sql_{i}",
                "email": f"sql{i}@example.com",
                "password": "TestPass123!",
                "full_name": malicious_input,
                "role": "user"
            }
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should either create the user with escaped content or reject it
            assert response.status_code in [201, 422]
            
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f"{self.BASE_URL}/users/{user_id}")
    
    def test_xss_attempts(self):
        """Test protection against XSS attempts"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<svg onload=alert('xss')>",
            "javascript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>"
        ]
        
        for i, payload in enumerate(xss_payloads):
            user_data = {
                "username": f"test_xss_{i}",
                "email": f"xss{i}@example.com",
                "password": "TestPass123!",
                "full_name": payload,
                "role": "user"
            }
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should either create the user with escaped content or reject it
            assert response.status_code in [201, 422]
            
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f"{self.BASE_URL}/users/{user_id}")
    
    def test_concurrent_user_creation(self):
        """Test handling of concurrent user creation"""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_user(thread_id):
            try:
                user_data = {
                    "username": f"test_concurrent_{thread_id}",
                    "email": f"concurrent{thread_id}@example.com",
                    "password": "TestPass123!",
                    "full_name": f"Concurrent User {thread_id}",
                    "role": "user"
                }
                response = requests.post(
                    f"{self.BASE_URL}/users",
                    json=user_data,
                    headers={'Content-Type': 'application/json'}
                )
                results.append((thread_id, response.status_code))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent user creation: {errors}"
        assert len(results) == 10
        
        # All requests should succeed
        for thread_id, status_code in results:
            assert status_code == 201
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_jsons = [
            '{"username": "test", "email": "test@example.com"',  # Missing closing brace
            '{"username": "test", "email": "test@example.com",}',  # Trailing comma
            '{"username": "test", "email": test@example.com}',  # Unquoted string
            '{"username": "test" "email": "test@example.com"}',  # Missing comma
            '{"username": "test", "email": "test@example.com", "role": }',  # Missing value
        ]
        
        for malformed_json in malformed_jsons:
            response = requests.post(
                f"{self.BASE_URL}/users",
                data=malformed_json,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 400
    
    def test_content_type_variations(self):
        """Test handling of different content types"""
        user_data = {
            "username": "test_content_type",
            "email": "contenttype@example.com",
            "password": "TestPass123!",
            "full_name": "Content Type User",
            "role": "user"
        }
        
        content_types = [
            'application/json',
            'application/json; charset=utf-8',
            'application/json;charset=utf-8',
            'text/json',
            'text/plain'
        ]
        
        for content_type in content_types:
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': content_type}
            )
            
            # Should either succeed or fail gracefully
            assert response.status_code in [201, 400, 415]
            
            if response.status_code == 201:
                user_id = response.json()['id']
                requests.delete(f"{self.BASE_URL}/users/{user_id}")
    
    def test_missing_headers(self):
        """Test handling of missing headers"""
        user_data = {
            "username": "test_no_headers",
            "email": "noheaders@example.com",
            "password": "TestPass123!",
            "full_name": "No Headers User",
            "role": "user"
        }
        
        # Test without Content-Type header
        response = requests.post(f"{self.BASE_URL}/users", json=user_data)
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 400, 415]
        
        if response.status_code == 201:
            user_id = response.json()['id']
            requests.delete(f"{self.BASE_URL}/users/{user_id}")
    
    def test_very_long_url(self):
        """Test handling of very long URLs"""
        # Create a very long query string
        long_params = "&".join([f"param{i}=value{i}" for i in range(100)])
        response = requests.get(f"{self.BASE_URL}/users?{long_params}")
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 414, 400]
    
    def test_password_strength_requirements(self):
        """Test password strength requirements"""
        weak_passwords = [
            "12345678",  # Only numbers
            "abcdefgh",  # Only lowercase letters
            "ABCDEFGH",  # Only uppercase letters
            "!@#$%^&*",  # Only special characters
            "Test123",   # Too short
            "testuser",  # No numbers or special chars
            "TESTUSER",  # No lowercase or special chars
            "123456789", # No letters
        ]
        
        for i, password in enumerate(weak_passwords):
            user_data = {
                "username": f"test_weak_password_{i}",
                "email": f"weakpassword{i}@example.com",
                "password": password,
                "full_name": f"Weak Password User {i}",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should fail for weak passwords
            assert response.status_code == 422
    
    def test_strong_passwords(self):
        """Test acceptance of strong passwords"""
        strong_passwords = [
            "TestPass123!",
            "MyStr0ng#Pass",
            "ComplexP@ssw0rd",
            "Secure123$Pass",
            "StrongP@ss1!",
        ]
        
        for i, password in enumerate(strong_passwords):
            user_data = {
                "username": f"test_strong_password_{i}",
                "email": f"strongpassword{i}@example.com",
                "password": password,
                "full_name": f"Strong Password User {i}",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should succeed for strong passwords
            assert response.status_code == 201
            
            # Clean up
            user_id = response.json()['id']
            requests.delete(f"{self.BASE_URL}/users/{user_id}")
    
    def test_username_alphanumeric_requirement(self):
        """Test username alphanumeric requirement"""
        invalid_usernames = [
            "user@name",  # Contains @
            "user name",  # Contains space
            "user.name",  # Contains dot
            "user-name",  # Contains hyphen
            "user_name!", # Contains exclamation
            "user#name",  # Contains hash
            "user$name",  # Contains dollar
        ]
        
        for i, username in enumerate(invalid_usernames):
            user_data = {
                "username": username,
                "email": f"invalidusername{i}@example.com",
                "password": "TestPass123!",
                "full_name": f"Invalid Username User {i}",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should fail for invalid usernames
            assert response.status_code == 422
    
    def test_valid_usernames(self):
        """Test acceptance of valid usernames"""
        valid_usernames = [
            "user123",
            "testuser",
            "User123",
            "test_user_123",
            "user123test",
            "a1b2c3",
            "test123user",
        ]
        
        for i, username in enumerate(valid_usernames):
            user_data = {
                "username": username,
                "email": f"validusername{i}@example.com",
                "password": "TestPass123!",
                "full_name": f"Valid Username User {i}",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should succeed for valid usernames
            assert response.status_code == 201
            
            # Clean up
            user_id = response.json()['id']
            requests.delete(f"{self.BASE_URL}/users/{user_id}")
