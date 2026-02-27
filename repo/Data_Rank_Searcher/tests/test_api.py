import requests
import pytest
import time
from typing import List, Dict, Any


BASE_URL = "http://localhost:8080"
API_ENDPOINT = f"{BASE_URL}/api/data"


class TestDataManagement:
    def test_add_data_success(self):
        payload = {
            "name": "Python Programming",
            "category": "Programming",
            "score": 95.5,
            "description": "A comprehensive guide to Python",
            "tags": ["python", "programming", "tutorial"]
        }
        
        response = requests.post(API_ENDPOINT, json=payload)
        
        assert response.status_code == 200 or response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["category"] == payload["category"]
        assert data["data"]["score"] == payload["score"]
        assert "id" in data["data"]
        assert "created_at" in data["data"]
    
    def test_add_data_missing_required_field(self):
        payload = {
            "name": "Incomplete Data"
        }
        
        response = requests.post(API_ENDPOINT, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_get_data_by_id(self):
        payload = {
            "name": "Test Data",
            "category": "Test",
            "score": 80.0
        }
        create_response = requests.post(API_ENDPOINT, json=payload)
        created_id = create_response.json()["data"]["id"]
        
        response = requests.get(f"{API_ENDPOINT}/{created_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == created_id
        assert data["data"]["name"] == payload["name"]
    
    def test_get_data_by_invalid_id(self):
        response = requests.get(f"{API_ENDPOINT}/invalid-id-12345")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
    
    def test_delete_data(self):
        payload = {
            "name": "To Be Deleted",
            "category": "Test",
            "score": 50.0
        }
        create_response = requests.post(API_ENDPOINT, json=payload)
        created_id = create_response.json()["data"]["id"]
        
        response = requests.delete(f"{API_ENDPOINT}/{created_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        get_response = requests.get(f"{API_ENDPOINT}/{created_id}")
        assert get_response.status_code == 404


class TestPagination:
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        for i in range(30):
            payload = {
                "name": f"Item {i+1:02d}",
                "category": f"Category {(i % 3) + 1}",
                "score": 50 + (i * 1.5)
            }
            response = requests.post(API_ENDPOINT, json=payload)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()["data"]["id"])
        
        yield
        
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_pagination_first_page(self):
        response = requests.get(API_ENDPOINT, params={"page": 1, "page_size": 10})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) <= 10
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["page_size"] == 10
        assert data["data"]["pagination"]["total_items"] >= 30
    
    def test_pagination_middle_page(self):
        response = requests.get(API_ENDPOINT, params={"page": 2, "page_size": 10})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["pagination"]["page"] == 2
        assert len(data["data"]["items"]) <= 10
    
    def test_pagination_last_page(self):
        first_response = requests.get(API_ENDPOINT, params={"page": 1, "page_size": 10})
        total_pages = first_response.json()["data"]["pagination"]["total_pages"]
        response = requests.get(API_ENDPOINT, params={"page": total_pages, "page_size": 10})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["pagination"]["page"] == total_pages
    
    def test_pagination_different_page_sizes(self):
        page_sizes = [5, 10, 20, 50]
        
        for page_size in page_sizes:
            response = requests.get(API_ENDPOINT, params={"page": 1, "page_size": page_size})
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["items"]) <= page_size
            assert data["data"]["pagination"]["page_size"] == page_size
    
    def test_pagination_boundary_conditions(self):
        response = requests.get(API_ENDPOINT, params={"page": 0, "page_size": 10})
        assert response.status_code in [200, 400]
        
        response = requests.get(API_ENDPOINT, params={"page": 9999, "page_size": 10})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"]["items"], list)


class TestSorting:
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [
            {"name": "Zebra", "category": "Animal", "score": 85.0},
            {"name": "Apple", "category": "Fruit", "score": 92.0},
            {"name": "Book", "category": "Object", "score": 78.5},
            {"name": "Car", "category": "Vehicle", "score": 95.0},
            {"name": "Dog", "category": "Animal", "score": 88.0}
        ]
        
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()["data"]["id"])
        
        time.sleep(0.1)
        
        yield
        
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_sort_by_name_ascending(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "name",
            "sort_order": "asc",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        names = [item["name"] for item in items]
        assert names == sorted(names)
    
    def test_sort_by_name_descending(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "name",
            "sort_order": "desc",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        names = [item["name"] for item in items]
        assert names == sorted(names, reverse=True)
    
    def test_sort_by_score_ascending(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "score",
            "sort_order": "asc",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        scores = [item["score"] for item in items]
        assert scores == sorted(scores)
    
    def test_sort_by_score_descending(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "score",
            "sort_order": "desc",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        scores = [item["score"] for item in items]
        assert scores == sorted(scores, reverse=True)
    
    def test_sort_by_category(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "category",
            "sort_order": "asc",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        categories = [item["category"] for item in items]
        assert categories == sorted(categories)
    
    def test_sort_with_pagination(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "score",
            "sort_order": "desc",
            "page": 1,
            "page_size": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) <= 3
        
        items = data["data"]["items"]
        scores = [item["score"] for item in items]
        assert scores == sorted(scores, reverse=True)


class TestSearch:
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [
            {"name": "Python Guide", "category": "Programming", "score": 90.0},
            {"name": "Java Tutorial", "category": "Programming", "score": 85.0},
            {"name": "Data Science", "category": "Science", "score": 92.0},
            {"name": "Machine Learning", "category": "AI", "score": 95.0},
            {"name": "Web Development", "category": "Programming", "score": 88.0}
        ]
        
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()["data"]["id"])
        
        time.sleep(0.1)
        
        yield
        
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_search_by_category(self):
        response = requests.get(API_ENDPOINT, params={
            "search_field": "category",
            "search_value": "Programming",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        for item in items:
            assert item["category"] == "Programming"
        
        assert len(items) >= 3
    
    def test_search_by_name(self):
        response = requests.get(API_ENDPOINT, params={
            "search_field": "name",
            "search_value": "Python Guide",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        assert len(items) >= 1
        assert items[0]["name"] == "Python Guide"
    
    def test_search_no_results(self):
        response = requests.get(API_ENDPOINT, params={
            "search_field": "category",
            "search_value": "NonExistentCategory",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 0
    
    def test_search_with_pagination(self):
        response = requests.get(API_ENDPOINT, params={
            "search_field": "category",
            "search_value": "Programming",
            "page": 1,
            "page_size": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) <= 2
        
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["page_size"] == 2


class TestFuzzySearch:
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [
            {"name": "Introduction to Python", "category": "Programming", "score": 90.0},
            {"name": "Advanced Python", "category": "Programming", "score": 95.0},
            {"name": "Python for Data Science", "category": "Science", "score": 92.0},
            {"name": "Java Programming", "category": "Programming", "score": 85.0},
            {"name": "JavaScript Basics", "category": "Web", "score": 88.0}
        ]
        
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()["data"]["id"])
        
        time.sleep(0.1)
        
        yield
        
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_fuzzy_search_by_name(self):
        response = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "Python",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        assert len(items) >= 3
        
        for item in items:
            assert "Python" in item["name"] or "python" in item["name"].lower()
    
    def test_fuzzy_search_partial_match(self):
        response = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "Java",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        assert len(items) >= 2
    
    def test_fuzzy_search_case_sensitivity(self):
        response_lower = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "python",
            "page_size": 100
        })
        
        response_upper = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "PYTHON",
            "page_size": 100
        })
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        
        items_lower = response_lower.json()["data"]["items"]
        items_upper = response_upper.json()["data"]["items"]
        
        assert len(items_lower) == len(items_upper)
    
    def test_fuzzy_search_no_match(self):
        response = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "Nonexistent",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 0


class TestCombinedFeatures:
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.test_ids = []
        test_data = [
            {"name": "Python Basics", "category": "Programming", "score": 85.0},
            {"name": "Python Advanced", "category": "Programming", "score": 95.0},
            {"name": "Python Expert", "category": "Programming", "score": 92.0},
            {"name": "Java Basics", "category": "Programming", "score": 80.0},
            {"name": "Data Analysis", "category": "Science", "score": 90.0}
        ]
        
        for item in test_data:
            response = requests.post(API_ENDPOINT, json=item)
            if response.status_code in [200, 201]:
                self.test_ids.append(response.json()["data"]["id"])
        
        time.sleep(0.1)
        
        yield
        
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_search_with_sort(self):
        response = requests.get(API_ENDPOINT, params={
            "search_field": "category",
            "search_value": "Programming",
            "sort_by": "score",
            "sort_order": "desc",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        for item in items:
            assert item["category"] == "Programming"
        
        scores = [item["score"] for item in items]
        assert scores == sorted(scores, reverse=True)
    
    def test_fuzzy_search_with_sort(self):
        response = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "Python",
            "sort_by": "score",
            "sort_order": "asc",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        for item in items:
            assert "Python" in item["name"] or "python" in item["name"].lower()
        
        scores = [item["score"] for item in items]
        assert scores == sorted(scores)
    
    def test_search_with_pagination_and_sort(self):
        response = requests.get(API_ENDPOINT, params={
            "search_field": "category",
            "search_value": "Programming",
            "sort_by": "name",
            "sort_order": "asc",
            "page": 1,
            "page_size": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        assert len(data["data"]["items"]) <= 2
        assert data["data"]["pagination"]["page"] == 1
        
        items = data["data"]["items"]
        for item in items:
            assert item["category"] == "Programming"
        
        names = [item["name"] for item in items]
        assert names == sorted(names)
    
    def test_fuzzy_search_with_pagination(self):
        response = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "Python",
            "page": 1,
            "page_size": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        assert len(data["data"]["items"]) <= 2
        assert data["data"]["pagination"]["page_size"] == 2


class TestEdgeCases:
    
    def test_invalid_sort_field(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "invalid_field",
            "sort_order": "asc"
        })
        
        assert response.status_code in [200, 400]
    
    def test_invalid_sort_order(self):
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "name",
            "sort_order": "invalid_order"
        })
        
        assert response.status_code in [200, 400]
    
    def test_large_page_size(self):
        response = requests.get(API_ENDPOINT, params={
            "page": 1,
            "page_size": 1000
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 100
    
    def test_empty_search_value(self):
        response = requests.get(API_ENDPOINT, params={
            "search_field": "name",
            "search_value": ""
        })
        
        assert response.status_code in [200, 400]
    
    def test_special_characters_in_fuzzy_search(self):
        payload = {
            "name": "C++ Programming",
            "category": "Programming",
            "score": 90.0
        }
        create_response = requests.post(API_ENDPOINT, json=payload)
        
        if create_response.status_code in [200, 201]:
            created_id = create_response.json()["data"]["id"]
            
            response = requests.get(API_ENDPOINT, params={
                "fuzzy_field": "name",
                "fuzzy_value": "C++",
                "page_size": 100
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            requests.delete(f"{API_ENDPOINT}/{created_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

