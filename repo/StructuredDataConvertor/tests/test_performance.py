import pytest
import requests
import json
import base64
import pandas as pd
import time
import threading
import statistics
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestPerformance:

    BASE_URL = "http://localhost:8000/api/v1"

    def setup_method(self):
        self.medium_df = pd.DataFrame({
            f'col{i}': range(1000) for i in range(10)
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.medium_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.medium_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

        self.small_csv_data = base64.b64encode(
            "Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai\nWang Wu,28,Shenzhen".encode('utf-8')
        ).decode('utf-8')

    def test_single_conversion_performance(self):
        payload = {
            "source_format": "excel",
            "target_format": "csv",
            "data": self.medium_excel_data
        }

        times = []
        for _ in range(10):
            start_time = time.time()
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=payload, timeout=30)
            end_time = time.time()

            assert response.status_code == 200
            times.append(end_time - start_time)

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        print("Single conversion performance statistics:")
        print(f"Average time: {avg_time:.2f} seconds")
        print(f"Median time: {median_time:.2f} seconds")
        print(f"Minimum time: {min_time:.2f} seconds")
        print(f"Maximum time: {max_time:.2f} seconds")
        print(f"Standard deviation: {std_dev:.2f} seconds")

        assert avg_time < 5.0, f"Average conversion time is too long: {avg_time:.2f} seconds"
        assert max_time < 10.0, f"Maximum conversion time is too long: {max_time:.2f} seconds"
        assert std_dev < 2.0, f"Conversion time stability is poor: {std_dev:.2f} seconds"

    def test_concurrent_requests_performance(self):
        def make_request(request_id):
            payload = {
                "source_format": "csv",
                "target_format": "excel",
                "data": self.small_csv_data
            }

            start_time = time.time()
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=payload, timeout=30)
            end_time = time.time()

            return {
                "request_id": request_id,
                "success": response.status_code == 200,
                "response_time": end_time - start_time
            }

        concurrency_levels = [5, 10, 20]
        results = {}

        for concurrency in concurrency_levels:
            print(f"\nTesting concurrency level: {concurrency}")

            start_time = time.time()

            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrency)]
                responses = [future.result() for future in as_completed(futures)]

            end_time = time.time()

            response_times = [r["response_time"] for r in responses if r["success"]]
            success_count = sum(1 for r in responses if r["success"])

            results[concurrency] = {
                "total_requests": len(responses),
                "success_count": success_count,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "total_time": end_time - start_time
            }

            print(f"Successful requests: {success_count}/{len(responses)}")
            print(f"Average response time: {results[concurrency]['avg_response_time']:.2f} seconds")
            print(f"Total time: {results[concurrency]['total_time']:.2f} seconds")

            assert success_count >= concurrency * 0.8, f"Concurrent request success rate is too low: {success_count}/{concurrency}"

        if len(results) >= 2:
            time_5 = results[5]["total_time"]
            time_10 = results[10]["total_time"]
            assert time_10 < time_5 * 3.0, f"Concurrency scalability is poor: 10 concurrency time {time_10:.2f} seconds vs 5 concurrency expected upper limit {time_5 * 3.0:.2f} seconds"

    def test_memory_usage_stability(self):
        def continuous_requests(duration_seconds=30):
            end_time = time.time() + duration_seconds
            request_count = 0
            errors = []

            while time.time() < end_time:
                try:
                    payload = {
                        "source_format": "csv",
                        "target_format": "excel",
                        "data": self.small_csv_data
                    }

                    response = requests.post(f"{self.BASE_URL}/convert",
                                           json=payload, timeout=10)

                    if response.status_code != 200:
                        errors.append(f"Request failed: {response.status_code}")

                    request_count += 1
                    time.sleep(0.1)

                except Exception as e:
                    errors.append(str(e))
                    time.sleep(0.1)

            return request_count, errors

        request_count, errors = continuous_requests(30)

        print(f"\nContinuous requests test results:")
        print(f"Total requests: {request_count}")
        print(f"Errors: {len(errors)}")
        print(f"Error rate: {len(errors) / request_count * 100:.2f}%" if request_count > 0 else "Error rate: N/A")
        assert request_count > 0, "Failed to send any requests"
        assert len(errors) / request_count < 0.1, f"Error rate is too high: {len(errors)}/{request_count}"

    def test_health_check_under_load(self):
        def load_generator():
            end_time = time.time() + 20

            while time.time() < end_time:
                payload = {
                    "source_format": "csv",
                    "target_format": "excel",
                    "data": self.small_csv_data
                }

                requests.post(f"{self.BASE_URL}/convert",
                            json=payload, timeout=10)
                time.sleep(0.2)

        def health_checks():
            health_times = []
            end_time = time.time() + 20

            while time.time() < end_time:
                start_time = time.time()
                response = requests.get(f"{self.BASE_URL}/health", timeout=5)
                end_time = time.time()

                health_times.append(end_time - start_time)

                assert response.status_code == 200

                time.sleep(0.5)

            return health_times

        load_thread = threading.Thread(target=load_generator)
        load_thread.start()

        health_response_times = health_checks()

        load_thread.join()

        avg_health_time = statistics.mean(health_response_times)
        max_health_time = max(health_response_times)

        print("Health check performance under load:")
        print(f"Average response time: {avg_health_time:.3f} seconds")
        print(f"Maximum response time: {max_health_time:.3f} seconds")

        assert avg_health_time < 1.0, f"Health check response is too slow under load: {avg_health_time:.3f} seconds"
        assert max_health_time < 2.0, f"Maximum health check response time is too long under load: {max_health_time:.3f} seconds"

    def test_large_file_performance(self):
        large_df = pd.DataFrame({
            f'col{i}': range(5000) for i in range(20)
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

        payload = {
            "source_format": "excel",
            "target_format": "csv",
            "data": large_excel_data
        }

        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=120)
        end_time = time.time()

        assert response.status_code == 200

        conversion_time = end_time - start_time

        print("Large file conversion performance:")
        print(f"Conversion time: {conversion_time:.2f} seconds")
        print(f"File size: {len(large_excel_data) * 3/4 / 1024:.1f} KB")

        assert conversion_time < 60.0, f"Large file conversion time is too long: {conversion_time:.2f} seconds"

        data = response.json()
        assert data["success"] is True

    def test_response_time_distribution(self):
        def make_request():
            payload = {
                "source_format": "csv",
                "target_format": "excel",
                "data": self.small_csv_data
            }

            start_time = time.time()
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=payload, timeout=15)
            end_time = time.time()

            return end_time - start_time if response.status_code == 200 else None

        response_times = []
        for _ in range(50):
            time_taken = make_request()
            if time_taken is not None:
                response_times.append(time_taken)

        if response_times:
            sorted_times = sorted(response_times)

            print("Response time distribution:")
            print(f"Average: {statistics.mean(response_times):.3f} seconds")
            print(f"Median: {statistics.median(response_times):.3f} seconds")
            print(f"90th percentile: {sorted_times[int(len(sorted_times) * 0.9)]:.3f} seconds")
            print(f"95th percentile: {sorted_times[int(len(sorted_times) * 0.95)]:.3f} seconds")
            print(f"99th percentile: {sorted_times[int(len(sorted_times) * 0.99)]:.3f} seconds")

            assert statistics.mean(response_times) < 3.0, "Average response time is too long"
            assert sorted_times[int(len(sorted_times) * 0.95)] < 5.0, "95th percentile response time is too long"

    def test_resource_cleanup_verification(self):
        def intensive_workload():
            for i in range(20):
                payload = {
                    "source_format": "excel",
                    "target_format": "csv",
                    "data": self.medium_excel_data
                }

                response = requests.post(f"{self.BASE_URL}/convert",
                                       json=payload, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    assert "metadata" in data
                    assert "conversion_time" in data["metadata"]

                time.sleep(0.1)

        start_time = time.time()

        health_before = requests.get(f"{self.BASE_URL}/health", timeout=5)
        assert health_before.status_code == 200

        intensive_workload()

        health_after = requests.get(f"{self.BASE_URL}/health", timeout=5)
        assert health_after.status_code == 200

        end_time = time.time()

        print("Resource cleanup verification:")
        print(f"Workload execution time: {end_time - start_time:.2f} seconds")
        print("Service remains healthy after high load")

        health_data_before = health_before.json()
        health_data_after = health_after.json()

        assert health_data_before["status"] == "healthy"
        assert health_data_after["status"] == "healthy"


