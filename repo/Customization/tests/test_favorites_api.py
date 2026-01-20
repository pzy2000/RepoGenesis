"""
个性化设置API - 收藏功能测试用例

本模块包含收藏管理API的综合测试用例。
所有测试均按照README.md中的接口定义进行真实端口测试。
"""

import pytest
import requests
import json
from datetime import datetime


class TestFavoritesAPI:
    """收藏API测试套件"""

    BASE_URL = "http://localhost:8082/api/v1"
    TEST_USER_TOKEN = "test_token_12345"  # 测试用token，实际使用时应从认证服务获取

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的清理工作"""
        try:
            # 清理测试收藏数据
            response = requests.get(f"{self.BASE_URL}/favorites", headers=self.get_auth_headers())
            if response.status_code == 200:
                favorites = response.json().get('favorites', [])
                for favorite in favorites:
                    if favorite['content_id'].startswith('test_content_'):
                        requests.delete(
                            f"{self.BASE_URL}/favorites/{favorite['id']}",
                            headers=self.get_auth_headers()
                        )
        except requests.exceptions.ConnectionError:
            pytest.skip("API服务器未运行")

    def get_auth_headers(self):
        """获取认证头"""
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        """测试健康检查接口"""
        response = requests.get(f"{self.BASE_URL.replace('/api/v1', '')}/health")

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_add_favorite_success(self):
        """测试成功添加收藏"""
        favorite_data = {
            "content_id": "test_content_001",
            "content_type": "post",
            "category": "技术文章"
        }

        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['content_id'] == favorite_data['content_id']
        assert data['content_type'] == favorite_data['content_type']
        assert data['category'] == favorite_data['category']
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_add_favorite_minimal_data(self):
        """测试使用最小数据添加收藏"""
        favorite_data = {
            "content_id": "test_content_minimal",
            "content_type": "article"
        }

        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['content_id'] == favorite_data['content_id']
        assert data['content_type'] == favorite_data['content_type']
        assert data['category'] is None or data['category'] == ""

    def test_add_favorite_duplicate_content(self):
        """测试重复添加相同内容的收藏"""
        favorite_data = {
            "content_id": "test_content_duplicate",
            "content_type": "video",
            "category": "教程"
        }

        # 第一次添加
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        first_id = response.json()['id']

        # 再次添加相同内容
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )

        # 预期行为：可能返回409冲突，或允许重复收藏（业务逻辑决定）
        assert response.status_code in [201, 409]

    def test_add_favorite_invalid_content_type(self):
        """测试使用无效内容类型添加收藏"""
        favorite_data = {
            "content_id": "test_content_invalid",
            "content_type": "invalid_type",
            "category": "测试"
        }

        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_favorite_missing_required_fields(self):
        """测试缺少必填字段时添加收藏"""
        favorite_data = {
            "category": "测试分类"
        }

        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_favorite_unauthorized(self):
        """测试未认证时添加收藏"""
        favorite_data = {
            "content_id": "test_content_unauth",
            "content_type": "post"
        }

        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data
        )

        assert response.status_code in [401, 403]

    def test_get_favorites_list_empty(self):
        """测试获取空收藏列表"""
        response = requests.get(
            f"{self.BASE_URL}/favorites",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'favorites' in data
        assert 'pagination' in data
        assert len(data['favorites']) == 0

    def test_get_favorites_list_with_data(self):
        """测试获取有数据的收藏列表"""
        # 先创建一些收藏
        favorites_data = [
            {"content_id": "test_list_1", "content_type": "post", "category": "新闻"},
            {"content_id": "test_list_2", "content_type": "article", "category": "技术"},
            {"content_id": "test_list_3", "content_type": "video", "category": "娱乐"}
        ]

        created_favorites = []
        for favorite_data in favorites_data:
            response = requests.post(
                f"{self.BASE_URL}/favorites",
                json=favorite_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201
            created_favorites.append(response.json())

        # 获取收藏列表
        response = requests.get(
            f"{self.BASE_URL}/favorites",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['favorites']) >= 3
        assert data['pagination']['total'] >= 3
        assert data['pagination']['page'] == 1

    def test_get_favorites_with_pagination(self):
        """测试收藏列表分页"""
        # 创建15个收藏
        for i in range(15):
            favorite_data = {
                "content_id": f"test_pagination_{i+1}",
                "content_type": "post",
                "category": "测试"
            }
            response = requests.post(
                f"{self.BASE_URL}/favorites",
                json=favorite_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        # 测试第一页
        response = requests.get(
            f"{self.BASE_URL}/favorites?page=1&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data['favorites']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 15

        # 测试第二页
        response = requests.get(
            f"{self.BASE_URL}/favorites?page=2&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 2

    def test_get_favorites_filter_by_content_type(self):
        """测试按内容类型筛选收藏"""
        # 创建不同类型的收藏
        content_types = ["post", "article", "video", "product"]
        for content_type in content_types:
            favorite_data = {
                "content_id": f"test_filter_{content_type}",
                "content_type": content_type,
                "category": "测试"
            }
            response = requests.post(
                f"{self.BASE_URL}/favorites",
                json=favorite_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        # 按文章类型筛选
        response = requests.get(
            f"{self.BASE_URL}/favorites?content_type=article",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        article_favorites = [f for f in data['favorites'] if f['content_type'] == 'article']
        assert len(article_favorites) >= 1

    def test_get_favorites_filter_by_category(self):
        """测试按分类筛选收藏"""
        # 创建不同分类的收藏
        categories = ["新闻", "技术", "娱乐", "教育"]
        for category in categories:
            favorite_data = {
                "content_id": f"test_category_{category}",
                "content_type": "post",
                "category": category
            }
            response = requests.post(
                f"{self.BASE_URL}/favorites",
                json=favorite_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        # 按技术分类筛选
        response = requests.get(
            f"{self.BASE_URL}/favorites?category=技术",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        tech_favorites = [f for f in data['favorites'] if f['category'] == '技术']
        assert len(tech_favorites) >= 1

    def test_delete_favorite_success(self):
        """测试成功删除收藏"""
        # 先创建一个收藏
        favorite_data = {
            "content_id": "test_delete_001",
            "content_type": "post",
            "category": "测试删除"
        }
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        favorite_id = response.json()['id']

        # 删除收藏
        response = requests.delete(
            f"{self.BASE_URL}/favorites/{favorite_id}",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    def test_delete_favorite_not_found(self):
        """测试删除不存在的收藏"""
        response = requests.delete(
            f"{self.BASE_URL}/favorites/non_existent_id",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data

    def test_delete_favorite_unauthorized(self):
        """测试未认证时删除收藏"""
        response = requests.delete(f"{self.BASE_URL}/favorites/some_id")

        assert response.status_code in [401, 403]

    def test_favorites_workflow_complete(self):
        """测试完整的收藏工作流程"""
        # 1. 添加收藏
        favorite_data = {
            "content_id": "test_workflow_content",
            "content_type": "article",
            "category": "工作流程测试"
        }
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        favorite_id = response.json()['id']

        # 2. 获取收藏列表验证存在
        response = requests.get(
            f"{self.BASE_URL}/favorites?content_type=article",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        favorites = response.json()['favorites']
        favorite_ids = [f['id'] for f in favorites]
        assert favorite_id in favorite_ids

        # 3. 删除收藏
        response = requests.delete(
            f"{self.BASE_URL}/favorites/{favorite_id}",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200

        # 4. 验证收藏已被删除
        response = requests.get(
            f"{self.BASE_URL}/favorites?content_type=article",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        favorites = response.json()['favorites']
        favorite_ids = [f['id'] for f in favorites]
        assert favorite_id not in favorite_ids

    def test_invalid_json_request(self):
        """测试无效JSON请求"""
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            data="invalid json",
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        """测试大分页数量限制"""
        response = requests.get(
            f"{self.BASE_URL}/favorites?limit=1000",
            headers=self.get_auth_headers()
        )

        # 应该返回错误或限制最大数量
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100
