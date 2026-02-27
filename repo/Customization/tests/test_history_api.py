import pytest
import requests
import json
from datetime import datetime, timedelta


class TestHistoryAPI:
    BASE_URL = "http://localhost:8082/api/v1"
    TEST_USER_TOKEN = "test_token_12345"

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            response = requests.get(f"{self.BASE_URL}/history", headers=self.get_auth_headers())
            if response.status_code == 200:
                history_records = response.json().get('history', [])
                for record in history_records:
                    if record.get('content_id', '').startswith('test_'):
                        requests.delete(
                            f"{self.BASE_URL}/history/{record['id']}",
                            headers=self.get_auth_headers()
                        )
        except requests.exceptions.ConnectionError:
            pytest.skip("API Server not running")

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}

    def test_health_check(self):
        response = requests.get(f"{self.BASE_URL.replace('/api/v1', '')}/health")

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_record_history_view_action(self):
        history_data = {
            "action": "view",
            "content_id": "test_content_view_001",
            "content_type": "post",
            "metadata": {
                "duration": 30,
                "device": "mobile"
            },
            "session_id": "test_session_123"
        }

        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['action'] == history_data['action']
        assert data['content_id'] == history_data['content_id']
        assert data['content_type'] == history_data['content_type']
        assert data['metadata'] == history_data['metadata']
        assert data['session_id'] == history_data['session_id']
        assert 'id' in data
        assert 'created_at' in data
        assert 'ip_address' in data
        assert 'user_agent' in data

    def test_record_history_search_action(self):
        history_data = {
            "action": "search",
            "metadata": {
                "query": "python tutorial",
                "results_count": 25
            },
            "session_id": "test_session_456"
        }

        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'search'
        assert data['metadata']['query'] == 'python tutorial'

    def test_record_history_share_action(self):
        history_data = {
            "action": "share",
            "content_id": "test_content_share_001",
            "content_type": "article",
            "metadata": {
                "platform": "twitter",
                "share_type": "link"
            }
        }

        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'share'
        assert data['metadata']['platform'] == 'twitter'

    def test_record_history_download_action(self):
        history_data = {
            "action": "download",
            "content_id": "test_content_download_001",
            "content_type": "video",
            "metadata": {
                "file_size": 1024000,
                "format": "mp4"
            }
        }

        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'download'

    def test_record_history_minimal_data(self):
        history_data = {
            "action": "view"
        }

        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 201
        data = response.json()
        assert data['action'] == 'view'

    def test_record_history_invalid_action(self):
        history_data = {
            "action": "invalid_action",
            "content_id": "test_content_invalid"
        }

        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'error' in error_data

    def test_record_history_unauthorized(self):
        history_data = {
            "action": "view",
            "content_id": "test_content_unauth"
        }

        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data
        )

        assert response.status_code in [401, 403]

    def test_get_history_empty(self):
        response = requests.get(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'history' in data
        assert 'pagination' in data
        assert len(data['history']) == 0

    def test_get_history_with_data(self):
        actions = [
            {"action": "view", "content_id": "test_history_1", "content_type": "post"},
            {"action": "search", "metadata": {"query": "test query"}},
            {"action": "share", "content_id": "test_history_2", "content_type": "article"},
            {"action": "download", "content_id": "test_history_3", "content_type": "video"}
        ]

        created_records = []
        for action_data in actions:
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=action_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201
            created_records.append(response.json())

        response = requests.get(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) >= 4
        assert data['pagination']['total'] >= 4

    def test_get_history_pagination(self):
        for i in range(25):
            history_data = {
                "action": "view",
                "content_id": f"test_pagination_{i+1}",
                "content_type": "post"
            }
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=history_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        response = requests.get(
            f"{self.BASE_URL}/history?page=1&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] >= 25

        response = requests.get(
            f"{self.BASE_URL}/history?page=3&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 3

    def test_get_history_filter_by_action(self):
        actions = ["view", "search", "share", "download", "view"]
        for i, action in enumerate(actions):
            history_data = {
                "action": action,
                "content_id": f"test_filter_action_{i+1}",
                "content_type": "post"
            }
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=history_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        response = requests.get(
            f"{self.BASE_URL}/history?action=view",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        view_records = [record for record in data['history'] if record['action'] == 'view']
        assert len(view_records) >= 2

    def test_get_history_filter_by_content_type(self):
        content_types = ["post", "article", "video", "product"]
        for content_type in content_types:
            history_data = {
                "action": "view",
                "content_id": f"test_filter_type_{content_type}",
                "content_type": content_type
            }
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=history_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201

        response = requests.get(
            f"{self.BASE_URL}/history?content_type=article",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        article_records = [record for record in data['history'] if record['content_type'] == 'article']
        assert len(article_records) >= 1

    def test_get_history_filter_by_date_range(self):
        base_time = datetime.now()


        yesterday_data = {
            "action": "view",
            "content_id": "test_yesterday",
            "content_type": "post"
        }
        response = requests.post(
            f"{self.BASE_URL}/history",
            json=yesterday_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201


        today_data = {
            "action": "view",
            "content_id": "test_today",
            "content_type": "post"
        }
        response = requests.post(
            f"{self.BASE_URL}/history",
            json=today_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201


        today_str = base_time.strftime('%Y-%m-%d')
        response = requests.get(
            f"{self.BASE_URL}/history?start_date={today_str}&end_date={today_str}",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        today_records = [record for record in data['history'] if 'test_today' in record['content_id']]
        assert len(today_records) >= 1

    def test_get_history_filter_by_session(self):

        session_id = "test_session_filter"


        for i in range(3):
            history_data = {
                "action": "view",
                "content_id": f"test_session_{i+1}",
                "content_type": "post",
                "session_id": session_id
            }
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=history_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201


        response = requests.get(
            f"{self.BASE_URL}/history?session_id={session_id}",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        session_records = [record for record in data['history'] if record['session_id'] == session_id]
        assert len(session_records) >= 3

    def test_get_history_unauthorized(self):

        response = requests.get(f"{self.BASE_URL}/history")

        assert response.status_code in [401, 403]

    def test_delete_single_history_success(self):


        history_data = {
            "action": "view",
            "content_id": "test_delete_single",
            "content_type": "post"
        }
        response = requests.post(
            f"{self.BASE_URL}/history",
            json=history_data,
            headers=self.get_auth_headers()
        )
        assert response.status_code == 201
        history_id = response.json()['id']


        response = requests.delete(
            f"{self.BASE_URL}/history/{history_id}",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    def test_delete_single_history_not_found(self):

        response = requests.delete(
            f"{self.BASE_URL}/history/non_existent_id",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 404
        error_data = response.json()
        assert 'error' in error_data

    def test_delete_single_history_unauthorized(self):

        response = requests.delete(f"{self.BASE_URL}/history/some_id")

        assert response.status_code in [401, 403]

    def test_clear_all_history_success(self):


        for i in range(5):
            history_data = {
                "action": "view",
                "content_id": f"test_clear_{i+1}",
                "content_type": "post"
            }
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=history_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201


        response = requests.get(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        initial_count = response.json()['pagination']['total']
        assert initial_count >= 5


        response = requests.delete(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'deleted_count' in data
        assert data['deleted_count'] >= 5

    def test_clear_all_history_empty(self):

        response = requests.delete(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert data['deleted_count'] == 0

    def test_clear_all_history_unauthorized(self):

        response = requests.delete(f"{self.BASE_URL}/history")

        assert response.status_code in [401, 403]

    def test_history_workflow_complete(self):


        actions = [
            {"action": "view", "content_id": "workflow_1", "content_type": "post"},
            {"action": "search", "metadata": {"query": "workflow test"}},
            {"action": "share", "content_id": "workflow_2", "content_type": "article"}
        ]

        created_ids = []
        for action_data in actions:
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=action_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201
            created_ids.append(response.json()['id'])


        response = requests.get(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        history_ids = [record['id'] for record in data['history']]
        for created_id in created_ids:
            assert created_id in history_ids


        response = requests.delete(
            f"{self.BASE_URL}/history/{created_ids[0]}",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200


        response = requests.get(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        history_ids = [record['id'] for record in data['history']]
        assert created_ids[0] not in history_ids


        response = requests.delete(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200


        response = requests.get(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) == 0

    def test_history_actions_coverage(self):

        actions = ["view", "search", "share", "download"]

        for action in actions:
            history_data = {
                "action": action,
                "content_id": f"test_action_{action}",
                "content_type": "post"
            }
            response = requests.post(
                f"{self.BASE_URL}/history",
                json=history_data,
                headers=self.get_auth_headers()
            )
            assert response.status_code == 201


        response = requests.get(
            f"{self.BASE_URL}/history",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        recorded_actions = [record['action'] for record in data['history']]
        for action in actions:
            assert action in recorded_actions

    def test_invalid_json_request(self):

        response = requests.post(
            f"{self.BASE_URL}/history",
            data="invalid json",
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.TEST_USER_TOKEN}'}
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data

    def test_large_pagination_limit(self):

        response = requests.get(
            f"{self.BASE_URL}/history?limit=1000",
            headers=self.get_auth_headers()
        )


        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data['pagination']['limit'] <= 100
