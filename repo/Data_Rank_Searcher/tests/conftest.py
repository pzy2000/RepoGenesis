"""
Pytest 配置文件

提供测试的全局配置和fixture
"""

import pytest
import requests
import time
from typing import Generator


BASE_URL = "http://localhost:8080"
API_ENDPOINT = f"{BASE_URL}/api/data"


@pytest.fixture(scope="session", autouse=True)
def check_server_availability():
    """
    检查服务器是否可用
    在所有测试开始前执行
    """
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=2)
            print(f"\n服务器连接成功: {BASE_URL}")
            return
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"\n尝试连接服务器 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                pytest.exit(
                    f"无法连接到服务器 {BASE_URL}。"
                    f"请确保服务已启动并监听在端口 8080。\n"
                    f"错误信息: {str(e)}"
                )


@pytest.fixture(scope="function")
def clean_test_data():
    """
    在每个测试后清理数据
    """
    created_ids = []
    
    def _register_id(data_id: str):
        """注册需要清理的ID"""
        created_ids.append(data_id)
    
    yield _register_id
    
    # 测试结束后清理
    for data_id in created_ids:
        try:
            requests.delete(f"{API_ENDPOINT}/{data_id}", timeout=2)
        except:
            pass


@pytest.fixture(scope="function")
def sample_data():
    """
    提供测试用的样本数据
    """
    return [
        {
            "name": "Sample Item 1",
            "category": "Category A",
            "score": 85.0,
            "description": "This is a sample item for testing",
            "tags": ["test", "sample"]
        },
        {
            "name": "Sample Item 2",
            "category": "Category B",
            "score": 90.0,
            "description": "Another sample item",
            "tags": ["test", "example"]
        },
        {
            "name": "Sample Item 3",
            "category": "Category A",
            "score": 78.5,
            "description": "Third sample item",
            "tags": ["test"]
        }
    ]


def pytest_configure(config):
    """
    Pytest 配置钩子
    """
    config.addinivalue_line(
        "markers", "slow: 标记测试为慢速测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记为集成测试"
    )


def pytest_collection_modifyitems(config, items):
    """
    修改测试收集行为
    为所有测试添加integration标记
    """
    for item in items:
        item.add_marker(pytest.mark.integration)

