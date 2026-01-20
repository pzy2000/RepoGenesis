"""
单次格式转换接口测试用例
测试各种数据格式转换功能，包括Excel、CSV、PDF之间的互相转换
"""

import pytest
import requests
import json
import base64
import pandas as pd
import io
import os
import tempfile


class TestConvertEndpoint:
    """单次转换接口测试类"""

    BASE_URL = "http://localhost:8000/api/v1"

    # 测试数据样本
    SAMPLE_CSV_DATA = """姓名,年龄,城市,薪资
张三,25,北京,15000
李四,30,上海,18000
王五,28,深圳,20000
赵六,35,广州,16000"""

    SAMPLE_EXCEL_DATA = None  # 将在setup中生成

    def setup_method(self):
        """测试前准备工作"""
        # 生成Excel测试数据
        df = pd.DataFrame({
            '姓名': ['张三', '李四', '王五', '赵六'],
            '年龄': [25, 30, 28, 35],
            '城市': ['北京', '上海', '深圳', '广州'],
            '薪资': [15000, 18000, 20000, 16000]
        })

        # 保存到临时文件然后读取为base64
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.SAMPLE_EXCEL_DATA = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_csv_to_excel_conversion(self):
        """测试CSV转Excel格式转换"""
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

        # 验证元数据
        assert "metadata" in data
        assert data["metadata"]["source_size"] > 0
        assert data["metadata"]["target_size"] > 0
        assert data["metadata"]["conversion_time"] > 0
        assert data["metadata"]["rows_count"] == 4
        assert data["metadata"]["columns_count"] == 4

    def test_excel_to_csv_conversion(self):
        """测试Excel转CSV格式转换"""
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

        # 解码并验证转换结果
        result_data = base64.b64decode(data["result"]).decode('utf-8')

        # 验证CSV内容
        lines = result_data.strip().split('\n')
        assert len(lines) >= 2  # 至少包含表头和一行数据

        # 验证表头
        headers = lines[0].split(',')
        assert "姓名" in headers
        assert "年龄" in headers
        assert "城市" in headers
        assert "薪资" in headers

    def test_excel_to_pdf_conversion(self):
        """测试Excel转PDF格式转换"""
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

        # PDF文件应该是二进制数据，base64编码后长度应该合理
        result_data = base64.b64decode(data["result"])
        assert len(result_data) > 1000  # PDF文件通常较大

    def test_csv_to_pdf_conversion(self):
        """测试CSV转PDF格式转换"""
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

        # 验证PDF结果
        result_data = base64.b64decode(data["result"])
        assert len(result_data) > 1000  # PDF文件应该有一定大小

    def test_invalid_format_conversion(self):
        """测试无效格式转换请求"""
        payload = {
            "source_format": "invalid",
            "target_format": "excel",
            "data": base64.b64encode(b"test data").decode('utf-8')
        }

        response = requests.post(f"{self.BASE_URL}/convert",
                               json=payload, timeout=10)

        # 应该返回错误状态
        assert response.status_code in [400, 422]  # 错误的请求格式或不支持的格式

    def test_empty_data_conversion(self):
        """测试空数据转换请求"""
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

        # 应该返回错误或处理空数据
        assert response.status_code in [200, 400]

    def test_large_file_conversion(self):
        """测试大文件转换（性能测试）"""
        # 生成较大的测试数据
        large_data = pd.DataFrame({
            f'列{i}': range(1000) for i in range(20)
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

        # 大文件转换时间应在合理范围内（视具体实现而定）
        assert conversion_time < 30.0  # 假设30秒内完成

        data = response.json()
        assert data["success"] is True

    @pytest.mark.parametrize("encoding", ["utf-8", "gbk", "utf-16"])
    def test_different_encodings(self, encoding):
        """测试不同编码格式的处理"""
        test_data = "姓名,年龄\n张三,25\n李四,30"

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

            # 某些编码可能不支持，取决于服务实现
            assert response.status_code in [200, 400, 422]

        except UnicodeEncodeError:
            # 某些编码可能不支持中文字符，这是正常的
            pytest.skip(f"编码 {encoding} 不支持中文字符")

    def test_conversion_with_special_characters(self):
        """测试包含特殊字符的数据转换"""
        special_data = """姓名,描述,符号
张三,包含@符号和#井号,北京@上海#深圳
李四,包含$美元和%百分比,金额$1000 占比50%
王五,包含&和号和*星号,条件A&B 数量*2"""

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


