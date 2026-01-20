import pytest
import time


class TestTaskCreation:
    
    def test_create_file_cleanup_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201, f"Init task failed: {response.text}"
        
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        
        data = result["data"]
        assert "task_id" in data
        assert data["name"] == task_data["name"]
        assert data["task_type"] == task_data["task_type"]
        assert data["schedule"] == task_data["schedule"]
        assert data["enabled"] is True
        assert "created_at" in data
        
        cleanup_tasks.append(data["task_id"])
    
    def test_create_data_summary_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["data_summary"]
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["task_type"] == "data_summary"
        
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_create_data_backup_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["data_backup"]
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["task_type"] == "data_backup"
        assert result["data"]["enabled"] is False
        
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_create_task_with_missing_required_fields(self, api_client):
        invalid_data = {
            "name": "Test Task"
        }
        response = api_client.post("/tasks", data=invalid_data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
    
    def test_create_task_with_invalid_task_type(self, api_client):
        invalid_data = {
            "name": "Test Task",
            "task_type": "invalid_type",
            "schedule": "0 0 * * *"
        }
        response = api_client.post("/tasks", data=invalid_data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
    
    def test_create_task_with_invalid_cron(self, api_client):
        invalid_data = {
            "name": "Test Task",
            "task_type": "file_cleanup",
            "schedule": "invalid cron"
        }
        response = api_client.post("/tasks", data=invalid_data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False


class TestTaskRetrieval:
    
    def test_get_all_tasks(self, api_client, sample_task_data, cleanup_tasks):
        for task_type, task_data in sample_task_data.items():
            response = api_client.post("/tasks", data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()["data"]["task_id"])
        
        response = api_client.get("/tasks")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        
        data = result["data"]
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["tasks"]) > 0
    
    def test_get_tasks_with_filter_by_type(self, api_client, sample_task_data, cleanup_tasks):
        for task_type, task_data in sample_task_data.items():
            response = api_client.post("/tasks", data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()["data"]["task_id"])
        
        response = api_client.get("/tasks", params={"task_type": "file_cleanup"})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        tasks = result["data"]["tasks"]
        for task in tasks:
            assert task["task_type"] == "file_cleanup"
    
    def test_get_tasks_with_filter_by_enabled(self, api_client, sample_task_data, cleanup_tasks):
        for task_type, task_data in sample_task_data.items():
            response = api_client.post("/tasks", data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()["data"]["task_id"])
        
        response = api_client.get("/tasks", params={"enabled": True})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        tasks = result["data"]["tasks"]
        for task in tasks:
            assert task["enabled"] is True
    
    def test_get_tasks_with_pagination(self, api_client):
        response = api_client.get("/tasks", params={"page": 1, "page_size": 5})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        data = result["data"]
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["tasks"]) <= 5
    
    def test_get_task_by_id(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        assert create_response.status_code == 201
        
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        response = api_client.get(f"/tasks/{task_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        data = result["data"]
        assert data["task_id"] == task_id
        assert data["name"] == task_data["name"]
        assert data["description"] == task_data["description"]
        assert data["task_type"] == task_data["task_type"]
        assert data["schedule"] == task_data["schedule"]
        assert "config" in data
        assert data["enabled"] is True
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_nonexistent_task(self, api_client):
        response = api_client.get("/tasks/nonexistent_task_id")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False


class TestTaskUpdate:
    
    def test_update_task_name(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        update_data = {"name": "Updated Task Name"}
        response = api_client.put(f"/tasks/{task_id}", data=update_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["name"] == update_data["name"]
    
    def test_update_task_schedule(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        update_data = {"schedule": "0 1 * * *"}
        response = api_client.put(f"/tasks/{task_id}", data=update_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["schedule"] == update_data["schedule"]
    
    def test_update_task_config(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        update_data = {
            "config": {
                "path": "/tmp/new_path",
                "pattern": "*.log",
                "days": 30
            }
        }
        response = api_client.put(f"/tasks/{task_id}", data=update_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_update_nonexistent_task(self, api_client):
        update_data = {"name": "New name"}
        response = api_client.put("/tasks/nonexistent_task_id", data=update_data)
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False


class TestTaskDeletion:
    
    def test_delete_task(self, api_client, sample_task_data):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        
        response = api_client.delete(f"/tasks/{task_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        get_response = api_client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_task(self, api_client):
        response = api_client.delete("/tasks/nonexistent_task_id")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False


class TestTaskToggle:
    
    def test_disable_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        toggle_data = {"enabled": False}
        response = api_client.post(f"/tasks/{task_id}/toggle", data=toggle_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["enabled"] is False
    
    def test_enable_task(self, api_client, sample_task_data, cleanup_tasks):
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        toggle_data = {"enabled": True}
        response = api_client.post(f"/tasks/{task_id}/toggle", data=toggle_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["enabled"] is True
    
    def test_toggle_nonexistent_task(self, api_client):
        toggle_data = {"enabled": True}
        response = api_client.post("/tasks/nonexistent_task_id/toggle", data=toggle_data)
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False

