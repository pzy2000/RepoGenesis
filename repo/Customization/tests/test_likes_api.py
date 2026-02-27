import pytest
import requests
import json
from datetime import datetime


class TestLikesAPI:
    BASE_URL = "http://localhost:8082/api/v1"
    TEST_USER_TOKEN = "test_token_12345"

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            response = requests.get(f"{self.BASE_URL}/likes/history", headers=self.get_auth_headers())
            if response.status_code == 200:
                likes = response.json().get('likes', [])
                for like in likes:
                    if like['content_id'].startswith('test_content_'):
                        pass
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        response = requests.get(f"{self.BASE_URL.replace('/api/v1', '')}/health")

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_add_like_success(self):
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
        content_id = "test_stats_content_001"
        content_type = "post"

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

        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")

        assert response.status_code == 200
        data = response.json()
        assert data['content_id'] == content_id
        assert data['content_type'] == content_type
        assert 'total_likes' in data
        assert 'total_unlikes' in data
        assert 'user_action' in data

    def test_get_like_stats_not_found(self):
        response = requests.get(f"{self.BASE_URL}/likes/stats/non_existent_content")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data['total_likes'] == 0
            assert data['total_unlikes'] == 0

    def test_get_like_stats_without_auth(self):
        response = requests.get(f"{self.BASE_URL}/likes/stats/some_content")

        assert response.status_code == 200

    def test_get_likes_history_empty(self):
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

        response = requests.get(
            f"{self.BASE_URL}/likes/history",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['likes']) >= 3
        assert data['pagination']['total'] >= 3

    def test_get_likes_history_pagination(self):
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

        response = requests.get(
            f"{self.BASE_URL}/likes/history?page=1&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data['likes']) == 10
        assert data['pagination']['page'] == 1

        response = requests.get(
            f"{self.BASE_URL}/likes/history?page=2&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 2

    def test_get_likes_history_filter_by_content_type(self):
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

        response = requests.get(
            f"{self.BASE_URL}/likes/history?content_type=video",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        video_likes = [like for like in data['likes'] if like['content_type'] == 'video']
        assert len(video_likes) >= 1

    def test_get_likes_history_unauthorized(self):
        response = requests.get(f"{self.BASE_URL}/likes/history")

        assert response.status_code in [401, 403]

    def test_like_workflow_complete(self):
        content_id = "test_workflow_like_content"
        content_type = "post"

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

        response = requests.get(
            f"{self.BASE_URL}/likes/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        likes = response.json()['likes']
        like_ids = [like['id'] for like in likes]
        assert like_id in like_ids

        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_likes'] >= 1

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

        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_unlikes'] >= 1

    def test_multiple_users_like_same_content(self):
        content_id = "test_multi_user_content"
        content_type = "article"

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

        response = requests.post(
            f"{self.BASE_URL}/likes",
            json=like_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code in [201, 409]

        response = requests.get(f"{self.BASE_URL}/likes/stats/{content_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_likes'] >= 1

    def test_like_content_types_coverage(self):
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

            response = requests.get(f"{self.BASE_URL}/likes/stats/test_content_type_{content_type}")
            assert response.status_code == 200

    def test_invalid_json_request(self):
        response = requests.post(
            f"{self.BASE_URL}/likes",
            data="invalid json",
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        response = requests.get(
            f"{self.BASE_URL}/likes/history?limit=1000",
            headers=self.get_auth_headers()
        )

        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 50
