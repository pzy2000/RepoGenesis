import pytest
import requests
import json
from datetime import datetime


class TestFavoritesAPI:
    BASE_URL = "http://localhost:8082/api/v1"
    TEST_USER_TOKEN = "test_token_12345"

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
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
            pytest.skip("API server is not running")

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        response = requests.get(f"{self.BASE_URL.replace('/api/v1', '')}/health")

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_add_favorite_success(self):
        favorite_data = {
            "content_id": "test_content_001",
            "content_type": "post",
            "category": "test_category"
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
        favorite_data = {
            "content_id": "test_content_duplicate",
            "content_type": "video",
            "category": "test_category"
        }

        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        first_id = response.json()['id']

        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code in [201, 409]

    def test_add_favorite_invalid_content_type(self):
        favorite_data = {
            "content_id": "test_content_invalid",
            "content_type": "invalid_type",
            "category": "test_category"
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
        favorite_data = {
            "category": "test_category"
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
        favorites_data = [
            {"content_id": "test_list_1", "content_type": "post", "category": "news"},
            {"content_id": "test_list_2", "content_type": "article", "category": "tech"},
            {"content_id": "test_list_3", "content_type": "video", "category": "entertainment"}
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
        for i in range(15):
            favorite_data = {
                "content_id": f"test_pagination_{i+1}",
                "content_type": "post",
                "category": "test"
            }
            response = requests.post(
                f"{self.BASE_URL}/favorites",
                json=favorite_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        response = requests.get(
            f"{self.BASE_URL}/favorites?page=1&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data['favorites']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 15

        response = requests.get(
            f"{self.BASE_URL}/favorites?page=2&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 2

    def test_get_favorites_filter_by_content_type(self):
        content_types = ["post", "article", "video", "product"]
        for content_type in content_types:
            favorite_data = {
                "content_id": f"test_filter_{content_type}",
                "content_type": content_type,
                "category": "test"
            }
            response = requests.post(
                f"{self.BASE_URL}/favorites",
                json=favorite_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        response = requests.get(
            f"{self.BASE_URL}/favorites?content_type=article",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        article_favorites = [f for f in data['favorites'] if f['content_type'] == 'article']
        assert len(article_favorites) >= 1

    def test_get_favorites_filter_by_category(self):
        categories = ["news", "tech", "entertainment", "education"]
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

        response = requests.get(
            f"{self.BASE_URL}/favorites?category=tech",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        tech_favorites = [f for f in data['favorites'] if f['category'] == 'tech']
        assert len(tech_favorites) >= 1

    def test_delete_favorite_success(self):
        favorite_data = {
            "content_id": "test_delete_001",
            "content_type": "post",
            "category": "test_delete"
        }
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        favorite_id = response.json()['id']

        response = requests.delete(
            f"{self.BASE_URL}/favorites/{favorite_id}",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    def test_delete_favorite_not_found(self):
        response = requests.delete(
            f"{self.BASE_URL}/favorites/non_existent_id",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data

    def test_delete_favorite_unauthorized(self):
        response = requests.delete(f"{self.BASE_URL}/favorites/some_id")

        assert response.status_code in [401, 403]

    def test_favorites_workflow_complete(self):
        favorite_data = {
            "content_id": "test_workflow_content",
            "content_type": "article",
            "category": "test_workflow"
        }
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            json=favorite_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        favorite_id = response.json()['id']

        response = requests.get(
            f"{self.BASE_URL}/favorites?content_type=article",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        favorites = response.json()['favorites']
        favorite_ids = [f['id'] for f in favorites]
        assert favorite_id in favorite_ids

        response = requests.delete(
            f"{self.BASE_URL}/favorites/{favorite_id}",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200

        response = requests.get(
            f"{self.BASE_URL}/favorites?content_type=article",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        favorites = response.json()['favorites']
        favorite_ids = [f['id'] for f in favorites]
        assert favorite_id not in favorite_ids

    def test_invalid_json_request(self):
        response = requests.post(
            f"{self.BASE_URL}/favorites",
            data="invalid json",
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):
        response = requests.get(
            f"{self.BASE_URL}/favorites?limit=1000",
            headers=self.get_auth_headers()
        )

        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100
