import pytest


class TestFileCleanupTask:
    
    def test_create_file_cleanup_task_with_full_config(self, api_client, cleanup_tasks):
        task_data = {
            "name": "Clean log files",
            "description": "Clean log files older than 30 days",
            "task_type": "file_cleanup",
            "schedule": "0 3 * * *",
            "config": {
                "path": "/var/log/app",
                "pattern": "*.log",
                "days": 30
            },
            "enabled": True
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["task_type"] == "file_cleanup"
        
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_file_cleanup_task_missing_path(self, api_client):
        task_data = {
            "name": "Clean tmp files",
            "task_type": "file_cleanup",
            "schedule": "0 3 * * *",
            "config": {
                "pattern": "*.tmp",
                "days": 7
            }
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code in [201, 400]
        
        if response.status_code == 400:
            result = response.json()
            assert result["success"] is False
    
    def test_file_cleanup_task_with_different_patterns(self, api_client, cleanup_tasks):
        patterns = ["*.tmp", "*.log", "*.bak", "temp_*"]
        
        for pattern in patterns:
            task_data = {
                "name": f"Clean {pattern} files",
                "task_type": "file_cleanup",
                "schedule": "0 4 * * *",
                "config": {
                    "path": "/tmp",
                    "pattern": pattern,
                    "days": 7
                }
            }
            
            response = api_client.post("/tasks", data=task_data)
            
            assert response.status_code == 201
            result = response.json()
            cleanup_tasks.append(result["data"]["task_id"])


class TestDataSummaryTask:
    
    def test_create_data_summary_task_with_full_config(self, api_client, cleanup_tasks):
        task_data = {
            "name": "Daily sales summary",
            "description": "Daily sales data summary",
            "task_type": "data_summary",
            "schedule": "0 22 * * *",
            "config": {
                "source": "sales_records",
                "target": "daily_sales_summary"
            },
            "enabled": True
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["task_type"] == "data_summary"
        
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_data_summary_task_weekly_schedule(self, api_client, cleanup_tasks):
        task_data = {
            "name": "Weekly report summary",
            "task_type": "data_summary",
            "schedule": "0 9 * * 1",
            "config": {
                "source": "weekly_data",
                "target": "weekly_report"
            }
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_data_summary_task_monthly_schedule(self, api_client, cleanup_tasks):
        task_data = {
            "name": "Monthly report summary",
            "task_type": "data_summary",
            "schedule": "0 0 1 * *",
            "config": {
                "source": "monthly_data",
                "target": "monthly_report"
            }
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result["data"]["task_id"])


class TestDataBackupTask:
    
    def test_create_data_backup_task_with_full_config(self, api_client, cleanup_tasks):
        task_data = {
            "name": "Database full backup",
            "description": "Daily database full backup at 2 AM",
            "task_type": "data_backup",
            "schedule": "0 2 * * *",
            "config": {
                "source": "mysql_database",
                "target": "/backup/mysql/full"
            },
            "enabled": True
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["task_type"] == "data_backup"
        
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_data_backup_task_incremental(self, api_client, cleanup_tasks):
        task_data = {
            "name": "Incremental backup",
            "task_type": "data_backup",
            "schedule": "0 */4 * * *",
            "config": {
                "source": "database",
                "target": "/backup/incremental",
                "backup_type": "incremental"
            }
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code == 201
        result = response.json()
        cleanup_tasks.append(result["data"]["task_id"])
    
    def test_data_backup_task_missing_target(self, api_client):
        task_data = {
            "name": "Backup task",
            "task_type": "data_backup",
            "schedule": "0 2 * * *",
            "config": {
                "source": "database"
            }
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        assert response.status_code in [201, 400]


class TestTaskTypeValidation:
    def test_all_valid_task_types(self, api_client, cleanup_tasks):
        valid_types = ["file_cleanup", "data_summary", "data_backup"]
        
        for task_type in valid_types:
            task_data = {
                "name": f"Test{task_type}",
                "task_type": task_type,
                "schedule": "0 0 * * *",
                "config": {}
            }
            
            response = api_client.post("/tasks", data=task_data)
            
            assert response.status_code in [201, 400]
            if response.status_code == 201:
                result = response.json()
                cleanup_tasks.append(result["data"]["task_id"])
    
    def test_invalid_task_types(self, api_client):
        invalid_types = [
            "invalid_type",
            "file_delete",
            "data_export",
            "",
            "FILE_CLEANUP",
            "file-cleanup"
        ]
        
        for task_type in invalid_types:
            task_data = {
                "name": "Test task",
                "task_type": task_type,
                "schedule": "0 0 * * *",
                "config": {}
            }
            
            response = api_client.post("/tasks", data=task_data)
            
            assert response.status_code == 400
            result = response.json()
            assert result["success"] is False


class TestCronScheduleValidation:
    
    def test_valid_cron_expressions(self, api_client, cleanup_tasks):
        valid_crons = [
            "0 0 * * *",
            "0 */2 * * *",
            "30 3 * * 1",
            "0 0 1 * *",
            "*/5 * * * *",
            "0 9-17 * * 1-5"
        ]
        
        for cron in valid_crons:
            task_data = {
                "name": f"Test cron: {cron}",
                "task_type": "file_cleanup",
                "schedule": cron,
                "config": {
                    "path": "/tmp",
                    "pattern": "*.tmp",
                    "days": 7
                }
            }
            
            response = api_client.post("/tasks", data=task_data)
            
            assert response.status_code == 201
            result = response.json()
            cleanup_tasks.append(result["data"]["task_id"])
    
    def test_invalid_cron_expressions(self, api_client):
        invalid_crons = [
            "invalid",
            "* * * *",
            "60 0 * * *",
            "0 25 * * *",
            "0 0 32 * *",
            "0 0 * 13 *",
            "0 0 * * 7",
            ""
        ]
        
        for cron in invalid_crons:
            task_data = {
                "name": "Test task",
                "task_type": "file_cleanup",
                "schedule": cron,
                "config": {
                    "path": "/tmp",
                    "pattern": "*.tmp",
                    "days": 7
                }
            }
            
            response = api_client.post("/tasks", data=task_data)
            
            assert response.status_code == 400
            result = response.json()
            assert result["success"] is False

