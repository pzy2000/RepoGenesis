"""
个性化设置API - 点赞功能测试用例

本模块包含点赞管理API的综合测试用例。
所有测试均按照README.md中的接口定义进行真实端口测试。
"""

import pytest
import requests
import json
from datetime import datetime


class TestLikesAPI:
    """点赞API测试套件"""

    BASE_URL = "http://localhost:8082/api/v1"
    TEST_USER_TOKEN = "test_token_12345"  # 测试用token，实际使用时应从认证服务获取

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的清理工作"""
        try:
            # 清理测试点赞数据
            response = requests.get(f"{self.BASE_URL}/likes/history", headers=self.get_auth_headers())
            if response.status_code == 200:
                likes = response.json().get('likes', [])
                for like in likes:
                    if like['content_id'].startswith('test_content_'):
                        # 这里可以添加清理逻辑，如果API支持删除特定点赞记录的话
                        pass
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

    def test_add_like_success(self):
        """测试成功添加点赞"""
        like_data = {
            "content_id": "test_content_like_001",
            "content_type": "post",
            "action": "like"
        }

        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['content_id'] == like_data['content_id']
        assert data['content_type'] == like_data['content_type']
        assert data['action'] == like_data['action']
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_add_unlike_success(self):
        """测试成功添加点踩"""
        like_data = {
            "content_id": "test_content_unlike_001",
            "content_type": "article",
            "action": "unlike"
        }

        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'unlike'

    def test_add_like_missing_action(self):
        """测试缺少action字段时添加点赞"""
        like_data = {
            "content_id": "test_content_missing_action",
            "content_type": "post"
        }

        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_like_invalid_action(self):
        """测试使用无效action添加点赞"""
        like_data = {
            "content_id": "test_content_invalid_action",
            "content_type": "post",
            "action": "invalid_action"
        }

        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_like_invalid_content_type(self):
        """测试使用无效内容类型添加点赞"""
        like_data = {
            "content_id": "test_content_invalid_type",
            "content_type": "invalid_type",
            "action": "like"
        }

        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_add_like_unauthorized(self):
        """测试未认证时添加点赞"""
        like_data = {
            "content_id": "test_content_unauth",
            "content_type": "post",
            "action": "like"
        }

        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data
        )

        assert response.status_code in [401, 403]

    def test_get_like_stats_success(self):
        """测试成功获取点赞统计"""
        # 先添加一些点赞
        content_id = "test_stats_content_001"
        content_type = "post"

        # 添加点赞
        like_data = {
            "content_id": content_id,
            "content_type": content_type,
            "action": "like"
        }
        requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        # 添加点踩
        unlike_data = {
            "content_id": content_id,
            "content_type": content_type,
            "action": "unlike"
        }
        requests.post(
            f"{self.BASE_URL}/likes",
            json=unlike_data,
            headers=self.get_auth_headers()
        )

        # 获取统计
        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")

        assert response.status_code == 200
        data = response.json()
        assert data['content_id'] == content_id
        assert data['content_type'] == content_type
        assert 'total_likes' in data
        assert 'total_unlikes' in data
        assert 'user_action' in data

    def test_get_like_stats_not_found(self):
        """测试获取不存在内容的点赞统计"""
        response = requests.get(f"{self.BASE_URL}/likes/stats/non_existent_content")

        # 可能返回404或返回空统计数据（视业务逻辑而定）
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data['total_likes'] == 0
            assert data['total_unlikes'] == 0

    def test_get_like_stats_without_auth(self):
        """测试未认证时获取点赞统计"""
        response = requests.get(f"{self.BASE_URL}/likes/stats/some_content")

        # 统计接口通常允许匿名访问
        assert response.status_code == 200

    def test_get_likes_history_empty(self):
        """测试获取空点赞历史"""
        response = requests.get(
            f"{self.BASE_URL}/likes/history",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'likes' in data
        assert 'pagination' in data
        assert len(data['likes']) == 0

    def test_get_likes_history_with_data(self):
        """测试获取有数据的点赞历史"""
        # 先创建一些点赞记录
        likes_data = [
            {"content_id": "test_history_1", "content_type": "post", "action": "like"},
            {"content_id": "test_history_2", "content_type": "article", "action": "unlike"},
            {"content_id": "test_history_3", "content_type": "video", "action": "like"}
        ]

        for like_data in likes_data:
            response = requests.post(
                f"{self.BASE_URL}/likes",
                json=like_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        # 获取历史记录
        response = requests.get(
            f"{self.BASE_URL}/likes/history",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['likes']) >= 3
        assert data['pagination']['total'] >= 3

    def test_get_likes_history_pagination(self):
        """测试点赞历史分页"""
        # 创建15条点赞记录
        for i in range(15):
            like_data = {
                "content_id": f"test_history_pagination_{i+1}",
                "content_type": "post",
                "action": "like"
            }
            response = requests.post(
                f"{self.BASE_URL}/likes",
                json=like_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        # 测试第一页
        response = requests.get(
            f"{self.BASE_URL}/likes/history?page=1&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data['likes']) == 10
        assert data['pagination']['page'] == 1

        # 测试第二页
        response = requests.get(
            f"{self.BASE_URL}/likes/history?page=2&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 2

    def test_get_likes_history_filter_by_content_type(self):
        """测试按内容类型筛选点赞历史"""
        # 创建不同类型的点赞记录
        content_types = ["post", "article", "video"]
        for content_type in content_types:
            like_data = {
                "content_id": f"test_filter_history_{content_type}",
                "content_type": content_type,
                "action": "like"
            }
            response = requests.post(
                f"{self.BASE_URL}/likes",
                json=like_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        # 按视频类型筛选
        response = requests.get(
            f"{self.BASE_URL}/likes/history?content_type=video",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        video_likes = [like for like in data['likes'] if like['content_type'] == 'video']
        assert len(video_likes) >= 1

    def test_get_likes_history_unauthorized(self):
        """测试未认证时获取点赞历史"""
        response = requests.get(f"{self.BASE_URL}/likes/history")

        assert response.status_code in [401, 403]

    def test_like_workflow_complete(self):
        """测试完整的点赞工作流程"""
        content_id = "test_workflow_like_content"
        content_type = "post"

        # 1. 点赞内容
        like_data = {
            "content_id": content_id,
            "content_type": content_type,
            "action": "like"
        }
        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        like_id = response.json()['id']

        # 2. 验证点赞历史中存在该记录
        response = requests.get(
            f"{self.BASE_URL}/likes/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        likes = response.json()['likes']
        like_ids = [like['id'] for like in likes]
        assert like_id in like_ids

        # 3. 检查点赞统计
        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_likes'] >= 1

        # 4. 取消点赞（点踩）
        unlike_data = {
            "content_id": content_id,
            "content_type": content_type,
            "action": "unlike"
        }
        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=unlike_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201

        # 5. 验证统计更新
        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_unlikes'] >= 1

    def test_multiple_users_like_same_content(self):
        """测试多个用户对同一内容点赞"""
        content_id = "test_multi_user_content"
        content_type = "article"

        # 模拟不同用户的点赞（实际测试中可能需要不同的token）
        like_data = {
            "content_id": content_id,
            "content_type": content_type,
            "action": "like"
        }

        # 第一次点赞
        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201

        # 第二次点赞（同一用户再次点赞，应该覆盖或拒绝）
        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        # 预期行为：可能返回201（更新）或409（冲突），视业务逻辑而定
        assert response.status_code in [201, 409]

        # 检查统计
        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_likes'] >= 1

    def test_like_content_types_coverage(self):
        """测试所有支持的内容类型点赞"""
        content_types = ["post", "article", "product", "video"]

        for content_type in content_types:
            like_data = {
                "content_id": f"test_content_type_{content_type}",
                "content_type": content_type,
                "action": "like"
            }

            response = requests.post(
                f"{self.BASE_URL}/likes",
                json=like_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

            # 验证统计接口也能处理该类型
            response = requests.get(f"{self.BASE_URL}/likes/stats/test_content_type_{content_type}")
            assert response.status_code == 200

    def test_invalid_json_request(self):
        """测试无效JSON请求"""
        response = requests.post(
            f"{self.BASE_URL}/likes",
            data="invalid json",
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        """测试大分页数量限制"""
        response = requests.get(
            f"{self.BASE_URL}/likes/history?limit=1000",
            headers=self.get_auth_headers()
        )

        # 应该返回错误或限制最大数量
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 50  # 根据README，最大限制是50
