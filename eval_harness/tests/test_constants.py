"""
Tests for eval_harness.constants module.
"""

import unittest
from eval_harness.constants import (
    REPO_SPECS,
    TOTAL_PYTHON_REPOS,
    TOTAL_JAVA_REPOS,
    TOTAL_VERIFIED_REPOS,
    get_repo_lang,
    get_repo_port,
    get_python_repos,
    get_java_repos,
    get_startup_timeout,
    get_test_timeout,
    get_build_timeout,
    get_success_patterns,
    PYTHON_STARTUP_TIMEOUT,
    JAVA_STARTUP_TIMEOUT,
    PYTHON_TEST_TIMEOUT,
    JAVA_TEST_TIMEOUT,
    PYTHON_BUILD_TIMEOUT,
    JAVA_BUILD_TIMEOUT,
    PYTHON_SUCCESS_PATTERNS,
    JAVA_SUCCESS_PATTERNS,
    HEALTH_CHECK_PATHS,
    SOURCE_EXTENSIONS,
    EXCLUDED_DIRS,
    DSR_START_MARKER,
    DSR_END_MARKER,
    TEST_START_MARKER,
    TEST_END_MARKER,
    DOCKER_IMAGE_PREFIX,
    BASE_IMAGE_PYTHON,
    BASE_IMAGE_JAVA,
)


class TestRepoSpecs(unittest.TestCase):
    """Test the REPO_SPECS dictionary."""

    def test_repo_count(self):
        """REPO_SPECS should contain exactly 30 repos."""
        self.assertEqual(len(REPO_SPECS), TOTAL_VERIFIED_REPOS)

    def test_python_repo_count(self):
        """Should have exactly 22 Python repos."""
        python_repos = {k: v for k, v in REPO_SPECS.items() if v["lang"] == "python"}
        self.assertEqual(len(python_repos), TOTAL_PYTHON_REPOS)

    def test_java_repo_count(self):
        """Should have exactly 8 Java repos."""
        java_repos = {k: v for k, v in REPO_SPECS.items() if v["lang"] == "java"}
        self.assertEqual(len(java_repos), TOTAL_JAVA_REPOS)

    def test_all_repos_have_required_keys(self):
        """Every repo spec must have lang, port, framework."""
        for name, spec in REPO_SPECS.items():
            with self.subTest(repo=name):
                self.assertIn("lang", spec, f"{name} missing 'lang'")
                self.assertIn("port", spec, f"{name} missing 'port'")
                self.assertIn("framework", spec, f"{name} missing 'framework'")

    def test_lang_values(self):
        """All lang values must be 'python' or 'java'."""
        for name, spec in REPO_SPECS.items():
            with self.subTest(repo=name):
                self.assertIn(spec["lang"], ("python", "java"))

    def test_port_values_are_positive_integers(self):
        """All ports must be positive integers."""
        for name, spec in REPO_SPECS.items():
            with self.subTest(repo=name):
                self.assertIsInstance(spec["port"], int)
                self.assertGreater(spec["port"], 0)
                self.assertLess(spec["port"], 65536)

    def test_specific_repos_exist(self):
        """Spot-check that key repos exist."""
        expected_repos = [
            "Blog", "flask", "GameBackend", "javalin-online-judge",
            "springboot-chat-gateway", "quarkus-blog-cms",
        ]
        for name in expected_repos:
            with self.subTest(repo=name):
                self.assertIn(name, REPO_SPECS)

    def test_blog_spec(self):
        """Blog should be Python, port 8000, FastAPI."""
        spec = REPO_SPECS["Blog"]
        self.assertEqual(spec["lang"], "python")
        self.assertEqual(spec["port"], 8000)
        self.assertEqual(spec["framework"], "fastapi")

    def test_javalin_online_judge_spec(self):
        """javalin-online-judge should be Java, port 7000, javalin."""
        spec = REPO_SPECS["javalin-online-judge"]
        self.assertEqual(spec["lang"], "java")
        self.assertEqual(spec["port"], 7000)
        self.assertEqual(spec["framework"], "javalin")


class TestHelperFunctions(unittest.TestCase):
    """Test the helper functions in constants."""

    def test_get_repo_lang_python(self):
        self.assertEqual(get_repo_lang("Blog"), "python")

    def test_get_repo_lang_java(self):
        self.assertEqual(get_repo_lang("javalin-online-judge"), "java")

    def test_get_repo_lang_unknown(self):
        with self.assertRaises(ValueError):
            get_repo_lang("nonexistent-repo")

    def test_get_repo_port(self):
        self.assertEqual(get_repo_port("Blog"), 8000)
        self.assertEqual(get_repo_port("flask"), 5000)

    def test_get_repo_port_unknown(self):
        with self.assertRaises(ValueError):
            get_repo_port("nonexistent-repo")

    def test_get_python_repos(self):
        python_repos = get_python_repos()
        self.assertEqual(len(python_repos), TOTAL_PYTHON_REPOS)
        for spec in python_repos.values():
            self.assertEqual(spec["lang"], "python")

    def test_get_java_repos(self):
        java_repos = get_java_repos()
        self.assertEqual(len(java_repos), TOTAL_JAVA_REPOS)
        for spec in java_repos.values():
            self.assertEqual(spec["lang"], "java")

    def test_get_startup_timeout(self):
        self.assertEqual(get_startup_timeout("python"), PYTHON_STARTUP_TIMEOUT)
        self.assertEqual(get_startup_timeout("java"), JAVA_STARTUP_TIMEOUT)
        # Unknown lang defaults to python
        self.assertEqual(get_startup_timeout("unknown"), PYTHON_STARTUP_TIMEOUT)

    def test_get_test_timeout(self):
        self.assertEqual(get_test_timeout("python"), PYTHON_TEST_TIMEOUT)
        self.assertEqual(get_test_timeout("java"), JAVA_TEST_TIMEOUT)

    def test_get_build_timeout(self):
        self.assertEqual(get_build_timeout("python"), PYTHON_BUILD_TIMEOUT)
        self.assertEqual(get_build_timeout("java"), JAVA_BUILD_TIMEOUT)

    def test_get_success_patterns(self):
        self.assertEqual(get_success_patterns("python"), PYTHON_SUCCESS_PATTERNS)
        self.assertEqual(get_success_patterns("java"), JAVA_SUCCESS_PATTERNS)


class TestConstantValues(unittest.TestCase):
    """Test that constant values are reasonable."""

    def test_markers_are_strings(self):
        for marker in [DSR_START_MARKER, DSR_END_MARKER, TEST_START_MARKER, TEST_END_MARKER]:
            self.assertIsInstance(marker, str)
            self.assertTrue(len(marker) > 0)

    def test_markers_have_swebench_format(self):
        """Markers should start with >>>>> per SWE-bench convention."""
        for marker in [DSR_START_MARKER, DSR_END_MARKER, TEST_START_MARKER, TEST_END_MARKER]:
            self.assertTrue(marker.startswith(">>>>>"))

    def test_docker_image_prefix(self):
        self.assertEqual(DOCKER_IMAGE_PREFIX, "repogenesis-eval")

    def test_base_images(self):
        self.assertIn("python", BASE_IMAGE_PYTHON)
        self.assertIn("maven", BASE_IMAGE_JAVA)

    def test_health_check_paths_not_empty(self):
        self.assertTrue(len(HEALTH_CHECK_PATHS) > 0)
        for path in HEALTH_CHECK_PATHS:
            self.assertTrue(path.startswith("/"))

    def test_source_extensions(self):
        self.assertIn(".py", SOURCE_EXTENSIONS)
        self.assertIn(".java", SOURCE_EXTENSIONS)

    def test_excluded_dirs(self):
        self.assertIn("__pycache__", EXCLUDED_DIRS)
        self.assertIn(".git", EXCLUDED_DIRS)
        self.assertIn("node_modules", EXCLUDED_DIRS)

    def test_timeout_ordering(self):
        """Java timeouts should be >= Python timeouts."""
        self.assertGreaterEqual(JAVA_STARTUP_TIMEOUT, PYTHON_STARTUP_TIMEOUT)
        self.assertGreaterEqual(JAVA_TEST_TIMEOUT, PYTHON_TEST_TIMEOUT)
        self.assertGreaterEqual(JAVA_BUILD_TIMEOUT, PYTHON_BUILD_TIMEOUT)


if __name__ == "__main__":
    unittest.main()
