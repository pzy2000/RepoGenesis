"""
批量格式转换接口测试用例
测试批量数据格式转换功能，包括并发处理和错误处理
"""

import pytest
import requests
import json
import base64
import pandas as pd
import time
import tempfile
import os


class TestConvertBatchEndpoint:
    """批量转换接口测试类"""

    BASE_URL = "http://localhost:8000/api/v1"

    def setup_method(self):
        """测试前准备工作"""
        # 准备多个测试数据集
        self.test_datasets = []

        # 数据集1：CSV格式
        csv_data = "姓名,年龄,城市\n张三,25,北京\n李四,30,上海"
        self.test_datasets.append({
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
        })

        # 数据集2：Excel格式
        df = pd.DataFrame({
            '产品名': ['产品A', '产品B', '产品C'],
            '价格': [100, 200, 300],
            '库存': [50, 30, 20]
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

        # 数据集3：另一个CSV数据集
        csv_data2 = "部门,人数,预算\n技术部,10,100000\n销售部,8,80000\n市场部,5,50000"
        self.test_datasets.append({
            "source_format": "csv",
            "target_format": "pdf",
            "data": base64.b64encode(csv_data2.encode('utf-8')).decode('utf-8')
        })

    def test_batch_conversion_sequential(self):
        """测试批量转换（顺序处理）"""
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

        # 验证结果数量
        assert len(data["results"]) == len(self.test_datasets)

        # 验证汇总信息
        summary = data["summary"]
        assert summary["total_count"] == len(self.test_datasets)
        assert summary["success_count"] >= 0  # 可能有部分失败
        assert summary["failure_count"] >= 0
        assert summary["total_count"] == summary["success_count"] + summary["failure_count"]
        assert summary["total_time"] > 0

        # 验证处理时间合理
        assert end_time - start_time < 45.0  # 假设45秒内完成

    def test_batch_conversion_parallel(self):
        """测试批量转换（并行处理）"""
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

        # 并行处理应该更快（或至少不比顺序处理慢太多）
        parallel_time = end_time - start_time

        # 执行顺序处理作为对比
        sequential_payload = {
            "conversions": self.test_datasets,
            "parallel": False
        }
        seq_start = time.time()
        seq_response = requests.post(f"{self.BASE_URL}/convert/batch",
                                   json=sequential_payload, timeout=60)
        seq_end = time.time()

        sequential_time = seq_end - seq_start

        # 并行处理的时间应该合理（可能更快或相近）
        assert parallel_time <= sequential_time + 5.0  # 允许一些额外开销

    def test_batch_conversion_with_failures(self):
        """测试包含失败任务的批量转换"""
        # 包含一个无效的转换任务
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
        assert data["success"] is True  # 批量操作本身成功，即使有部分任务失败

        # 验证结果
        assert len(data["results"]) == len(test_datasets_with_failure)

        # 验证汇总信息
        summary = data["summary"]
        assert summary["total_count"] == len(test_datasets_with_failure)
        assert summary["success_count"] >= 0
        assert summary["failure_count"] > 0  # 应该有失败的任务

    def test_batch_conversion_empty_list(self):
        """测试空任务列表的批量转换"""
        payload = {
            "conversions": [],
            "parallel": False
        }

        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=10)

        # 空任务列表应该被正确处理
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", {})
            assert summary.get("total_count", 0) == 0

    def test_batch_conversion_large_dataset(self):
        """测试大数据集的批量转换"""
        # 生成较大的数据集
        large_df = pd.DataFrame({
            f'列{i}': range(100) for i in range(50)  # 50列，100行
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                large_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

        # 创建多个大文件的转换任务
        large_datasets = []
        for i in range(3):  # 3个大文件
            large_datasets.append({
                "source_format": "excel",
                "target_format": "csv",
                "data": large_excel_data
            })

        payload = {
            "conversions": large_datasets,
            "parallel": True  # 使用并行处理来加速
        }

        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/convert/batch",
                               json=payload, timeout=120)  # 较长的超时时间
        end_time = time.time()

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # 大数据集处理时间应该合理
        processing_time = end_time - start_time
        assert processing_time < 90.0  # 假设90秒内完成

        # 验证所有任务都成功
        summary = data["summary"]
        assert summary["success_count"] == len(large_datasets)

    def test_batch_conversion_mixed_formats(self):
        """测试混合格式的批量转换"""
        mixed_datasets = [
            {
                "source_format": "csv",
                "target_format": "excel",
                "data": base64.b64encode("a,b\n1,2".encode('utf-8')).decode('utf-8')
            },
            {
                "source_format": "excel",
                "target_format": "pdf",
                "data": self.test_datasets[1]["data"]  # 使用之前准备的Excel数据
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

        # 验证每个转换结果
        for i, result in enumerate(data["results"]):
            assert "success" in result
            assert "message" in result
            if result["success"]:
                assert "result" in result
                assert result["result"] != ""

    def test_batch_conversion_performance_comparison(self):
        """测试批量转换与单次转换的性能对比"""
        # 准备测试数据
        test_data = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode("a,b,c\n1,2,3\n4,5,6".encode('utf-8')).decode('utf-8')
        }

        # 测试单次转换时间
        single_start = time.time()
        for _ in range(3):
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=test_data, timeout=30)
            assert response.status_code == 200
        single_end = time.time()
        single_avg_time = (single_end - single_start) / 3

        # 测试批量转换时间
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

        # 批量转换的总时间应该与单次转换相当或稍长（由于批量开销）
        # 但不应该显著慢于单次转换的总时间
        assert batch_time <= single_avg_time * 4  # 允许一些额外开销

        # 批量转换应该成功完成所有任务
        assert summary["success_count"] == 3


