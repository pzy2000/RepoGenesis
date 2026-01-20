"""
测试系统统计相关的 API 接口
"""
import pytest
import time


class TestStats:
    """测试系统统计功能"""
    
    def test_get_stats(self, api_client):
        """测试获取系统统计信息"""
        response = api_client.get("/stats")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        
        data = result["data"]
        assert "total_tasks" in data
        assert "active_tasks" in data
        assert "total_executions" in data
        assert "successful_executions" in data
        assert "failed_executions" in data
        
        # 验证数据类型
        assert isinstance(data["total_tasks"], int)
        assert isinstance(data["active_tasks"], int)
        assert isinstance(data["total_executions"], int)
        assert isinstance(data["successful_executions"], int)
        assert isinstance(data["failed_executions"], int)
        
        # 验证数据合理性
        assert data["total_tasks"] >= 0
        assert data["active_tasks"] >= 0
        assert data["active_tasks"] <= data["total_tasks"]
        assert data["total_executions"] >= 0
        assert data["successful_executions"] >= 0
        assert data["failed_executions"] >= 0
        assert (data["successful_executions"] + data["failed_executions"]) <= data["total_executions"]
    
    def test_stats_increase_after_task_creation(self, api_client, sample_task_data, cleanup_tasks):
        """测试创建任务后统计数据增加"""
        # 获取初始统计
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_total = initial_stats["total_tasks"]
        
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 获取更新后的统计
        updated_response = api_client.get("/stats")
        updated_stats = updated_response.json()["data"]
        
        # 验证任务总数增加
        assert updated_stats["total_tasks"] == initial_total + 1
    
    def test_stats_active_tasks_count(self, api_client, sample_task_data, cleanup_tasks):
        """测试活跃任务统计"""
        # 获取初始统计
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_active = initial_stats["active_tasks"]
        
        # 创建启用的任务
        task_data = sample_task_data["file_cleanup"]
        task_data["enabled"] = True
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 获取更新后的统计
        updated_response = api_client.get("/stats")
        updated_stats = updated_response.json()["data"]
        
        # 验证活跃任务数增加
        assert updated_stats["active_tasks"] == initial_active + 1
        
        # 禁用任务
        api_client.post(f"/tasks/{task_id}/toggle", data={"enabled": False})
        
        # 再次获取统计
        final_response = api_client.get("/stats")
        final_stats = final_response.json()["data"]
        
        # 验证活跃任务数减少
        assert final_stats["active_tasks"] == initial_active
    
    @pytest.mark.slow
    def test_stats_execution_count(self, api_client, sample_task_data, cleanup_tasks):
        """测试执行次数统计"""
        # 获取初始统计
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_executions = initial_stats["total_executions"]
        
        # 创建任务
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 执行任务
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(1)  # 等待执行记录
        
        # 获取更新后的统计
        updated_response = api_client.get("/stats")
        updated_stats = updated_response.json()["data"]
        
        # 验证执行次数增加
        assert updated_stats["total_executions"] >= initial_executions + 1
    
    def test_stats_after_task_deletion(self, api_client, sample_task_data):
        """测试删除任务后统计数据"""
        # 获取初始统计
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_total = initial_stats["total_tasks"]
        
        # 创建任务
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        
        # 验证任务总数增加
        after_create_response = api_client.get("/stats")
        after_create_stats = after_create_response.json()["data"]
        assert after_create_stats["total_tasks"] == initial_total + 1
        
        # 删除任务
        api_client.delete(f"/tasks/{task_id}")
        
        # 获取删除后的统计
        final_response = api_client.get("/stats")
        final_stats = final_response.json()["data"]
        
        # 验证任务总数恢复
        assert final_stats["total_tasks"] == initial_total


class TestStatsConsistency:
    """测试统计数据一致性"""
    
    def test_stats_consistency_with_task_list(self, api_client):
        """测试统计数据与任务列表的一致性"""
        # 获取统计
        stats_response = api_client.get("/stats")
        stats = stats_response.json()["data"]
        
        # 获取任务列表
        tasks_response = api_client.get("/tasks", params={"page_size": 1000})
        tasks_data = tasks_response.json()["data"]
        
        # 验证总任务数一致
        assert stats["total_tasks"] == tasks_data["total"]
        
        # 验证活跃任务数
        active_count = sum(1 for task in tasks_data["tasks"] if task["enabled"])
        assert stats["active_tasks"] == active_count
    
    @pytest.mark.slow
    def test_stats_real_time_update(self, api_client, sample_task_data, cleanup_tasks):
        """测试统计数据实时更新"""
        # 执行一系列操作并验证统计更新
        operations = []
        
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        stats1 = api_client.get("/stats").json()["data"]
        operations.append(("create", stats1))
        
        # 执行任务
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(1)
        
        stats2 = api_client.get("/stats").json()["data"]
        operations.append(("execute", stats2))
        
        # 禁用任务
        api_client.post(f"/tasks/{task_id}/toggle", data={"enabled": False})
        
        stats3 = api_client.get("/stats").json()["data"]
        operations.append(("disable", stats3))
        
        # 验证统计变化
        assert stats2["total_executions"] >= stats1["total_executions"]
        assert stats3["active_tasks"] <= stats2["active_tasks"]


class TestStatsEdgeCases:
    """测试统计功能的边界情况"""
    
    def test_stats_with_no_tasks(self, api_client):
        """测试没有任务时的统计"""
        # 即使没有任务，统计接口也应该正常工作
        response = api_client.get("/stats")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        data = result["data"]
        # 所有计数都应该是非负数
        for key in ["total_tasks", "active_tasks", "total_executions", 
                    "successful_executions", "failed_executions"]:
            assert key in data
            assert data[key] >= 0
    
    def test_stats_response_format(self, api_client):
        """测试统计响应格式"""
        response = api_client.get("/stats")
        
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"
        
        result = response.json()
        
        # 验证响应结构
        assert "success" in result
        assert "data" in result
        assert isinstance(result["data"], dict)
        
        # 验证所有必需字段存在
        required_fields = [
            "total_tasks",
            "active_tasks",
            "total_executions",
            "successful_executions",
            "failed_executions"
        ]
        
        for field in required_fields:
            assert field in result["data"], f"缺少必需字段: {field}"

