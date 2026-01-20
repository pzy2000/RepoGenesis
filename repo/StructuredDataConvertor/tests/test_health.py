"""
健康检查接口测试用例
测试服务健康检查功能的正确性和可靠性
"""

import pytest
import requests
import json
import time
from datetime import datetime, timedelta


class TestHealthEndpoint:
    """健康检查接口测试类"""

    BASE_URL = "http://localhost:8000/api/v1"

    def test_health_endpoint_available(self):
        """测试健康检查接口可用性"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "timestamp" in data
            assert "version" in data

            # 验证状态值
            assert data["status"] in ["healthy", "unhealthy"]

            # 验证时间戳格式
            datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))

        except requests.exceptions.ConnectionError:
            pytest.fail("无法连接到服务，请确保服务已启动")

    def test_health_response_format(self):
        """测试健康检查响应格式"""
        response = requests.get(f"{self.BASE_URL}/health")
        data = response.json()

        # 验证必需字段
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data, f"响应中缺少必需字段: {field}"

        # 验证字段类型
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["version"], str)

    def test_health_endpoint_performance(self):
        """测试健康检查接口性能"""
        start_time = time.time()

        response = requests.get(f"{self.BASE_URL}/health")

        end_time = time.time()
        response_time = end_time - start_time

        # 响应时间应小于1秒
        assert response_time < 1.0, f"健康检查响应时间过长: {response_time:.2f}秒"

        # 响应状态码应为200
        assert response.status_code == 200

    def test_health_endpoint_concurrent_requests(self):
        """测试健康检查接口并发请求处理"""
        import threading

        results = []
        errors = []

        def make_request():
            try:
                response = requests.get(f"{self.BASE_URL}/health", timeout=5)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # 创建10个并发请求
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有请求都成功
        assert len(errors) == 0, f"并发请求中出现错误: {errors}"
        assert len(results) == 10
        assert all(status == 200 for status in results)

    def test_health_endpoint_headers(self):
        """测试健康检查接口响应头"""
        response = requests.get(f"{self.BASE_URL}/health")

        # 验证响应头
        assert response.headers["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in response.headers or "*" in response.headers.get("Access-Control-Allow-Origin", "")

    @pytest.mark.parametrize("invalid_method", ["POST", "PUT", "DELETE"])
    def test_health_endpoint_invalid_methods(self, invalid_method):
        """测试健康检查接口对无效HTTP方法的处理"""
        response = requests.request(invalid_method, f"{self.BASE_URL}/health")

        # 健康检查接口通常只接受GET请求
        # 这里我们测试服务是否正确处理了其他HTTP方法
        # 实际的行为取决于服务的实现
        assert response.status_code in [200, 405]  # 200表示接受，405表示方法不允许

    def test_health_endpoint_with_query_params(self):
        """测试健康检查接口对查询参数的处理"""
        # 健康检查接口通常不需要查询参数，但应该能够正确处理
        response = requests.get(f"{self.BASE_URL}/health?param=test&debug=1")

        # 应该仍然返回正常的健康检查响应
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


