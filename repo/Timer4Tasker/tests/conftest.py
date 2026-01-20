"""
Pytest 配置和通用 fixtures
"""
import pytest
import requests
import time
import json


# 测试服务的基础 URL
BASE_URL = "http://localhost:8080/api/v1"


@pytest.fixture(scope="session")
def base_url():
    """返回 API 基础 URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def check_server():
    """检查服务器是否运行"""
    max_retries = 5
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/stats", timeout=5)
            if response.status_code in [200, 404]:
                return True
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                pytest.fail(
                    f"服务器未运行或无法访问: {BASE_URL}\n"
                    "请先启动服务: python app.py"
                )
    return True


@pytest.fixture
def api_client(base_url, check_server):
    """返回一个简单的 API 客户端类"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            self.session.headers.update({"Content-Type": "application/json"})
        
        def get(self, endpoint, params=None):
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params)
            return response
        
        def post(self, endpoint, data=None):
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=data)
            return response
        
        def put(self, endpoint, data=None):
            url = f"{self.base_url}{endpoint}"
            response = self.session.put(url, json=data)
            return response
        
        def delete(self, endpoint):
            url = f"{self.base_url}{endpoint}"
            response = self.session.delete(url)
            return response
    
    return APIClient(base_url)


@pytest.fixture
def sample_task_data():
    """返回示例任务数据"""
    return {
        "file_cleanup": {
            "name": "清理临时文件",
            "description": "每天凌晨清理临时文件",
            "task_type": "file_cleanup",
            "schedule": "0 0 * * *",
            "config": {
                "path": "/tmp/app_temp",
                "pattern": "*.tmp",
                "days": 7
            },
            "enabled": True
        },
        "data_summary": {
            "name": "每日数据汇总",
            "description": "每天23点进行数据汇总",
            "task_type": "data_summary",
            "schedule": "0 23 * * *",
            "config": {
                "source": "transactions",
                "target": "daily_summary"
            },
            "enabled": True
        },
        "data_backup": {
            "name": "数据库备份",
            "description": "每周日凌晨2点备份数据库",
            "task_type": "data_backup",
            "schedule": "0 2 * * 0",
            "config": {
                "source": "database",
                "target": "/backup/db"
            },
            "enabled": False
        }
    }


@pytest.fixture
def cleanup_tasks(api_client):
    """测试后清理创建的任务"""
    created_task_ids = []
    
    yield created_task_ids
    
    # 清理所有创建的任务
    for task_id in created_task_ids:
        try:
            api_client.delete(f"/tasks/{task_id}")
        except Exception:
            pass  # 忽略清理时的错误


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "integration: 标记为集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    )

