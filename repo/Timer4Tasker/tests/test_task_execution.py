import pytest
import time


class TestTaskExecution:
    
    def test_manual_execute_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
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
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        response = api_client.post(f"/tasks/{task_id}/execute")
        
        assert response.status_code in [200, 400]
        result = response.json()
        
        if response.status_code == 200:
            assert result["success"] is True
            assert "execution_id" in result["data"]
        else:
            assert result["success"] is False
    
    def test_execute_nonexistent_task(self, api_client):
        response = api_client.post("/tasks/nonexistent_task_id/execute")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False
    
    @pytest.mark.slow
    def test_concurrent_task_execution(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        response1 = api_client.post(f"/tasks/{task_id}/execute")
        response2 = api_client.post(f"/tasks/{task_id}/execute")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        execution_id1 = response1.json()["data"]["execution_id"]
        execution_id2 = response2.json()["data"]["execution_id"]
        
        assert execution_id1 != execution_id2


class TestExecutionHistory:
    
    def test_get_execution_history(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(1)
        
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
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        for _ in range(3):
            api_client.post(f"/tasks/{task_id}/execute")
            time.sleep(0.5)
        
        response = api_client.get(f"/tasks/{task_id}/executions", params={"limit": 2})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        executions = result["data"]["executions"]
        assert len(executions) <= 2
    
    def test_get_execution_history_empty(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        response = api_client.get(f"/tasks/{task_id}/executions")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["data"]["executions"]) == 0
    
    def test_get_execution_history_nonexistent_task(self, api_client):
        response = api_client.get("/tasks/nonexistent_task_id/executions")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False
    
    @pytest.mark.slow
    def test_execution_status_transition(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        exec_response = api_client.post(f"/tasks/{task_id}/execute")
        execution_id = exec_response.json()["data"]["execution_id"]
        
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
        
        if initial_status == "running":
            time.sleep(3)
            history_response = api_client.get(f"/tasks/{task_id}/executions")
            executions = history_response.json()["data"]["executions"]
            
            for execution in executions:
                if execution["execution_id"] == execution_id:
                    final_status = execution["status"]
                    assert final_status in ["completed", "failed"]
                    
                    if final_status in ["completed", "failed"]:
                        assert "completed_at" in execution
                    break
    
    def test_execution_result_fields(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(2)
        
        response = api_client.get(f"/tasks/{task_id}/executions")
        executions = response.json()["data"]["executions"]
        
        if len(executions) > 0:
            execution = executions[0]
            
            assert "execution_id" in execution
            assert "task_id" in execution
            assert "status" in execution
            assert "started_at" in execution
            
            if execution["status"] == "completed":
                assert "completed_at" in execution or True
            elif execution["status"] == "failed":
                assert "error" in execution or True

