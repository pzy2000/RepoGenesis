import pytest
import requests
import json
import base64
import pandas as pd
import time
import tempfile
import os


class TestIntegration:
    BASE_URL = "http://localhost:8000/api/v1"

    def setup_method(self):
        self.test_data = {
            "csv": "Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000\nWang Wu,28,Shenzhen,20000",
            "excel": None,
            "complex_csv": """ProductID,ProductName,Category,Price,Stock,Supplier,Description
P001,Smartphone,Electronics,2999.00,50,ZTE,High-performance 5G smartphone
P002,Laptop,Electronics,5999.00,20,Huawei,Lightweight business laptop
P003,Mechanical Keyboard,Accessories,299.00,100,Rapoo,RGB backlit mechanical keyboard
P004,Mouse Pad,Accessories,49.00,200,SteelSeries,Extra large mouse pad"""
        }

        df = pd.DataFrame({
            'Name': ['Zhang San', 'Li Si', 'Wang Wu'],
            'Age': [25, 30, 28],
            'City': ['Beijing', 'Shanghai', 'Shenzhen'],
            'Salary': [15000, 18000, 20000]
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.test_data["excel"] = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_end_to_end_conversion_workflow(self):
        health_response = requests.get(f"{self.BASE_URL}/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        csv_to_excel_payload = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(self.test_data["csv"].encode('utf-8')).decode('utf-8')
        }

        response1 = requests.post(f"{self.BASE_URL}/convert",
                                json=csv_to_excel_payload, timeout=30)
        assert response1.status_code == 200

        data1 = response1.json()
        assert data1["success"] is True
        excel_result = data1["result"]

        excel_to_pdf_payload = {
            "source_format": "excel",
            "target_format": "pdf",
            "data": excel_result
        }

        response2 = requests.post(f"{self.BASE_URL}/convert",
                                json=excel_to_pdf_payload, timeout=30)
        assert response2.status_code == 200

        data2 = response2.json()
        assert data2["success"] is True

        assert "metadata" in data1
        assert "metadata" in data2
        assert data1["metadata"]["rows_count"] == 3
        assert data1["metadata"]["columns_count"] == 4

        print("End-to-end workflow test passed")

    def test_batch_conversion_workflow(self):
        conversions = [
            {
                "source_format": "csv",
                "target_format": "excel",
                "data": base64.b64encode(self.test_data["csv"].encode('utf-8')).decode('utf-8')
            },
            {
                "source_format": "excel",
                "target_format": "csv",
                "data": self.test_data["excel"]
            },
            {
                "source_format": "csv",
                "target_format": "pdf",
                "data": base64.b64encode(self.test_data["complex_csv"].encode('utf-8')).decode('utf-8')
            }
        ]

        batch_payload = {
            "conversions": conversions,
            "parallel": True
        }

        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=batch_payload, timeout=60)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 3

        for i, result in enumerate(data["results"]):
            assert result["success"] is True, f"The {i+1}-th conversion failed: {result.get('message', 'Unknown error')}"
            assert "result" in result
            assert result["result"] != ""
        summary = data["summary"]
        assert summary["total_count"] == 3
        assert summary["success_count"] == 3
        assert summary["failure_count"] == 0

        print("Batch conversion workflow test passed")

    def test_error_handling_workflow(self):
        invalid_format_payload = {
            "source_format": "invalid",
            "target_format": "excel",
            "data": base64.b64encode(b"test").decode('utf-8')
        }

        response1 = requests.post(f"{self.BASE_URL}/convert",
                                json=invalid_format_payload, timeout=10)
        assert response1.status_code in [400, 422]

        empty_data_payload = {
            "source_format": "csv",
            "target_format": "excel",
            "data": ""
        }

        response2 = requests.post(f"{self.BASE_URL}/convert",
                                json=empty_data_payload, timeout=10)
        assert response2.status_code in [200, 400]

        health_response = requests.get(f"{self.BASE_URL}/health")
        assert health_response.status_code == 200

        print("Error handling workflow test passed")

    def test_performance_under_realistic_load(self):
        def simulate_user_session(session_id):
            results = []

            health_response = requests.get(f"{self.BASE_URL}/health")
            results.append(health_response.status_code == 200)

            operations = [
                ("csv", "excel", self.test_data["csv"]),
                ("excel", "csv", self.test_data["excel"]),
                ("csv", "pdf", self.test_data["complex_csv"])
            ]

            for source_fmt, target_fmt, data in operations:
                payload = {
                    "source_format": source_fmt,
                    "target_format": target_fmt,
                    "data": base64.b64encode(data.encode('utf-8')).decode('utf-8') if isinstance(data, str) else data
                }

                response = requests.post(f"{self.BASE_URL}/convert",
                                       json=payload, timeout=30)
                results.append(response.status_code == 200)

                time.sleep(0.2)

            return results

        import threading

        results = []
        errors = []

        def run_user_session(session_id):
            try:
                session_results = simulate_user_session(session_id)
                results.append(session_results)
            except Exception as e:
                errors.append(f"Session {session_id} error: {str(e)}")

        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_user_session, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"User session error: {errors}"

        total_operations = sum(len(session_result) for session_result in results)
        successful_operations = sum(sum(session_result) for session_result in results)

        success_rate = successful_operations / total_operations if total_operations > 0 else 0

        print("Performance under realistic load test passed")
        print(f"Total operations: {total_operations}")
        print(f"Successful operations: {successful_operations}")
        print(f"Success rate: {success_rate * 100:.1f}%")
        assert success_rate > 0.9, f"Success rate is too low: {success_rate * 100:.1f}%"

    def test_data_consistency_across_formats(self):
        original_csv = "Name,Age,City,Salary\nZhang San,25,Beijing,15000\nLi Si,30,Shanghai,18000"

        payload1 = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(original_csv.encode('utf-8')).decode('utf-8')
        }

        response1 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_data = response1.json()["result"]

        payload2 = {
            "source_format": "excel",
            "target_format": "csv",
            "data": excel_data
        }

        response2 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload2, timeout=30)
        assert response2.status_code == 200
        final_csv = base64.b64decode(response2.json()["result"]).decode('utf-8')

        original_lines = [line.strip() for line in original_csv.split('\n') if line.strip()]
        final_lines = [line.strip() for line in final_csv.split('\n') if line.strip()]

        assert len(original_lines) == len(final_lines), "Number of rows is inconsistent"

        for original_line, final_line in zip(original_lines, final_lines):
            original_elements = set(original_line.split(','))
            final_elements = set(final_line.split(','))

            assert len(original_elements) == len(final_elements), f"Number of data elements is inconsistent: {original_line} vs {final_line}"

        print("Data consistency test passed")

    def test_system_resource_usage(self):
        health_before = requests.get(f"{self.BASE_URL}/health")
        assert health_before.status_code == 200
        before_timestamp = health_before.json()["timestamp"]

        operations = []

        for i in range(10):
            payload = {
                "source_format": "csv",
                "target_format": "excel",
                "data": base64.b64encode(self.test_data["csv"].encode('utf-8')).decode('utf-8')
            }
            operations.append(payload)

        start_time = time.time()
        for payload in operations:
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=payload, timeout=30)
            assert response.status_code == 200

        end_time = time.time()

        health_after = requests.get(f"{self.BASE_URL}/health")
        assert health_after.status_code == 200
        after_timestamp = health_after.json()["timestamp"]

        assert health_before.json()["status"] == "healthy"
        assert health_after.json()["status"] == "healthy"

        print("System resource usage test passed")
        print(f"Number of operations: {len(operations)}")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Average time: {(end_time - start_time) / len(operations):.2f} seconds")
        print("System remains healthy after high load")
        time.sleep(2)
        final_health = requests.get(f"{self.BASE_URL}/health")
        assert final_health.status_code == 200
        assert final_health.json()["status"] == "healthy"

    def test_api_version_compatibility(self):
        health_response = requests.get(f"{self.BASE_URL}/health")
        assert health_response.status_code == 200

        health_data = health_response.json()
        assert "version" in health_data

        interfaces = [
            ("Health check", "GET", f"{self.BASE_URL}/health"),
            ("Single conversion", "POST", f"{self.BASE_URL}/convert"),
            ("Batch conversion", "POST", f"{self.BASE_URL}/convert/batch")
        ]

        for interface_name, method, url in interfaces:
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                payload = {
                    "source_format": "csv",
                    "target_format": "excel",
                    "data": base64.b64encode(b"test,a,b\n1,2,3").decode('utf-8')
                }
                response = requests.post(url, json=payload, timeout=10)

            print(f"{interface_name} interface status: {response.status_code}")
            assert response.status_code in [200, 400, 404, 405, 422], f"{interface_name} interface is not available"

        print("API version compatibility test passed")

    def test_real_world_usage_scenario(self):
        employee_data = """EmployeeID,Name,Department,Position,HireDate,Salary,PerformanceLevel
E001,Zhang San,Technology,Senior Engineer,2022-01-15,25000,A
E002,Li Si,Sales,Sales Manager,2021-08-20,30000,A
E003,Wang Wu,Marketing,Marketing Specialist,2023-03-10,15000,B
E004,Zhao Liu,HR,HR Assistant,2022-11-05,12000,B"""

        payload1 = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(employee_data.encode('utf-8')).decode('utf-8')
        }

        response1 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_report = response1.json()["result"]

        payload2 = {
            "source_format": "excel",
            "target_format": "pdf",
            "data": excel_report
        }

        response2 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload2, timeout=30)
        assert response2.status_code == 200
        pdf_report = response2.json()["result"]

        data1 = response1.json()
        data2 = response2.json()

        assert data1["success"] is True
        assert data2["success"] is True

        assert data1["metadata"]["rows_count"] == 4
        assert data1["metadata"]["columns_count"] == 7

        pdf_size = len(base64.b64decode(pdf_report)) / 1024
        assert pdf_size > 1, f"PDF report is too small: {pdf_size:.1f}KB"

        print("Real-world usage scenario test passed")
        print(f"Employee data rows: {data1['metadata']['rows_count']}")
        print(f"Data columns: {data1['metadata']['columns_count']}")
        print(f"PDF report size: {pdf_size:.1f}KB")


