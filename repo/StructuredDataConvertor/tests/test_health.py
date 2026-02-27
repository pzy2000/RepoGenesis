import pytest
import requests
import json
import time
from datetime import datetime, timedelta


class TestHealthEndpoint:
    BASE_URL = "http://localhost:8000/api/v1"

    def test_health_endpoint_available(self):
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "timestamp" in data
            assert "version" in data

            assert data["status"] in ["healthy", "unhealthy"]

            datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))

        except requests.exceptions.ConnectionError:
            pytest.fail("Unable to connect to the service, please ensure the service is started")

    def test_health_response_format(self):
        response = requests.get(f"{self.BASE_URL}/health")
        data = response.json()

        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data, f"Response is missing required field: {field}"
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["version"], str)

    def test_health_endpoint_performance(self):
        start_time = time.time()

        response = requests.get(f"{self.BASE_URL}/health")

        end_time = time.time()
        response_time = end_time - start_time

        assert response_time < 1.0, f"Health check response time is too long: {response_time:.2f} seconds"

        assert response.status_code == 200

    def test_health_endpoint_concurrent_requests(self):
        import threading

        results = []
        errors = []

        def make_request():
            try:
                response = requests.get(f"{self.BASE_URL}/health", timeout=5)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Errors occurred during concurrent requests: {errors}"
        assert len(results) == 10
        assert all(status == 200 for status in results)

    def test_health_endpoint_headers(self):
        response = requests.get(f"{self.BASE_URL}/health")

        assert response.headers["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in response.headers or "*" in response.headers.get("Access-Control-Allow-Origin", "")

    @pytest.mark.parametrize("invalid_method", ["POST", "PUT", "DELETE"])
    def test_health_endpoint_invalid_methods(self, invalid_method):
        response = requests.request(invalid_method, f"{self.BASE_URL}/health")

        assert response.status_code in [200, 405]

    def test_health_endpoint_with_query_params(self):
        response = requests.get(f"{self.BASE_URL}/health?param=test&debug=1")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


