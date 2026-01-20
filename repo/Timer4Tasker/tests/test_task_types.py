"""
测试不同类型的任务
"""
import pytest


class TestFileCleanupTask:
    """测试文件清理任务"""
    
    def test_create_file_cleanup_task_with_full_config(self, api_client, cleanup_tasks):
        """测试创建完整配置的文件清理任务"""
        task_data = {
            "name": "清理日志文件",
            "description": "清理30天前的日志文件",
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
        """测试文件清理任务缺少路径配置"""
        task_data = {
            "name": "清理任务",
            "task_type": "file_cleanup",
            "schedule": "0 3 * * *",
            "config": {
                "pattern": "*.tmp",
                "days": 7
            }
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        # 可能返回 400（配置不完整）或 201（有默认值）
        assert response.status_code in [201, 400]
        
        if response.status_code == 400:
            result = response.json()
            assert result["success"] is False
    
    def test_file_cleanup_task_with_different_patterns(self, api_client, cleanup_tasks):
        """测试不同文件模式的清理任务"""
        patterns = ["*.tmp", "*.log", "*.bak", "temp_*"]
        
        for pattern in patterns:
            task_data = {
                "name": f"清理{pattern}文件",
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
    """测试数据汇总任务"""
    
    def test_create_data_summary_task_with_full_config(self, api_client, cleanup_tasks):
        """测试创建完整配置的数据汇总任务"""
        task_data = {
            "name": "销售数据汇总",
            "description": "每日销售数据汇总",
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
        """测试每周数据汇总任务"""
        task_data = {
            "name": "周报汇总",
            "task_type": "data_summary",
            "schedule": "0 9 * * 1",  # 每周一早上9点
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
        """测试每月数据汇总任务"""
        task_data = {
            "name": "月报汇总",
            "task_type": "data_summary",
            "schedule": "0 0 1 * *",  # 每月1号凌晨
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
    """测试数据备份任务"""
    
    def test_create_data_backup_task_with_full_config(self, api_client, cleanup_tasks):
        """测试创建完整配置的数据备份任务"""
        task_data = {
            "name": "数据库全量备份",
            "description": "每天凌晨2点进行数据库全量备份",
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
        """测试增量备份任务"""
        task_data = {
            "name": "增量备份",
            "task_type": "data_backup",
            "schedule": "0 */4 * * *",  # 每4小时一次
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
        """测试备份任务缺少目标路径"""
        task_data = {
            "name": "备份任务",
            "task_type": "data_backup",
            "schedule": "0 2 * * *",
            "config": {
                "source": "database"
                # 缺少 target
            }
        }
        
        response = api_client.post("/tasks", data=task_data)
        
        # 可能返回 400（配置不完整）或 201（有默认值）
        assert response.status_code in [201, 400]


class TestTaskTypeValidation:
    """测试任务类型验证"""
    
    def test_all_valid_task_types(self, api_client, cleanup_tasks):
        """测试所有有效的任务类型"""
        valid_types = ["file_cleanup", "data_summary", "data_backup"]
        
        for task_type in valid_types:
            task_data = {
                "name": f"测试{task_type}",
                "task_type": task_type,
                "schedule": "0 0 * * *",
                "config": {}
            }
            
            response = api_client.post("/tasks", data=task_data)
            
            assert response.status_code in [201, 400]  # 400可能是因为config不完整
            if response.status_code == 201:
                result = response.json()
                cleanup_tasks.append(result["data"]["task_id"])
    
    def test_invalid_task_types(self, api_client):
        """测试无效的任务类型"""
        invalid_types = [
            "invalid_type",
            "file_delete",
            "data_export",
            "",
            "FILE_CLEANUP",  # 大写
            "file-cleanup"   # 错误的分隔符
        ]
        
        for task_type in invalid_types:
            task_data = {
                "name": "测试任务",
                "task_type": task_type,
                "schedule": "0 0 * * *",
                "config": {}
            }
            
            response = api_client.post("/tasks", data=task_data)
            
            assert response.status_code == 400
            result = response.json()
            assert result["success"] is False


class TestCronScheduleValidation:
    """测试 Cron 表达式验证"""
    
    def test_valid_cron_expressions(self, api_client, cleanup_tasks):
        """测试有效的 Cron 表达式"""
        valid_crons = [
            "0 0 * * *",      # 每天凌晨
            "0 */2 * * *",    # 每2小时
            "30 3 * * 1",     # 每周一凌晨3:30
            "0 0 1 * *",      # 每月1号
            "*/5 * * * *",    # 每5分钟
            "0 9-17 * * 1-5"  # 工作日的9-17点
        ]
        
        for cron in valid_crons:
            task_data = {
                "name": f"测试cron: {cron}",
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
        """测试无效的 Cron 表达式"""
        invalid_crons = [
            "invalid",
            "* * * *",        # 缺少字段
            "60 0 * * *",     # 无效的分钟
            "0 25 * * *",     # 无效的小时
            "0 0 32 * *",     # 无效的日期
            "0 0 * 13 *",     # 无效的月份
            "0 0 * * 7",      # 无效的星期（取决于实现）
            ""
        ]
        
        for cron in invalid_crons:
            task_data = {
                "name": "测试任务",
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

