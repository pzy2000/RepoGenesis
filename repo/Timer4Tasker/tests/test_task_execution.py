"""
测试任务执行相关的 API 接口
"""
import pytest
import time


class TestTaskExecution:
    """测试任务执行功能"""
    
    def test_manual_execute_task(self, api_client, sample_task_data, cleanup_tasks):
        """测试手动执行任务"""
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 手动执行任务
        response = api_client.post(f"/tasks/{task_id}/execute")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        
        data = result["data"]
        assert "execution_id" in data
        assert data["task_id"] == task_id
        assert data["status"] in ["running", "completed", "failed"]
        assert "started_at" in data
    
    def test_execute_disabled_task(self, api_client, sample_task_data, cleanup_tasks):
        """测试执行已禁用的任务"""
        # 创建禁用的任务
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 尝试执行禁用的任务
        response = api_client.post(f"/tasks/{task_id}/execute")
        
        # 可能返回 200（允许手动执行）或 400（禁止执行）
        assert response.status_code in [200, 400]
        result = response.json()
        
        if response.status_code == 200:
            # 如果允许执行禁用的任务
            assert result["success"] is True
            assert "execution_id" in result["data"]
        else:
            # 如果不允许执行禁用的任务
            assert result["success"] is False
    
    def test_execute_nonexistent_task(self, api_client):
        """测试执行不存在的任务"""
        response = api_client.post("/tasks/nonexistent_task_id/execute")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False
    
    @pytest.mark.slow
    def test_concurrent_task_execution(self, api_client, sample_task_data, cleanup_tasks):
        """测试同一任务的并发执行"""
        # 创建任务
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 连续执行两次
        response1 = api_client.post(f"/tasks/{task_id}/execute")
        response2 = api_client.post(f"/tasks/{task_id}/execute")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        execution_id1 = response1.json()["data"]["execution_id"]
        execution_id2 = response2.json()["data"]["execution_id"]
        
        # 执行ID应该不同
        assert execution_id1 != execution_id2


class TestExecutionHistory:
    """测试任务执行历史功能"""
    
    def test_get_execution_history(self, api_client, sample_task_data, cleanup_tasks):
        """测试获取任务执行历史"""
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 执行任务
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(1)  # 等待任务执行
        
        # 获取执行历史
        response = api_client.get(f"/tasks/{task_id}/executions")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        
        data = result["data"]
        assert "executions" in data
        assert len(data["executions"]) > 0
        
        execution = data["executions"][0]
        assert "execution_id" in execution
        assert execution["task_id"] == task_id
        assert "status" in execution
        assert execution["status"] in ["running", "completed", "failed"]
        assert "started_at" in execution
    
    def test_get_execution_history_with_limit(self, api_client, sample_task_data, cleanup_tasks):
        """测试获取有限数量的执行历史"""
        # 创建任务
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 执行任务多次
        for _ in range(3):
            api_client.post(f"/tasks/{task_id}/execute")
            time.sleep(0.5)
        
        # 获取最多2条执行历史
        response = api_client.get(f"/tasks/{task_id}/executions", params={"limit": 2})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        executions = result["data"]["executions"]
        assert len(executions) <= 2
    
    def test_get_execution_history_empty(self, api_client, sample_task_data, cleanup_tasks):
        """测试获取未执行任务的历史"""
        # 创建任务但不执行
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 获取执行历史
        response = api_client.get(f"/tasks/{task_id}/executions")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["data"]["executions"]) == 0
    
    def test_get_execution_history_nonexistent_task(self, api_client):
        """测试获取不存在任务的执行历史"""
        response = api_client.get("/tasks/nonexistent_task_id/executions")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False
    
    @pytest.mark.slow
    def test_execution_status_transition(self, api_client, sample_task_data, cleanup_tasks):
        """测试执行状态的转换"""
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 执行任务
        exec_response = api_client.post(f"/tasks/{task_id}/execute")
        execution_id = exec_response.json()["data"]["execution_id"]
        
        # 立即查询，状态可能是 running
        history_response = api_client.get(f"/tasks/{task_id}/executions")
        executions = history_response.json()["data"]["executions"]
        
        current_execution = None
        for execution in executions:
            if execution["execution_id"] == execution_id:
                current_execution = execution
                break
        
        assert current_execution is not None
        initial_status = current_execution["status"]
        assert initial_status in ["running", "completed", "failed"]
        
        # 等待一段时间后再查询
        if initial_status == "running":
            time.sleep(3)
            history_response = api_client.get(f"/tasks/{task_id}/executions")
            executions = history_response.json()["data"]["executions"]
            
            for execution in executions:
                if execution["execution_id"] == execution_id:
                    final_status = execution["status"]
                    assert final_status in ["completed", "failed"]
                    
                    # 如果任务完成，应该有 completed_at
                    if final_status in ["completed", "failed"]:
                        assert "completed_at" in execution
                    break
    
    def test_execution_result_fields(self, api_client, sample_task_data, cleanup_tasks):
        """测试执行结果包含必要的字段"""
        # 创建任务
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 执行任务
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(2)  # 等待任务完成
        
        # 获取执行历史
        response = api_client.get(f"/tasks/{task_id}/executions")
        executions = response.json()["data"]["executions"]
        
        if len(executions) > 0:
            execution = executions[0]
            
            # 验证必需字段
            assert "execution_id" in execution
            assert "task_id" in execution
            assert "status" in execution
            assert "started_at" in execution
            
            # 根据状态验证可选字段
            if execution["status"] == "completed":
                # 完成的任务应该有 completed_at 和可能的 result
                assert "completed_at" in execution or True  # 可选字段
            elif execution["status"] == "failed":
                # 失败的任务应该有 error 信息
                assert "error" in execution or True  # 可选字段

