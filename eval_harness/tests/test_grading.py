"""
Tests for eval_harness.grading module.
"""

import unittest

from eval_harness.grading import grade_dsr, grade_pass_at_1, grade_repo
from eval_harness.constants import (
    DSR_START_MARKER,
    DSR_END_MARKER,
    DSR_RESULT_PREFIX,
    DSR_MESSAGE_PREFIX,
    TEST_START_MARKER,
    TEST_END_MARKER,
)
from eval_harness.test_spec import RepoSpec


class TestGradeDsr(unittest.TestCase):
    """Test DSR grading from container logs."""

    def test_success(self):
        logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}true
{DSR_MESSAGE_PREFIX}Service started successfully
{DSR_END_MARKER}
"""
        result = grade_dsr(logs)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Service started successfully")

    def test_failure(self):
        logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}false
{DSR_MESSAGE_PREFIX}Service failed to start
{DSR_END_MARKER}
"""
        result = grade_dsr(logs)
        self.assertFalse(result["success"])
        self.assertIn("failed", result["message"].lower())

    def test_no_markers(self):
        logs = "some random output without any markers"
        result = grade_dsr(logs)
        self.assertFalse(result["success"])
        self.assertIn("No DSR markers", result["message"])

    def test_result_yes(self):
        """'yes' should also be treated as success."""
        logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}yes
{DSR_MESSAGE_PREFIX}OK
{DSR_END_MARKER}
"""
        result = grade_dsr(logs)
        self.assertTrue(result["success"])

    def test_result_1(self):
        """'1' should also be treated as success."""
        logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}1
{DSR_MESSAGE_PREFIX}OK
{DSR_END_MARKER}
"""
        result = grade_dsr(logs)
        self.assertTrue(result["success"])

    def test_empty_logs(self):
        result = grade_dsr("")
        self.assertFalse(result["success"])


class TestGradePassAt1(unittest.TestCase):
    """Test Pass@1 grading from container logs."""

    def test_python_all_passed(self):
        logs = f"""
{TEST_START_MARKER}
Running pytest...
test_api.py::test_create PASSED
test_api.py::test_list PASSED
===== 2 passed in 1.00s =====
{TEST_END_MARKER}
"""
        result = grade_pass_at_1(logs, "python")
        self.assertEqual(result["passed"], 2)
        self.assertEqual(result["total"], 2)
        self.assertAlmostEqual(result["score"], 1.0)

    def test_python_mixed(self):
        logs = f"""
{TEST_START_MARKER}
===== 3 passed, 2 failed in 2.00s =====
{TEST_END_MARKER}
"""
        result = grade_pass_at_1(logs, "python")
        self.assertEqual(result["passed"], 3)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(result["total"], 5)
        self.assertAlmostEqual(result["score"], 0.6)

    def test_java_results(self):
        logs = f"""
{TEST_START_MARKER}
Tests run: 10, Failures: 2, Errors: 1, Skipped: 0
{TEST_END_MARKER}
"""
        result = grade_pass_at_1(logs, "java")
        self.assertEqual(result["passed"], 7)
        self.assertEqual(result["total"], 10)
        self.assertAlmostEqual(result["score"], 0.7)

    def test_no_test_markers(self):
        """When no markers, should try to parse the entire log."""
        logs = "===== 5 passed in 1.00s ====="
        result = grade_pass_at_1(logs, "python")
        self.assertEqual(result["passed"], 5)

    def test_zero_total(self):
        logs = f"{TEST_START_MARKER}\nno tests ran\n{TEST_END_MARKER}"
        result = grade_pass_at_1(logs, "python")
        self.assertEqual(result["total"], 0)
        self.assertAlmostEqual(result["score"], 0.0)

    def test_unknown_lang(self):
        result = grade_pass_at_1("anything", "rust")
        self.assertEqual(result["total"], 0)
        self.assertAlmostEqual(result["score"], 0.0)


class TestGradeRepo(unittest.TestCase):
    """Test the full repo grading."""

    def setUp(self):
        self.spec = RepoSpec(
            repo_name="Blog",
            lang="python",
            port=8000,
            framework="fastapi",
        )

    def test_full_grading(self):
        logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}true
{DSR_MESSAGE_PREFIX}Service started successfully
{DSR_END_MARKER}
{TEST_START_MARKER}
===== 5 passed, 1 failed in 3.00s =====
{TEST_END_MARKER}
"""
        ac_result = {
            "total_apis": 10,
            "implemented_apis": 7,
            "score": 0.7,
        }
        result = grade_repo(self.spec, logs, exit_code=0, ac_result=ac_result)
        self.assertEqual(result["repo_name"], "Blog")
        self.assertEqual(result["lang"], "python")
        self.assertTrue(result["dsr"]["success"])
        self.assertEqual(result["pass_at_1"]["passed"], 5)
        self.assertEqual(result["api_coverage"]["total_apis"], 10)
        self.assertAlmostEqual(result["api_coverage"]["score"], 0.7)

    def test_grading_without_ac(self):
        logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}false
{DSR_MESSAGE_PREFIX}Failed
{DSR_END_MARKER}
"""
        result = grade_repo(self.spec, logs, exit_code=1)
        self.assertEqual(result["repo_name"], "Blog")
        self.assertFalse(result["dsr"]["success"])
        self.assertNotIn("api_coverage", result)

    def test_grading_with_exit_code(self):
        result = grade_repo(self.spec, logs="", exit_code=-1)
        self.assertEqual(result["exit_code"], -1)


if __name__ == "__main__":
    unittest.main()
