import pytest
import requests
import json
import base64
import pandas as pd
import io
import os
import tempfile


class TestConvertEndpoint:

    BASE_URL = "http://localhost:8000/api/v1"

    SAMPLE_CSV_DATA = """Name,Age,City,Salary
Zhang San,25,Beijing,15000
Li Si,30,Shanghai,18000
Wang Wu,28,Shenzhen,20000
Zhao Liu,35,Guangzhou,16000"""

    SAMPLE_EXCEL_DATA = None

    def setup_method(self):
        df = pd.DataFrame({
            'Name': ['Zhang San', 'Li Si', 'Wang Wu', 'Zhao Liu'],
            'Age': [25, 30, 28, 35],
            'City': ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou'],
            'Salary': [15000, 18000, 20000, 16000]
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.SAMPLE_EXCEL_DATA = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_csv_to_excel_conversion(self):
        payload = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'),
            "options": {
                "encoding": "utf-8",
                "has_header": True
            }
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=30)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert data["result"] != ""

        assert "metadata" in data
        assert data["metadata"]["source_size"] > 0
        assert data["metadata"]["target_size"] > 0
        assert data["metadata"]["conversion_time"] > 0
        assert data["metadata"]["rows_count"] == 4
        assert data["metadata"]["columns_count"] == 4

    def test_excel_to_csv_conversion(self):
        payload = {
            "source_format": "excel",
            "target_format": "csv",
            "data": self.SAMPLE_EXCEL_DATA,
            "options": {
                "encoding": "utf-8",
                "has_header": True
            }
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=30)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        result_data = base64.b64decode(data["result"]).decode('utf-8')

        lines = result_data.strip().split('\n')
        assert len(lines) >= 2

        headers = lines[0].split(',')
        assert "Name" in headers
        assert "Age" in headers
        assert "City" in headers
        assert "Salary" in headers

    def test_excel_to_pdf_conversion(self):
        payload = {
            "source_format": "excel",
            "target_format": "pdf",
            "data": self.SAMPLE_EXCEL_DATA,
            "options": {
                "encoding": "utf-8",
                "has_header": True,
                "sheet_name": "Sheet1"
            }
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=30)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "result" in data

        result_data = base64.b64decode(data["result"])
        assert len(result_data) > 1000

    def test_csv_to_pdf_conversion(self):
        payload = {
            "source_format": "csv",
            "target_format": "pdf",
            "data": base64.b64encode(self.SAMPLE_CSV_DATA.encode('utf-8')).decode('utf-8'),
            "options": {
                "encoding": "utf-8",
                "has_header": True,
                "delimiter": ","
            }
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=30)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        result_data = base64.b64decode(data["result"])
        assert len(result_data) > 1000

    def test_invalid_format_conversion(self):
        payload = {
            "source_format": "invalid",
            "target_format": "excel",
            "data": base64.b64encode(b"test data").decode('utf-8')
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=10)

        assert response.status_code in [400, 422]

    def test_empty_data_conversion(self):
        payload = {
            "source_format": "csv",
            "target_format": "excel",
            "data": "",
            "options": {
                "has_header": True
            }
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=10)

        assert response.status_code in [200, 400]

    def test_large_file_conversion(self):
        large_data = pd.DataFrame({
            f'col{i}': range(1000) for i in range(20)
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_data.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

        payload = {
            "source_format": "excel",
            "target_format": "csv",
            "data": large_excel_data,
            "options": {
                "encoding": "utf-8",
                "has_header": True
            }
        }

        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=60)
        end_time = time.time()

        assert response.status_code == 200
        conversion_time = end_time - start_time

        assert conversion_time < 30.0

        data = response.json()
        assert data["success"] is True

    @pytest.mark.parametrize("encoding", ["utf-8", "gbk", "utf-16"])
    def test_different_encodings(self, encoding):
        test_data = "name,age\nZhang San,25\nLi Si,30"

        try:
            encoded_data = test_data.encode(encoding)
            payload = {
                "source_format": "csv",
                "target_format": "excel",
                "data": base64.b64encode(encoded_data).decode('utf-8'),
                "options": {
                    "encoding": encoding,
                    "has_header": True
                }
            }

            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=payload, timeout=15)

            assert response.status_code in [200, 400, 422]

        except UnicodeEncodeError:
            pytest.skip(f"encoding {encoding} does not support Chinese characters")

    def test_conversion_with_special_characters(self):
        special_data = """name,description,symbol
Zhang San,contains @ and #,Beijing @ Shanghai # Shenzhen
Li Si,contains $ and %,amount $1000 50%
Wang Wu,contains & and *,condition A&B quantity *2"""

        payload = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(special_data.encode('utf-8')).decode('utf-8'),
            "options": {
                "encoding": "utf-8",
                "has_header": True
            }
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=15)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


