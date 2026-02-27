import pytest
import time


class TestStats:
    
    def test_get_stats(self, api_client):
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
        
        assert isinstance(data["total_tasks"], int)
        assert isinstance(data["active_tasks"], int)
        assert isinstance(data["total_executions"], int)
        assert isinstance(data["successful_executions"], int)
        assert isinstance(data["failed_executions"], int)
        
        assert data["total_tasks"] >= 0
        assert data["active_tasks"] >= 0
        assert data["active_tasks"] <= data["total_tasks"]
        assert data["total_executions"] >= 0
        assert data["successful_executions"] >= 0
        assert data["failed_executions"] >= 0
        assert (data["successful_executions"] + data["failed_executions"]) <= data["total_executions"]
    
    def test_stats_increase_after_task_creation(self, api_client, sample_task_data, cleanup_tasks):
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_total = initial_stats["total_tasks"]
        
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        updated_response = api_client.get("/stats")
        updated_stats = updated_response.json()["data"]
        
        assert updated_stats["total_tasks"] == initial_total + 1
    
    def test_stats_active_tasks_count(self, api_client, sample_task_data, cleanup_tasks):
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_active = initial_stats["active_tasks"]
        
        task_data = sample_task_data["file_cleanup"]
        task_data["enabled"] = True
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        updated_response = api_client.get("/stats")
        updated_stats = updated_response.json()["data"]
        
        assert updated_stats["active_tasks"] == initial_active + 1
        
        api_client.post(f"/tasks/{task_id}/toggle", data={"enabled": False})
        
        final_response = api_client.get("/stats")
        final_stats = final_response.json()["data"]
        
        assert final_stats["active_tasks"] == initial_active
    
    @pytest.mark.slow
    def test_stats_execution_count(self, api_client, sample_task_data, cleanup_tasks):
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_executions = initial_stats["total_executions"]
        
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(1)
        
        updated_response = api_client.get("/stats")
        updated_stats = updated_response.json()["data"]
        
        assert updated_stats["total_executions"] >= initial_executions + 1
    
    def test_stats_after_task_deletion(self, api_client, sample_task_data):
        initial_response = api_client.get("/stats")
        initial_stats = initial_response.json()["data"]
        initial_total = initial_stats["total_tasks"]
        
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        
        after_create_response = api_client.get("/stats")
        after_create_stats = after_create_response.json()["data"]
        assert after_create_stats["total_tasks"] == initial_total + 1
        
        api_client.delete(f"/tasks/{task_id}")
        
        final_response = api_client.get("/stats")
        final_stats = final_response.json()["data"]
        
        assert final_stats["total_tasks"] == initial_total


class TestStatsConsistency:
    
    def test_stats_consistency_with_task_list(self, api_client):
        stats_response = api_client.get("/stats")
        stats = stats_response.json()["data"]
        
        tasks_response = api_client.get("/tasks", params={"page_size": 1000})
        tasks_data = tasks_response.json()["data"]
        
        assert stats["total_tasks"] == tasks_data["total"]
        
        active_count = sum(1 for task in tasks_data["tasks"] if task["enabled"])
        assert stats["active_tasks"] == active_count
    
    @pytest.mark.slow
    def test_stats_real_time_update(self, api_client, sample_task_data, cleanup_tasks):
        operations = []
        
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        stats1 = api_client.get("/stats").json()["data"]
        operations.append(("create", stats1))
        
        api_client.post(f"/tasks/{task_id}/execute")
        time.sleep(1)
        
        stats2 = api_client.get("/stats").json()["data"]
        operations.append(("execute", stats2))
        
        api_client.post(f"/tasks/{task_id}/toggle", data={"enabled": False})
        
        stats3 = api_client.get("/stats").json()["data"]
        operations.append(("disable", stats3))
        
        assert stats2["total_executions"] >= stats1["total_executions"]
        assert stats3["active_tasks"] <= stats2["active_tasks"]


class TestStatsEdgeCases:
    
    def test_stats_with_no_tasks(self, api_client):
        response = api_client.get("/stats")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        data = result["data"]
        for key in ["total_tasks", "active_tasks", "total_executions", 
                    "successful_executions", "failed_executions"]:
            assert key in data
            assert data[key] >= 0
    
    def test_stats_response_format(self, api_client):
        response = api_client.get("/stats")
        
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"
        
        result = response.json()
        
        assert "success" in result
        assert "data" in result
        assert isinstance(result["data"], dict)
        
        required_fields = [
            "total_tasks",
            "active_tasks",
            "total_executions",
            "successful_executions",
            "failed_executions"
        ]
        
        for field in required_fields:
            assert field in result["data"], f"Lack of field: {field}"

