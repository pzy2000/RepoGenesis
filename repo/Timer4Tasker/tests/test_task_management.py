"""
测试任务管理相关的 API 接口
"""
import pytest
import time


class TestTaskCreation:
    """测试任务创建功能"""
    
    def test_create_file_cleanup_task(self, api_client, sample_task_data, cleanup_tasks):
        """测试创建文件清理任务"""
        task_data = sample_task_data["file_cleanup"]
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201, f"创建任务失败: {response.text}"
        
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
        """测试创建数据汇总任务"""
        task_data = sample_task_data["data_summary"]
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["task_type"] == "data_summary"
        
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_create_data_backup_task(self, api_client, sample_task_data, cleanup_tasks):
        """测试创建数据备份任务"""
        task_data = sample_task_data["data_backup"]
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["task_type"] == "data_backup"
        assert result["data"]["enabled"] is False
        
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_create_task_with_missing_required_fields(self, api_client):
        """测试缺少必填字段时创建任务失败"""
        invalid_data = {
            "name": "测试任务"
            # 缺少 task_type 和 schedule
        }
        response = api_client.post("/tasks", data=invalid_data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
    
    def test_create_task_with_invalid_task_type(self, api_client):
        """测试使用无效的任务类型"""
        invalid_data = {
            "name": "测试任务",
            "task_type": "invalid_type",
            "schedule": "0 0 * * *"
        }
        response = api_client.post("/tasks", data=invalid_data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
    
    def test_create_task_with_invalid_cron(self, api_client):
        """测试使用无效的 cron 表达式"""
        invalid_data = {
            "name": "测试任务",
            "task_type": "file_cleanup",
            "schedule": "invalid cron"
        }
        response = api_client.post("/tasks", data=invalid_data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False


class TestTaskRetrieval:
    """测试任务查询功能"""
    
    def test_get_all_tasks(self, api_client, sample_task_data, cleanup_tasks):
        """测试获取所有任务列表"""
        # 先创建几个任务
        for task_type, task_data in sample_task_data.items():
            response = api_client.post("/tasks", data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()["data"]["task_id"])
        
        # 获取任务列表
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
        """测试按任务类型过滤"""
        # 创建不同类型的任务
        for task_type, task_data in sample_task_data.items():
            response = api_client.post("/tasks", data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()["data"]["task_id"])
        
        # 按类型过滤
        response = api_client.get("/tasks", params={"task_type": "file_cleanup"})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        tasks = result["data"]["tasks"]
        for task in tasks:
            assert task["task_type"] == "file_cleanup"
    
    def test_get_tasks_with_filter_by_enabled(self, api_client, sample_task_data, cleanup_tasks):
        """测试按启用状态过滤"""
        # 创建任务
        for task_type, task_data in sample_task_data.items():
            response = api_client.post("/tasks", data=task_data)
            if response.status_code == 201:
                cleanup_tasks.append(response.json()["data"]["task_id"])
        
        # 过滤已启用的任务
        response = api_client.get("/tasks", params={"enabled": True})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        tasks = result["data"]["tasks"]
        for task in tasks:
            assert task["enabled"] is True
    
    def test_get_tasks_with_pagination(self, api_client):
        """测试分页功能"""
        response = api_client.get("/tasks", params={"page": 1, "page_size": 5})
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        data = result["data"]
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["tasks"]) <= 5
    
    def test_get_task_by_id(self, api_client, sample_task_data, cleanup_tasks):
        """测试获取任务详情"""
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        assert create_response.status_code == 201
        
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 获取任务详情
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
        """测试获取不存在的任务"""
        response = api_client.get("/tasks/nonexistent_task_id")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False


class TestTaskUpdate:
    """测试任务更新功能"""
    
    def test_update_task_name(self, api_client, sample_task_data, cleanup_tasks):
        """测试更新任务名称"""
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 更新任务名称
        update_data = {"name": "更新后的任务名称"}
        response = api_client.put(f"/tasks/{task_id}", data=update_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["name"] == update_data["name"]
    
    def test_update_task_schedule(self, api_client, sample_task_data, cleanup_tasks):
        """测试更新任务调度时间"""
        # 创建任务
        task_data = sample_task_data["data_summary"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 更新调度时间
        update_data = {"schedule": "0 1 * * *"}
        response = api_client.put(f"/tasks/{task_id}", data=update_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["schedule"] == update_data["schedule"]
    
    def test_update_task_config(self, api_client, sample_task_data, cleanup_tasks):
        """测试更新任务配置"""
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 更新配置
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
        """测试更新不存在的任务"""
        update_data = {"name": "新名称"}
        response = api_client.put("/tasks/nonexistent_task_id", data=update_data)
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False


class TestTaskDeletion:
    """测试任务删除功能"""
    
    def test_delete_task(self, api_client, sample_task_data):
        """测试删除任务"""
        # 创建任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        
        # 删除任务
        response = api_client.delete(f"/tasks/{task_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # 验证任务已被删除
        get_response = api_client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_task(self, api_client):
        """测试删除不存在的任务"""
        response = api_client.delete("/tasks/nonexistent_task_id")
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False


class TestTaskToggle:
    """测试任务启动/停止功能"""
    
    def test_disable_task(self, api_client, sample_task_data, cleanup_tasks):
        """测试停止任务"""
        # 创建启用的任务
        task_data = sample_task_data["file_cleanup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 停止任务
        toggle_data = {"enabled": False}
        response = api_client.post(f"/tasks/{task_id}/toggle", data=toggle_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["enabled"] is False
    
    def test_enable_task(self, api_client, sample_task_data, cleanup_tasks):
        """测试启动任务"""
        # 创建禁用的任务
        task_data = sample_task_data["data_backup"]
        create_response = api_client.post("/tasks", data=task_data)
        task_id = create_response.json()["data"]["task_id"]
        cleanup_tasks.append(task_id)
        
        # 启动任务
        toggle_data = {"enabled": True}
        response = api_client.post(f"/tasks/{task_id}/toggle", data=toggle_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["enabled"] is True
    
    def test_toggle_nonexistent_task(self, api_client):
        """测试切换不存在的任务"""
        toggle_data = {"enabled": True}
        response = api_client.post("/tasks/nonexistent_task_id/toggle", data=toggle_data)
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False

