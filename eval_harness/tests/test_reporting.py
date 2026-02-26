"""
Tests for eval_harness.reporting module.
"""

import json
import tempfile
import unittest
from pathlib import Path

from eval_harness.reporting import (
    compute_summary,
    generate_report,
    save_report,
    save_intermediate_result,
    load_intermediate_results,
    format_summary_table,
)


def _make_result(
    repo_name: str,
    lang: str = "python",
    dsr_success: bool = True,
    pass_score: float = 0.8,
    passed: int = 4,
    total: int = 5,
    ac_score: float = 0.7,
    total_apis: int = 10,
    impl_apis: int = 7,
):
    """Helper to create a mock result dict."""
    result = {
        "repo_name": repo_name,
        "lang": lang,
        "port": 8000,
        "framework": "any",
        "exit_code": 0,
        "dsr": {"success": dsr_success, "message": "ok" if dsr_success else "fail"},
        "pass_at_1": {
            "passed": passed,
            "failed": total - passed,
            "errors": 0,
            "skipped": 0,
            "total": total,
            "score": pass_score,
        },
    }
    if total_apis > 0:
        result["api_coverage"] = {
            "total_apis": total_apis,
            "implemented_apis": impl_apis,
            "score": ac_score,
        }
    return result


class TestComputeSummary(unittest.TestCase):
    """Test summary computation."""

    def test_empty_results(self):
        summary = compute_summary([])
        self.assertEqual(summary["total_repos"], 0)
        self.assertAlmostEqual(summary["avg_pass_at_1"], 0.0)

    def test_single_python_result(self):
        results = [_make_result("Blog", lang="python", pass_score=0.8, dsr_success=True, ac_score=0.7)]
        summary = compute_summary(results)
        self.assertEqual(summary["total_repos"], 1)
        self.assertEqual(summary["python_repos"], 1)
        self.assertEqual(summary["java_repos"], 0)
        self.assertAlmostEqual(summary["avg_pass_at_1"], 0.8)
        self.assertAlmostEqual(summary["deployment_success_rate"], 1.0)
        self.assertAlmostEqual(summary["avg_api_coverage"], 0.7)

    def test_mixed_results(self):
        results = [
            _make_result("Blog", lang="python", pass_score=1.0, dsr_success=True, ac_score=1.0),
            _make_result("flask", lang="python", pass_score=0.5, dsr_success=False, ac_score=0.5),
            _make_result("javalin-online-judge", lang="java", pass_score=0.6, dsr_success=True, ac_score=0.8),
        ]
        summary = compute_summary(results)
        self.assertEqual(summary["total_repos"], 3)
        self.assertEqual(summary["python_repos"], 2)
        self.assertEqual(summary["java_repos"], 1)
        # avg pass@1: (1.0 + 0.5 + 0.6) / 3 = 0.7
        self.assertAlmostEqual(summary["avg_pass_at_1"], 0.7, places=3)
        # DSR: 2/3
        self.assertAlmostEqual(summary["deployment_success_rate"], 2 / 3, places=3)

    def test_by_lang_breakdown(self):
        results = [
            _make_result("Blog", lang="python", pass_score=0.8, dsr_success=True),
            _make_result("flask", lang="python", pass_score=0.4, dsr_success=False),
            _make_result("joj", lang="java", pass_score=0.9, dsr_success=True),
        ]
        summary = compute_summary(results)
        # Python pass@1: (0.8 + 0.4) / 2 = 0.6
        self.assertAlmostEqual(summary["pass_at_1_by_lang"]["python"], 0.6, places=3)
        # Java pass@1: 0.9
        self.assertAlmostEqual(summary["pass_at_1_by_lang"]["java"], 0.9, places=3)
        # Python DSR: 1/2 = 0.5
        self.assertAlmostEqual(summary["dsr_by_lang"]["python"], 0.5, places=3)
        # Java DSR: 1/1 = 1.0
        self.assertAlmostEqual(summary["dsr_by_lang"]["java"], 1.0, places=3)

    def test_no_tests_repos_excluded_from_pass1(self):
        """Repos with total=0 should not affect avg pass@1."""
        results = [
            _make_result("Blog", pass_score=0.8, passed=4, total=5),
            _make_result("flask", pass_score=0.0, passed=0, total=0),
        ]
        summary = compute_summary(results)
        # Only Blog should count
        self.assertAlmostEqual(summary["avg_pass_at_1"], 0.8, places=3)


class TestGenerateReport(unittest.TestCase):
    """Test report generation."""

    def test_basic_report(self):
        results = [_make_result("Blog")]
        report = generate_report(results)
        self.assertIn("metadata", report)
        self.assertIn("summary", report)
        self.assertIn("results", report)
        self.assertEqual(len(report["results"]), 1)

    def test_metadata_defaults(self):
        report = generate_report([], metadata={})
        self.assertIn("timestamp", report["metadata"])
        self.assertIn("harness_version", report["metadata"])

    def test_custom_metadata(self):
        meta = {"model_name": "gpt-4o", "agent_name": "metagpt"}
        report = generate_report([], metadata=meta)
        self.assertEqual(report["metadata"]["model_name"], "gpt-4o")
        self.assertEqual(report["metadata"]["agent_name"], "metagpt")

    def test_none_metadata(self):
        report = generate_report([])
        self.assertIn("metadata", report)


class TestSaveReport(unittest.TestCase):
    """Test report saving to disk."""

    def test_save_and_read(self):
        report = generate_report([_make_result("Blog")])
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            save_report(report, output_path)
            self.assertTrue(output_path.exists())
            loaded = json.loads(output_path.read_text())
            self.assertEqual(loaded["results"][0]["repo_name"], "Blog")

    def test_save_creates_parent_dirs(self):
        report = generate_report([])
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "report.json"
            save_report(report, output_path)
            self.assertTrue(output_path.exists())


class TestIntermediateResults(unittest.TestCase):
    """Test intermediate result saving and loading."""

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result1 = _make_result("Blog")
            result2 = _make_result("flask")
            save_intermediate_result(result1, output_dir, "Blog")
            save_intermediate_result(result2, output_dir, "flask")
            loaded = load_intermediate_results(output_dir)
            self.assertEqual(len(loaded), 2)
            names = {r["repo_name"] for r in loaded}
            self.assertIn("Blog", names)
            self.assertIn("flask", names)

    def test_load_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loaded = load_intermediate_results(Path(tmpdir))
            self.assertEqual(loaded, [])

    def test_load_nonexistent_dir(self):
        loaded = load_intermediate_results(Path("/tmp/nonexistent_12345"))
        self.assertEqual(loaded, [])

    def test_overwrite_intermediate(self):
        """Saving twice should overwrite the previous."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result1 = _make_result("Blog", pass_score=0.5)
            result2 = _make_result("Blog", pass_score=0.9)
            save_intermediate_result(result1, output_dir, "Blog")
            save_intermediate_result(result2, output_dir, "Blog")
            loaded = load_intermediate_results(output_dir)
            self.assertEqual(len(loaded), 1)
            self.assertAlmostEqual(loaded[0]["pass_at_1"]["score"], 0.9)


class TestFormatSummaryTable(unittest.TestCase):
    """Test human-readable table formatting."""

    def test_nonempty_table(self):
        results = [
            _make_result("Blog", dsr_success=True, pass_score=0.8),
            _make_result("flask", dsr_success=False, pass_score=0.5),
        ]
        table = format_summary_table(results)
        self.assertIsInstance(table, str)
        self.assertIn("Blog", table)
        self.assertIn("flask", table)
        self.assertIn("PASS", table)
        self.assertIn("FAIL", table)
        self.assertIn("RepoGenesis", table)

    def test_empty_results(self):
        table = format_summary_table([])
        self.assertIsInstance(table, str)
        self.assertIn("0", table)


if __name__ == "__main__":
    unittest.main()
