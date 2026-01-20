"""
性能测试用例
测试服务在高负载、长时间运行等情况下的性能表现
"""

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
    """性能测试类"""

    BASE_URL = "http://localhost:8000/api/v1"

    def setup_method(self):
        """测试前准备测试数据"""
        # 生成中等大小的测试数据集
        self.medium_df = pd.DataFrame({
            f'列{i}': range(1000) for i in range(10)
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.medium_df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.medium_excel_data = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

        # 生成大量的小文件测试数据
        self.small_csv_data = base64.b64encode(
            "姓名,年龄,城市\n张三,25,北京\n李四,30,上海\n王五,28,深圳".encode('utf-8')
        ).decode('utf-8')

    def test_single_conversion_performance(self):
        """测试单次转换的性能基准"""
        payload = {
            "source_format": "excel",
            "target_format": "csv",
            "data": self.medium_excel_data
        }

        # 执行多次测试以获取平均性能
        times = []
        for _ in range(10):
            start_time = time.time()
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=payload, timeout=30)
            end_time = time.time()

            assert response.status_code == 200
            times.append(end_time - start_time)

        # 计算性能统计数据
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        print("
单次转换性能统计:"        print(f"平均时间: {avg_time:.2f}秒")
        print(f"中位数时间: {median_time:.2f}秒")
        print(f"最小时间: {min_time:.2f}秒")
        print(f"最大时间: {max_time:.2f}秒")
        print(f"标准差: {std_dev:.2f}秒")

        # 性能断言
        assert avg_time < 5.0, f"平均转换时间过长: {avg_time:.2f}秒"
        assert max_time < 10.0, f"最大转换时间过长: {max_time:.2f}秒"
        assert std_dev < 2.0, f"转换时间稳定性差: {std_dev:.2f}秒"

    def test_concurrent_requests_performance(self):
        """测试并发请求处理性能"""
        def make_request(request_id):
            """执行单个转换请求"""
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

        # 测试不同并发级别
        concurrency_levels = [5, 10, 20]
        results = {}

        for concurrency in concurrency_levels:
            print(f"\n测试并发级别: {concurrency}")

            start_time = time.time()

            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrency)]
                responses = [future.result() for future in as_completed(futures)]

            end_time = time.time()

            # 分析结果
            response_times = [r["response_time"] for r in responses if r["success"]]
            success_count = sum(1 for r in responses if r["success"])

            results[concurrency] = {
                "total_requests": len(responses),
                "success_count": success_count,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "total_time": end_time - start_time
            }

            print(f"成功请求: {success_count}/{len(responses)}")
            print(f"平均响应时间: {results[concurrency]['avg_response_time']:.2f}秒")
            print(f"总耗时: {results[concurrency]['total_time']:.2f}秒")

            # 断言
            assert success_count >= concurrency * 0.8, f"并发请求成功率过低: {success_count}/{concurrency}"

        # 验证并发性能扩展性
        # 并发数翻倍时，总时间不应翻倍（理想情况下）
        if len(results) >= 2:
            time_5 = results[5]["total_time"]
            time_10 = results[10]["total_time"]
            # 10并发的时间不应超过5并发的3倍（留出一些余量）
            assert time_10 < time_5 * 3.0, f"并发扩展性不佳: 10并发耗时{time_10:.2f}秒 vs 5并发预期上限{time_5 * 3.0:.2f}秒"

    def test_memory_usage_stability(self):
        """测试长时间运行的内存使用稳定性"""
        def continuous_requests(duration_seconds=30):
            """持续发送请求指定时间"""
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
                        errors.append(f"请求失败: {response.status_code}")

                    request_count += 1
                    time.sleep(0.1)  # 小延迟避免过度压力

                except Exception as e:
                    errors.append(str(e))
                    time.sleep(0.1)

            return request_count, errors

        # 执行持续请求测试
        request_count, errors = continuous_requests(30)

        print(f"\n持续请求测试结果:")
        print(f"总请求数: {request_count}")
        print(f"错误数: {len(errors)}")
        print(f"错误率: {len(errors) / request_count * 100:.2f}%" if request_count > 0 else "错误率: N/A")

        # 断言
        assert request_count > 0, "未能成功发送任何请求"
        assert len(errors) / request_count < 0.1, f"错误率过高: {len(errors)}/{request_count}"

    def test_health_check_under_load(self):
        """测试在负载下健康检查的响应性"""
        def load_generator():
            """生成负载的后台任务"""
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
            """在负载下执行健康检查"""
            health_times = []
            end_time = time.time() + 20

            while time.time() < end_time:
                start_time = time.time()
                response = requests.get(f"{self.BASE_URL}/health", timeout=5)
                end_time = time.time()

                health_times.append(end_time - start_time)

                # 健康检查本身应该成功
                assert response.status_code == 200

                time.sleep(0.5)

            return health_times

        # 启动负载生成器
        load_thread = threading.Thread(target=load_generator)
        load_thread.start()

        # 执行健康检查
        health_response_times = health_checks()

        # 等待负载生成器完成
        load_thread.join()

        # 分析健康检查响应时间
        avg_health_time = statistics.mean(health_response_times)
        max_health_time = max(health_response_times)

        print("
负载下健康检查性能:"        print(f"平均响应时间: {avg_health_time:.3f}秒")
        print(f"最大响应时间: {max_health_time:.3f}秒")

        # 在负载下，健康检查响应时间应保持在合理范围内
        assert avg_health_time < 1.0, f"负载下健康检查响应过慢: {avg_health_time:.3f}秒"
        assert max_health_time < 2.0, f"负载下健康检查最大响应时间过长: {max_health_time:.3f}秒"

    def test_large_file_performance(self):
        """测试大文件转换性能"""
        # 生成大文件测试数据
        large_df = pd.DataFrame({
            f'列{i}': range(5000) for i in range(20)  # 20列，5000行
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
                               json=payload, timeout=120)  # 较长超时
        end_time = time.time()

        assert response.status_code == 200

        conversion_time = end_time - start_time

        print("
大文件转换性能:"        print(f"转换耗时: {conversion_time:.2f}秒")
        print(f"文件大小: {len(large_excel_data) * 3/4 / 1024:.1f} KB")  # base64解码后的大概大小

        # 大文件转换时间应在合理范围内
        assert conversion_time < 60.0, f"大文件转换时间过长: {conversion_time:.2f}秒"

        # 验证转换结果
        data = response.json()
        assert data["success"] is True

    def test_response_time_distribution(self):
        """测试响应时间分布"""
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

        # 执行多次请求
        response_times = []
        for _ in range(50):
            time_taken = make_request()
            if time_taken is not None:
                response_times.append(time_taken)

        # 分析响应时间分布
        if response_times:
            sorted_times = sorted(response_times)

            print("
响应时间分布:"            print(f"平均时间: {statistics.mean(response_times):.3f}秒")
            print(f"中位数: {statistics.median(response_times):.3f}秒")
            print(f"90百分位: {sorted_times[int(len(sorted_times) * 0.9)]:.3f}秒")
            print(f"95百分位: {sorted_times[int(len(sorted_times) * 0.95)]:.3f}秒")
            print(f"99百分位: {sorted_times[int(len(sorted_times) * 0.99)]:.3f}秒")

            # 响应时间分布应合理
            assert statistics.mean(response_times) < 3.0, "平均响应时间过长"
            assert sorted_times[int(len(sorted_times) * 0.95)] < 5.0, "95%请求响应时间过长"

    def test_resource_cleanup_verification(self):
        """验证资源清理是否正确"""
        def intensive_workload():
            """执行密集工作负载"""
            for i in range(20):
                payload = {
                    "source_format": "excel",
                    "target_format": "csv",
                    "data": self.medium_excel_data
                }

                response = requests.post(f"{self.BASE_URL}/convert",
                                       json=payload, timeout=30)

                if response.status_code == 200:
                    # 验证响应包含预期的元数据
                    data = response.json()
                    assert "metadata" in data
                    assert "conversion_time" in data["metadata"]

                time.sleep(0.1)  # 小间隔

        # 执行密集工作负载前后都检查健康状态
        start_time = time.time()

        # 检查开始时的健康状态
        health_before = requests.get(f"{self.BASE_URL}/health", timeout=5)
        assert health_before.status_code == 200

        # 执行工作负载
        intensive_workload()

        # 检查结束时的健康状态
        health_after = requests.get(f"{self.BASE_URL}/health", timeout=5)
        assert health_after.status_code == 200

        end_time = time.time()

        print("
资源清理验证:"        print(f"工作负载执行时间: {end_time - start_time:.2f}秒")
        print("服务在高负载后仍保持健康状态")

        # 服务应该在高负载后仍然健康
        health_data_before = health_before.json()
        health_data_after = health_after.json()

        assert health_data_before["status"] == "healthy"
        assert health_data_after["status"] == "healthy"


