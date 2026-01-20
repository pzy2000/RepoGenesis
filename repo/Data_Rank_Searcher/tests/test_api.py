"""
Data Rank Searcher API 测试用例

测试覆盖：
1. 数据添加功能
2. 分页功能
3. 排序功能
4. 精确搜索功能
5. 模糊查询功能
6. 组合查询功能
"""

import requests
import pytest
import time
from typing import List, Dict, Any


BASE_URL = "http://localhost:8080"
API_ENDPOINT = f"{BASE_URL}/api/data"


class TestDataManagement:
    """测试数据管理基础功能"""
    
    def test_add_data_success(self):
        """测试添加数据记录成功"""
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
        """测试添加数据时缺少必填字段"""
        payload = {
            "name": "Incomplete Data"
            # 缺少 category 和 score
        }
        
        response = requests.post(API_ENDPOINT, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_get_data_by_id(self):
        """测试根据ID获取单条数据"""
        # 先添加一条数据
        payload = {
            "name": "Test Data",
            "category": "Test",
            "score": 80.0
        }
        create_response = requests.post(API_ENDPOINT, json=payload)
        created_id = create_response.json()["data"]["id"]
        
        # 获取数据
        response = requests.get(f"{API_ENDPOINT}/{created_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == created_id
        assert data["data"]["name"] == payload["name"]
    
    def test_get_data_by_invalid_id(self):
        """测试获取不存在的数据"""
        response = requests.get(f"{API_ENDPOINT}/invalid-id-12345")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
    
    def test_delete_data(self):
        """测试删除数据记录"""
        # 先添加一条数据
        payload = {
            "name": "To Be Deleted",
            "category": "Test",
            "score": 50.0
        }
        create_response = requests.post(API_ENDPOINT, json=payload)
        created_id = create_response.json()["data"]["id"]
        
        # 删除数据
        response = requests.delete(f"{API_ENDPOINT}/{created_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证数据已被删除
        get_response = requests.get(f"{API_ENDPOINT}/{created_id}")
        assert get_response.status_code == 404


class TestPagination:
    """测试分页功能"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """为分页测试准备数据"""
        self.test_ids = []
        # 添加30条测试数据
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
        
        # 清理测试数据
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_pagination_first_page(self):
        """测试获取第一页数据"""
        response = requests.get(API_ENDPOINT, params={"page": 1, "page_size": 10})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) <= 10
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["page_size"] == 10
        assert data["data"]["pagination"]["total_items"] >= 30
    
    def test_pagination_middle_page(self):
        """测试获取中间页数据"""
        response = requests.get(API_ENDPOINT, params={"page": 2, "page_size": 10})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["pagination"]["page"] == 2
        assert len(data["data"]["items"]) <= 10
    
    def test_pagination_last_page(self):
        """测试获取最后一页数据"""
        # 先获取总页数
        first_response = requests.get(API_ENDPOINT, params={"page": 1, "page_size": 10})
        total_pages = first_response.json()["data"]["pagination"]["total_pages"]
        
        # 获取最后一页
        response = requests.get(API_ENDPOINT, params={"page": total_pages, "page_size": 10})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["pagination"]["page"] == total_pages
    
    def test_pagination_different_page_sizes(self):
        """测试不同的页面大小"""
        page_sizes = [5, 10, 20, 50]
        
        for page_size in page_sizes:
            response = requests.get(API_ENDPOINT, params={"page": 1, "page_size": page_size})
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["items"]) <= page_size
            assert data["data"]["pagination"]["page_size"] == page_size
    
    def test_pagination_boundary_conditions(self):
        """测试分页边界条件"""
        # 测试页码为0
        response = requests.get(API_ENDPOINT, params={"page": 0, "page_size": 10})
        # 应该返回错误或默认为第1页
        assert response.status_code in [200, 400]
        
        # 测试超大页码
        response = requests.get(API_ENDPOINT, params={"page": 9999, "page_size": 10})
        assert response.status_code == 200
        data = response.json()
        # 应该返回空数据或最后一页
        assert isinstance(data["data"]["items"], list)


class TestSorting:
    """测试排序功能"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """为排序测试准备数据"""
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
        
        # 等待数据插入完成
        time.sleep(0.1)
        
        yield
        
        # 清理测试数据
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_sort_by_name_ascending(self):
        """测试按名称升序排序"""
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
        # 验证排序顺序
        assert names == sorted(names)
    
    def test_sort_by_name_descending(self):
        """测试按名称降序排序"""
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
        # 验证排序顺序
        assert names == sorted(names, reverse=True)
    
    def test_sort_by_score_ascending(self):
        """测试按分数升序排序"""
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
        # 验证排序顺序
        assert scores == sorted(scores)
    
    def test_sort_by_score_descending(self):
        """测试按分数降序排序"""
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
        # 验证排序顺序
        assert scores == sorted(scores, reverse=True)
    
    def test_sort_by_category(self):
        """测试按类别排序"""
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
        # 验证排序顺序
        assert categories == sorted(categories)
    
    def test_sort_with_pagination(self):
        """测试排序与分页结合"""
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
        
        # 验证第一页的数据是按分数降序排列的
        items = data["data"]["items"]
        scores = [item["score"] for item in items]
        assert scores == sorted(scores, reverse=True)


class TestSearch:
    """测试精确搜索功能"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """为搜索测试准备数据"""
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
        
        # 清理测试数据
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_search_by_category(self):
        """测试按类别精确搜索"""
        response = requests.get(API_ENDPOINT, params={
            "search_field": "category",
            "search_value": "Programming",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        # 所有返回的项都应该属于Programming类别
        for item in items:
            assert item["category"] == "Programming"
        
        # 应该至少找到3条记录
        assert len(items) >= 3
    
    def test_search_by_name(self):
        """测试按名称精确搜索"""
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
        """测试搜索不存在的记录"""
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
        """测试搜索与分页结合"""
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
        
        # 验证分页信息
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["page_size"] == 2


class TestFuzzySearch:
    """测试模糊查询功能"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """为模糊查询测试准备数据"""
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
        
        # 清理测试数据
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_fuzzy_search_by_name(self):
        """测试按名称模糊查询"""
        response = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "Python",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        # 应该找到所有包含"Python"的记录
        assert len(items) >= 3
        
        for item in items:
            assert "Python" in item["name"] or "python" in item["name"].lower()
    
    def test_fuzzy_search_partial_match(self):
        """测试部分匹配的模糊查询"""
        response = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "Java",
            "page_size": 100
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        items = data["data"]["items"]
        # 应该找到Java和JavaScript
        assert len(items) >= 2
    
    def test_fuzzy_search_case_sensitivity(self):
        """测试模糊查询的大小写处理"""
        # 测试小写查询
        response_lower = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "python",
            "page_size": 100
        })
        
        # 测试大写查询
        response_upper = requests.get(API_ENDPOINT, params={
            "fuzzy_field": "name",
            "fuzzy_value": "PYTHON",
            "page_size": 100
        })
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        
        # 大小写不敏感查询应该返回相同数量的结果
        items_lower = response_lower.json()["data"]["items"]
        items_upper = response_upper.json()["data"]["items"]
        
        assert len(items_lower) == len(items_upper)
    
    def test_fuzzy_search_no_match(self):
        """测试模糊查询无匹配结果"""
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
    """测试组合功能"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """为组合功能测试准备数据"""
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
        
        # 清理测试数据
        for test_id in self.test_ids:
            try:
                requests.delete(f"{API_ENDPOINT}/{test_id}")
            except:
                pass
    
    def test_search_with_sort(self):
        """测试搜索与排序结合"""
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
        # 验证所有项都属于Programming类别
        for item in items:
            assert item["category"] == "Programming"
        
        # 验证按分数降序排列
        scores = [item["score"] for item in items]
        assert scores == sorted(scores, reverse=True)
    
    def test_fuzzy_search_with_sort(self):
        """测试模糊查询与排序结合"""
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
        # 验证所有项名称包含Python
        for item in items:
            assert "Python" in item["name"] or "python" in item["name"].lower()
        
        # 验证按分数升序排列
        scores = [item["score"] for item in items]
        assert scores == sorted(scores)
    
    def test_search_with_pagination_and_sort(self):
        """测试搜索、分页和排序三者结合"""
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
        
        # 验证分页
        assert len(data["data"]["items"]) <= 2
        assert data["data"]["pagination"]["page"] == 1
        
        # 验证搜索结果
        items = data["data"]["items"]
        for item in items:
            assert item["category"] == "Programming"
        
        # 验证排序
        names = [item["name"] for item in items]
        assert names == sorted(names)
    
    def test_fuzzy_search_with_pagination(self):
        """测试模糊查询与分页结合"""
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
    """测试边界情况和错误处理"""
    
    def test_invalid_sort_field(self):
        """测试无效的排序字段"""
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "invalid_field",
            "sort_order": "asc"
        })
        
        # 应该返回错误或忽略无效字段
        assert response.status_code in [200, 400]
    
    def test_invalid_sort_order(self):
        """测试无效的排序顺序"""
        response = requests.get(API_ENDPOINT, params={
            "sort_by": "name",
            "sort_order": "invalid_order"
        })
        
        # 应该返回错误或使用默认排序
        assert response.status_code in [200, 400]
    
    def test_large_page_size(self):
        """测试超大页面大小"""
        response = requests.get(API_ENDPOINT, params={
            "page": 1,
            "page_size": 1000
        })
        
        assert response.status_code == 200
        data = response.json()
        # 应该限制最大页面大小为100
        assert len(data["data"]["items"]) <= 100
    
    def test_empty_search_value(self):
        """测试空搜索值"""
        response = requests.get(API_ENDPOINT, params={
            "search_field": "name",
            "search_value": ""
        })
        
        assert response.status_code in [200, 400]
    
    def test_special_characters_in_fuzzy_search(self):
        """测试模糊查询中的特殊字符"""
        # 先添加包含特殊字符的数据
        payload = {
            "name": "C++ Programming",
            "category": "Programming",
            "score": 90.0
        }
        create_response = requests.post(API_ENDPOINT, json=payload)
        
        if create_response.status_code in [200, 201]:
            created_id = create_response.json()["data"]["id"]
            
            # 测试搜索
            response = requests.get(API_ENDPOINT, params={
                "fuzzy_field": "name",
                "fuzzy_value": "C++",
                "page_size": 100
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # 清理
            requests.delete(f"{API_ENDPOINT}/{created_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

