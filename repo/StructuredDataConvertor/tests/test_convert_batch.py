import pytest
import requests
import json
import base64
import pandas as pd
import time
import tempfile
import os


class TestConvertBatchEndpoint:
    BASE_URL = "http://localhost:8000/api/v1"

    def setup_method(self):
        self.test_datasets = []

        csv_data = "Name,Age,City\nZhang San,25,Beijing\nLi Si,30,Shanghai"
        self.test_datasets.append({
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
        })

        df = pd.DataFrame({
            'Product': ['ProductA', 'ProductB', 'ProductC'],
            'Price': [100, 200, 300],
            'Stock': [50, 30, 20]
        })
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

        self.test_datasets.append({
            "source_format": "excel",
            "target_format": "csv",
            "data": excel_data
        })

        csv_data2 = "Department,Number of People,Budget\nTechnology Department,10,100000\nSales Department,8,80000\nMarketing Department,5,50000"
        self.test_datasets.append({
            "source_format": "csv",
            "target_format": "pdf",
            "data": base64.b64encode(csv_data2.encode('utf-8')).decode('utf-8')
        })

    def test_batch_conversion_sequential(self):
        payload = {
            "conversions": self.test_datasets,
            "parallel": False
        }

        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=60)
        end_time = time.time()

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert "summary" in data

        assert len(data["results"]) == len(self.test_datasets)

        summary = data["summary"]
        assert summary["total_count"] == len(self.test_datasets)
        assert summary["success_count"] >= 0
        assert summary["failure_count"] >= 0
        assert summary["total_count"] == summary["success_count"] + summary["failure_count"]
        assert summary["total_time"] > 0
        assert end_time - start_time < 45.0

    def test_batch_conversion_parallel(self):
        payload = {
            "conversions": self.test_datasets,
            "parallel": True
        }

        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=60)
        end_time = time.time()

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == len(self.test_datasets)

        parallel_time = end_time - start_time

        sequential_payload = {
            "conversions": self.test_datasets,
            "parallel": False
        }
        seq_start = time.time()
        seq_response = requests.post(f"{self.BASE_URL}/convert/batch",
                                   json=sequential_payload, timeout=60)
        seq_end = time.time()

        sequential_time = seq_end - seq_start

        assert parallel_time <= sequential_time + 5.0

    def test_batch_conversion_with_failures(self):
        invalid_dataset = {
            "source_format": "invalid_format",
            "target_format": "excel",
            "data": base64.b64encode(b"test data").decode('utf-8')
        }

        test_datasets_with_failure = self.test_datasets + [invalid_dataset]

        payload = {
            "conversions": test_datasets_with_failure,
            "parallel": False
        }

        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=30)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        assert len(data["results"]) == len(test_datasets_with_failure)
        summary = data["summary"]
        assert summary["total_count"] == len(test_datasets_with_failure)
        assert summary["success_count"] >= 0
        assert summary["failure_count"] > 0

    def test_batch_conversion_empty_list(self):
        payload = {
            "conversions": [],
            "parallel": False
        }

        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=10)

        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", {})
            assert summary.get("total_count", 0) == 0

    def test_batch_conversion_large_dataset(self):
        large_df = pd.DataFrame({
            f'col{i}': range(100) for i in range(50)
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

        large_datasets = []
        for i in range(3):
            large_datasets.append({
                "source_format": "excel",
                "target_format": "csv",
                "data": large_excel_data
            })

        payload = {
            "conversions": large_datasets,
            "parallel": True
        }

        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=120)
        end_time = time.time()

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        processing_time = end_time - start_time
        assert processing_time < 90.0

        summary = data["summary"]
        assert summary["success_count"] == len(large_datasets)

    def test_batch_conversion_mixed_formats(self):
        mixed_datasets = [
            {
                "source_format": "csv",
                "target_format": "excel",
                "data": base64.b64encode("a,b\n1,2".encode('utf-8')).decode('utf-8')
            },
            {
                "source_format": "excel",
                "target_format": "pdf",
                "data": self.test_datasets[1]["data"]
            },
            {
                "source_format": "csv",
                "target_format": "pdf",
                "data": base64.b64encode("x,y,z\n1,2,3\n4,5,6".encode('utf-8')).decode('utf-8')
            }
        ]

        payload = {
            "conversions": mixed_datasets,
            "parallel": False
        }

        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=45)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == len(mixed_datasets)

        for i, result in enumerate(data["results"]):
            assert "success" in result
            assert "message" in result
            if result["success"]:
                assert "result" in result
                assert result["result"] != ""

    def test_batch_conversion_performance_comparison(self):
        test_data = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode("a,b,c\n1,2,3\n4,5,6".encode('utf-8')).decode('utf-8')
        }

        single_start = time.time()
        for _ in range(3):
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=test_data, timeout=30)
            assert response.status_code == 200
        single_end = time.time()
        single_avg_time = (single_end - single_start) / 3

        batch_payload = {
            "conversions": [test_data, test_data, test_data],
            "parallel": True
        }

        batch_start = time.time()
        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=batch_payload, timeout=60)
        batch_end = time.time()
        batch_time = batch_end - batch_start

        assert response.status_code == 200

        data = response.json()
        summary = data["summary"]

        assert batch_time <= single_avg_time * 4

        assert summary["success_count"] == 3
