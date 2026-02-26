"""
Tests for eval_harness.api_coverage module.
"""

import tempfile
import unittest
from pathlib import Path

from eval_harness.api_coverage import (
    extract_api_endpoints_from_readme,
    search_implementation,
    calculate_repo_api_coverage,
    _build_search_patterns,
)


class TestExtractApiEndpoints(unittest.TestCase):
    """Test README endpoint extraction."""

    def test_explicit_endpoints(self):
        readme = """# API
GET /api/items - List all items
POST /api/items - Create an item
DELETE /api/items/{id} - Delete an item
"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
            f.write(readme)
            f.flush()
            endpoints = extract_api_endpoints_from_readme(Path(f.name))

        methods = {e["method"] for e in endpoints}
        self.assertIn("GET", methods)
        self.assertIn("POST", methods)
        self.assertIn("DELETE", methods)
        self.assertTrue(len(endpoints) >= 3)

    def test_markdown_table(self):
        readme = """# Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/users | List users |
| POST | /api/users | Create user |
"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
            f.write(readme)
            f.flush()
            endpoints = extract_api_endpoints_from_readme(Path(f.name))

        self.assertTrue(len(endpoints) >= 2)
        paths = {e["path"] for e in endpoints}
        self.assertIn("/api/users", paths)

    def test_code_block_endpoints(self):
        readme = """# API

```
GET /api/health - Health check
POST /api/data - Submit data
```
"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
            f.write(readme)
            f.flush()
            endpoints = extract_api_endpoints_from_readme(Path(f.name))

        self.assertTrue(len(endpoints) >= 2)

    def test_no_endpoints(self):
        readme = "# My Project\nThis is a simple project with no API."
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
            f.write(readme)
            f.flush()
            endpoints = extract_api_endpoints_from_readme(Path(f.name))

        self.assertEqual(len(endpoints), 0)

    def test_nonexistent_file(self):
        endpoints = extract_api_endpoints_from_readme(Path("/tmp/nonexistent_12345.md"))
        self.assertEqual(len(endpoints), 0)

    def test_deduplication(self):
        """Same endpoint mentioned twice should only appear once."""
        readme = """# API
GET /api/items - List items
GET /api/items - List all items
"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
            f.write(readme)
            f.flush()
            endpoints = extract_api_endpoints_from_readme(Path(f.name))

        get_items = [e for e in endpoints if e["method"] == "GET" and "/api/items" in e["path"]]
        self.assertEqual(len(get_items), 1)

    def test_feature_fallback(self):
        """When no explicit endpoints, should fall back to feature patterns."""
        readme = """# Features
- User Login
- User Register
- Create new post
- Delete existing post
"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
            f.write(readme)
            f.flush()
            endpoints = extract_api_endpoints_from_readme(Path(f.name))

        # Should find features
        feature_endpoints = [e for e in endpoints if e["method"] == "FEATURE"]
        self.assertTrue(len(feature_endpoints) > 0)

    def test_all_http_methods(self):
        readme = """# API
GET /a - get
POST /b - post
PUT /c - put
DELETE /d - delete
PATCH /e - patch
"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
            f.write(readme)
            f.flush()
            endpoints = extract_api_endpoints_from_readme(Path(f.name))

        methods = {e["method"] for e in endpoints}
        self.assertEqual(methods, {"GET", "POST", "PUT", "DELETE", "PATCH"})


class TestBuildSearchPatterns(unittest.TestCase):
    """Test pattern building for endpoint searching."""

    def test_get_endpoint_patterns(self):
        endpoint = {"method": "GET", "path": "/api/items", "description": "List items"}
        patterns = _build_search_patterns(endpoint)
        self.assertTrue(len(patterns) > 0)
        # Should have Flask/FastAPI patterns
        pattern_str = " ".join(patterns)
        self.assertIn("get", pattern_str.lower())

    def test_feature_patterns(self):
        endpoint = {"method": "FEATURE", "path": "User Login", "description": "User Login"}
        patterns = _build_search_patterns(endpoint)
        self.assertTrue(len(patterns) > 0)
        # Should have snake_case and concatenated versions
        pattern_str = " ".join(patterns)
        self.assertIn("user_login", pattern_str)


class TestSearchImplementation(unittest.TestCase):
    """Test static code search for endpoint implementation."""

    def test_flask_get_endpoint_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_py = Path(tmpdir) / "app.py"
            app_py.write_text("""
from flask import Flask
app = Flask(__name__)

@app.get("/api/items")
def list_items():
    return []
""")
            endpoint = {"method": "GET", "path": "/api/items", "description": ""}
            self.assertTrue(search_implementation(Path(tmpdir), endpoint))

    def test_fastapi_post_endpoint_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_py = Path(tmpdir) / "main.py"
            main_py.write_text("""
from fastapi import FastAPI
app = FastAPI()

@app.post("/api/users")
def create_user(user: dict):
    return user
""")
            endpoint = {"method": "POST", "path": "/api/users", "description": ""}
            self.assertTrue(search_implementation(Path(tmpdir), endpoint))

    def test_endpoint_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_py = Path(tmpdir) / "app.py"
            app_py.write_text("""
from flask import Flask
app = Flask(__name__)

@app.get("/api/health")
def health():
    return {"status": "ok"}
""")
            endpoint = {"method": "POST", "path": "/api/users", "description": ""}
            self.assertFalse(search_implementation(Path(tmpdir), endpoint))

    def test_excludes_test_directories(self):
        """Endpoints in test/ directories should not count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "tests"
            test_dir.mkdir()
            test_file = test_dir / "test_api.py"
            test_file.write_text("""
@app.get("/api/items")
def test_items():
    pass
""")
            endpoint = {"method": "GET", "path": "/api/items", "description": ""}
            self.assertFalse(search_implementation(Path(tmpdir), endpoint))

    def test_feature_search(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_py = Path(tmpdir) / "app.py"
            app_py.write_text("""
def user_login(username, password):
    # Login logic
    pass

@app.post("/login")
def login_endpoint():
    return user_login(request.form["username"], request.form["password"])
""")
            endpoint = {"method": "FEATURE", "path": "User Login", "description": "User Login"}
            self.assertTrue(search_implementation(Path(tmpdir), endpoint))

    def test_java_spring_boot_endpoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ctrl = Path(tmpdir) / "Controller.java"
            ctrl.write_text("""
@RestController
@RequestMapping("/api")
public class ItemController {
    @GetMapping("/items")
    public List<Item> getItems() {
        return itemService.findAll();
    }
}
""")
            endpoint = {"method": "GET", "path": "/api/items", "description": ""}
            self.assertTrue(search_implementation(Path(tmpdir), endpoint))

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            endpoint = {"method": "GET", "path": "/api/items", "description": ""}
            self.assertFalse(search_implementation(Path(tmpdir), endpoint))

    def test_non_source_files_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # .txt file should be ignored
            txt_file = Path(tmpdir) / "routes.txt"
            txt_file.write_text("@app.get('/api/items')\n/api/items")
            endpoint = {"method": "GET", "path": "/api/items", "description": ""}
            self.assertFalse(search_implementation(Path(tmpdir), endpoint))


class TestCalculateRepoApiCoverage(unittest.TestCase):
    """Test the full API coverage calculation."""

    def test_full_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            readme_path = repo_path / "README.md"
            readme_path.write_text("""# API
GET /api/items - List items
POST /api/items - Create item
""")
            app_py = repo_path / "app.py"
            app_py.write_text("""
from flask import Flask
app = Flask(__name__)

@app.get("/api/items")
def list_items():
    return []

@app.post("/api/items")
def create_item():
    return {}
""")
            result = calculate_repo_api_coverage(repo_path, readme_path)
            self.assertEqual(result["total_apis"], 2)
            self.assertEqual(result["implemented_apis"], 2)
            self.assertAlmostEqual(result["score"], 1.0)

    def test_partial_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            readme_path = repo_path / "README.md"
            readme_path.write_text("""# API
GET /api/items - List items
POST /api/items - Create item
DELETE /api/items/{id} - Delete item
""")
            app_py = repo_path / "app.py"
            app_py.write_text("""
from flask import Flask
app = Flask(__name__)

@app.get("/api/items")
def list_items():
    return []
""")
            result = calculate_repo_api_coverage(repo_path, readme_path)
            self.assertEqual(result["total_apis"], 3)
            self.assertEqual(result["implemented_apis"], 1)
            self.assertAlmostEqual(result["score"], 1 / 3, places=3)

    def test_no_endpoints_in_readme(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            readme_path = repo_path / "README.md"
            readme_path.write_text("# Simple Project\nNo API here.")
            result = calculate_repo_api_coverage(repo_path, readme_path)
            self.assertEqual(result["total_apis"], 0)
            self.assertAlmostEqual(result["score"], 0.0)

    def test_nonexistent_readme(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = calculate_repo_api_coverage(
                Path(tmpdir), Path("/tmp/nonexistent_12345.md")
            )
            self.assertEqual(result["total_apis"], 0)


if __name__ == "__main__":
    unittest.main()
