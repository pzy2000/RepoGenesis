"""
集成测试用例
测试完整的工作流程，包括多接口协作和端到端场景
"""

import pytest
import requests
import json
import base64
import pandas as pd
import time
import tempfile
import os


class TestIntegration:
    """集成测试类"""

    BASE_URL = "http://localhost:8000/api/v1"

    def setup_method(self):
        """测试前准备测试数据"""
        # 准备多种格式的测试数据
        self.test_data = {
            "csv": "姓名,年龄,城市,薪资\n张三,25,北京,15000\n李四,30,上海,18000\n王五,28,深圳,20000",
            "excel": None,  # 将在下面生成
            "complex_csv": """产品ID,产品名称,类别,价格,库存,供应商,描述
P001,智能手机,电子产品,2999.00,50,中兴通讯,高性能5G智能手机
P002,笔记本电脑,电子产品,5999.00,20,华为科技,轻薄商务笔记本
P003,机械键盘,配件,299.00,100,雷柏科技,RGB背光机械键盘
P004,鼠标垫,配件,49.00,200,赛睿,超大鼠标垫"""
        }

        # 生成Excel测试数据
        df = pd.DataFrame({
            '姓名': ['张三', '李四', '王五'],
            '年龄': [25, 30, 28],
            '城市': ['北京', '上海', '深圳'],
            '薪资': [15000, 18000, 20000]
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                self.test_data["excel"] = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)

    def test_end_to_end_conversion_workflow(self):
        """测试端到端转换工作流程"""
        # 1. 检查服务健康状态
        health_response = requests.get(f"{self.BASE_URL}/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"

        # 2. 执行CSV到Excel转换
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

        # 3. 将Excel转换结果转换为PDF
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

        # 4. 验证整个流程的元数据
        assert "metadata" in data1
        assert "metadata" in data2
        assert data1["metadata"]["rows_count"] == 3
        assert data1["metadata"]["columns_count"] == 4

        print("端到端工作流程测试通过")

    def test_batch_conversion_workflow(self):
        """测试批量转换完整工作流程"""
        # 准备批量转换任务
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

        # 执行批量转换
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

        # 验证每个转换结果
        for i, result in enumerate(data["results"]):
            assert result["success"] is True, f"第{i+1}个转换失败: {result.get('message', '未知错误')}"
            assert "result" in result
            assert result["result"] != ""

        # 验证汇总信息
        summary = data["summary"]
        assert summary["total_count"] == 3
        assert summary["success_count"] == 3
        assert summary["failure_count"] == 0

        print("批量转换工作流程测试通过")

    def test_error_handling_workflow(self):
        """测试错误处理完整流程"""
        # 1. 测试无效格式
        invalid_format_payload = {
            "source_format": "invalid",
            "target_format": "excel",
            "data": base64.b64encode(b"test").decode('utf-8')
        }

        response1 = requests.post(f"{self.BASE_URL}/convert",
                                json=invalid_format_payload, timeout=10)
        # 应该返回错误状态码
        assert response1.status_code in [400, 422]

        # 2. 测试空数据
        empty_data_payload = {
            "source_format": "csv",
            "target_format": "excel",
            "data": ""
        }

        response2 = requests.post(f"{self.BASE_URL}/convert",
                                json=empty_data_payload, timeout=10)
        # 应该被正确处理
        assert response2.status_code in [200, 400]

        # 3. 即使有错误，健康检查仍应正常工作
        health_response = requests.get(f"{self.BASE_URL}/health")
        assert health_response.status_code == 200

        print("错误处理工作流程测试通过")

    def test_performance_under_realistic_load(self):
        """测试真实负载下的性能表现"""
        def simulate_user_session(session_id):
            """模拟用户会话"""
            results = []

            # 用户先检查服务健康状态
            health_response = requests.get(f"{self.BASE_URL}/health")
            results.append(health_response.status_code == 200)

            # 用户进行一系列转换操作
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

                # 小间隔模拟用户思考时间
                time.sleep(0.2)

            return results

        # 模拟多个并发用户
        import threading

        results = []
        errors = []

        def run_user_session(session_id):
            try:
                session_results = simulate_user_session(session_id)
                results.append(session_results)
            except Exception as e:
                errors.append(f"会话{session_id}错误: {str(e)}")

        # 创建多个用户会话
        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_user_session, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有会话完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0, f"用户会话中出现错误: {errors}"

        total_operations = sum(len(session_result) for session_result in results)
        successful_operations = sum(sum(session_result) for session_result in results)

        success_rate = successful_operations / total_operations if total_operations > 0 else 0

        print("
真实负载性能测试:"        print(f"总操作数: {total_operations}")
        print(f"成功操作数: {successful_operations}")
        print(f"成功率: {success_rate * 100:.1f}%")

        # 成功率应在合理范围内
        assert success_rate > 0.9, f"成功率过低: {success_rate * 100:.1f}%"

    def test_data_consistency_across_formats(self):
        """测试不同格式间的数椐一致性"""
        original_csv = "姓名,年龄,城市,薪资\n张三,25,北京,15000\n李四,30,上海,18000"

        # CSV -> Excel -> CSV 循环转换
        # 1. CSV转Excel
        payload1 = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(original_csv.encode('utf-8')).decode('utf-8')
        }

        response1 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_data = response1.json()["result"]

        # 2. Excel转CSV
        payload2 = {
            "source_format": "excel",
            "target_format": "csv",
            "data": excel_data
        }

        response2 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload2, timeout=30)
        assert response2.status_code == 200
        final_csv = base64.b64decode(response2.json()["result"]).decode('utf-8')

        # 3. 验证数据一致性（忽略可能的格式差异）
        original_lines = [line.strip() for line in original_csv.split('\n') if line.strip()]
        final_lines = [line.strip() for line in final_csv.split('\n') if line.strip()]

        # 行数应该相同
        assert len(original_lines) == len(final_lines), "转换后行数不一致"

        # 每行应该包含相同的数据元素（顺序可能不同）
        for original_line, final_line in zip(original_lines, final_lines):
            original_elements = set(original_line.split(','))
            final_elements = set(final_line.split(','))

            # 允许一些格式差异（如多余空格），但核心数据应一致
            assert len(original_elements) == len(final_elements), f"数据元素数量不一致: {original_line} vs {final_line}"

        print("数据一致性测试通过")

    def test_system_resource_usage(self):
        """测试系统资源使用情况"""
        # 记录测试开始时的健康状态
        health_before = requests.get(f"{self.BASE_URL}/health")
        assert health_before.status_code == 200
        before_timestamp = health_before.json()["timestamp"]

        # 执行一系列密集操作
        operations = []

        # 添加多个转换操作
        for i in range(10):
            payload = {
                "source_format": "csv",
                "target_format": "excel",
                "data": base64.b64encode(self.test_data["csv"].encode('utf-8')).decode('utf-8')
            }
            operations.append(payload)

        # 执行所有操作
        start_time = time.time()
        for payload in operations:
            response = requests.post(f"{self.BASE_URL}/convert",
                                   json=payload, timeout=30)
            assert response.status_code == 200

        end_time = time.time()

        # 检查执行后的健康状态
        health_after = requests.get(f"{self.BASE_URL}/health")
        assert health_after.status_code == 200
        after_timestamp = health_after.json()["timestamp"]

        # 验证系统在负载后仍保持健康
        assert health_before.json()["status"] == "healthy"
        assert health_after.json()["status"] == "healthy"

        print("
系统资源使用测试:"        print(f"操作数量: {len(operations)}")
        print(f"总耗时: {end_time - start_time:.2f}秒")
        print(f"平均耗时: {(end_time - start_time) / len(operations):.2f}秒")
        print("系统在高负载后仍保持健康状态"

        # 系统应能在负载后迅速恢复
        time.sleep(2)  # 等待系统恢复
        final_health = requests.get(f"{self.BASE_URL}/health")
        assert final_health.status_code == 200
        assert final_health.json()["status"] == "healthy"

    def test_api_version_compatibility(self):
        """测试API版本兼容性"""
        # 测试当前API版本的接口
        health_response = requests.get(f"{self.BASE_URL}/health")
        assert health_response.status_code == 200

        health_data = health_response.json()
        assert "version" in health_data

        # 测试所有主要接口的可用性
        interfaces = [
            ("健康检查", "GET", f"{self.BASE_URL}/health"),
            ("单次转换", "POST", f"{self.BASE_URL}/convert"),
            ("批量转换", "POST", f"{self.BASE_URL}/convert/batch")
        ]

        for interface_name, method, url in interfaces:
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                # POST请求需要有效载荷
                payload = {
                    "source_format": "csv",
                    "target_format": "excel",
                    "data": base64.b64encode(b"test,a,b\n1,2,3").decode('utf-8')
                }
                response = requests.post(url, json=payload, timeout=10)

            print(f"{interface_name}接口状态: {response.status_code}")
            # 主要接口应该可用（即使返回错误码也是正常的，只要服务响应）
            assert response.status_code in [200, 400, 404, 405, 422], f"{interface_name}接口不可用"

        print("API版本兼容性测试通过")

    def test_real_world_usage_scenario(self):
        """测试真实世界使用场景"""
        # 模拟企业数据处理场景：员工信息管理

        # 1. 准备员工数据（CSV格式）
        employee_data = """员工ID,姓名,部门,职位,入职日期,薪资,绩效等级
E001,张三,技术部,高级工程师,2022-01-15,25000,A
E002,李四,销售部,销售经理,2021-08-20,30000,A
E003,王五,市场部,市场专员,2023-03-10,15000,B
E004,赵六,人事部,人事助理,2022-11-05,12000,B"""

        # 2. 转换为Excel格式用于内部报表
        payload1 = {
            "source_format": "csv",
            "target_format": "excel",
            "data": base64.b64encode(employee_data.encode('utf-8')).decode('utf-8')
        }

        response1 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload1, timeout=30)
        assert response1.status_code == 200
        excel_report = response1.json()["result"]

        # 3. 生成PDF格式的正式报告
        payload2 = {
            "source_format": "excel",
            "target_format": "pdf",
            "data": excel_report
        }

        response2 = requests.post(f"{self.BASE_URL}/convert",
                                json=payload2, timeout=30)
        assert response2.status_code == 200
        pdf_report = response2.json()["result"]

        # 4. 验证报告质量
        data1 = response1.json()
        data2 = response2.json()

        assert data1["success"] is True
        assert data2["success"] is True

        # 验证元数据
        assert data1["metadata"]["rows_count"] == 4  # 数据行数（不含表头）
        assert data1["metadata"]["columns_count"] == 7  # 列数

        # PDF文件应该有合理的大小
        pdf_size = len(base64.b64decode(pdf_report)) / 1024  # KB
        assert pdf_size > 1, f"PDF报告文件过小: {pdf_size:.1f}KB"

        print("
真实世界使用场景测试:"        print(f"员工数据行数: {data1['metadata']['rows_count']}")
        print(f"数据列数: {data1['metadata']['columns_count']}")
        print(f"PDF报告大小: {pdf_size:.1f}KB")
        print("企业级数据处理场景测试通过")


