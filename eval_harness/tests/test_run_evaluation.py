"""
Tests for eval_harness.run_evaluation module.

Integration-level tests with mocked Docker operations.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from eval_harness.run_evaluation import (
    evaluate_single_repo,
    run_evaluation,
    parse_args,
    setup_logging,
    main,
)
from eval_harness.test_spec import RepoSpec
from eval_harness.constants import (
    DSR_START_MARKER,
    DSR_END_MARKER,
    DSR_RESULT_PREFIX,
    DSR_MESSAGE_PREFIX,
    TEST_START_MARKER,
    TEST_END_MARKER,
)
from eval_harness.progress import _NoOpDisplay


def _noop_display(**kwargs):
    """Return a _NoOpDisplay for use in tests (avoids rich Live takeover)."""
    return _NoOpDisplay()


class TestParseArgs(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_required_predictions_dir(self):
        args = parse_args(["--predictions_dir", "/tmp/preds"])
        self.assertEqual(args.predictions_dir, Path("/tmp/preds"))

    def test_defaults(self):
        args = parse_args(["--predictions_dir", "/tmp/preds"])
        self.assertFalse(args.verbose)
        self.assertFalse(args.skip_docker)
        self.assertFalse(args.no_cache)
        self.assertFalse(args.keep_images)
        self.assertFalse(args.resume)
        self.assertFalse(args.cleanup)
        self.assertIsNone(args.repo_names)
        self.assertIsNone(args.lang)
        self.assertIsNone(args.model_name)
        self.assertIsNone(args.agent_name)

    def test_repo_names(self):
        args = parse_args(["--predictions_dir", "/tmp/preds", "--repo_names", "Blog", "flask"])
        self.assertEqual(args.repo_names, ["Blog", "flask"])

    def test_lang_filter(self):
        args = parse_args(["--predictions_dir", "/tmp/preds", "--lang", "python"])
        self.assertEqual(args.lang, "python")

    def test_verbose_flag(self):
        args = parse_args(["--predictions_dir", "/tmp/preds", "-v"])
        self.assertTrue(args.verbose)

    def test_skip_docker(self):
        args = parse_args(["--predictions_dir", "/tmp/preds", "--skip_docker"])
        self.assertTrue(args.skip_docker)

    def test_metadata_args(self):
        args = parse_args([
            "--predictions_dir", "/tmp/preds",
            "--model_name", "gpt-4o",
            "--agent_name", "metagpt",
        ])
        self.assertEqual(args.model_name, "gpt-4o")
        self.assertEqual(args.agent_name, "metagpt")

    def test_missing_required_arg(self):
        with self.assertRaises(SystemExit):
            parse_args([])


class TestSetupLogging(unittest.TestCase):
    """Test logging configuration."""

    def test_setup_default(self):
        # Should not raise
        setup_logging(verbose=False)

    def test_setup_verbose(self):
        setup_logging(verbose=True)

    def test_setup_with_logfile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(verbose=True, log_file=log_file)
            # Log file may not exist until something is logged
            # but parent dir should be created


class TestEvaluateSingleRepo(unittest.TestCase):
    """Test single repo evaluation with mocks."""

    def _make_spec(self, tmpdir: Path) -> RepoSpec:
        generated = tmpdir / "Blog"
        generated.mkdir()
        (generated / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n")

        readme = tmpdir / "readme" / "Blog" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text("# Blog\nGET /api/posts - List posts\n")

        return RepoSpec(
            repo_name="Blog",
            lang="python",
            port=8000,
            framework="fastapi",
            generated_repo_path=generated,
            readme_path=readme,
        )

    def test_skip_docker_returns_ac_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spec = self._make_spec(Path(tmpdir))
            result = evaluate_single_repo(spec, skip_docker=True)
            self.assertEqual(result["repo_name"], "Blog")
            self.assertFalse(result["dsr"]["success"])
            self.assertIn("skipped", result["dsr"]["message"].lower())
            self.assertIn("elapsed_seconds", result)

    @patch("eval_harness.run_evaluation.run_eval_container")
    @patch("eval_harness.run_evaluation.build_image")
    def test_full_evaluation_success(self, mock_build, mock_run):
        mock_build.return_value = (True, "repogenesis-eval-blog:latest")
        container_logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}true
{DSR_MESSAGE_PREFIX}Service started
{DSR_END_MARKER}
{TEST_START_MARKER}
===== 3 passed in 1.00s =====
{TEST_END_MARKER}
"""
        mock_run.return_value = (0, container_logs)

        with tempfile.TemporaryDirectory() as tmpdir:
            spec = self._make_spec(Path(tmpdir))
            with patch("eval_harness.run_evaluation.remove_image"):
                result = evaluate_single_repo(spec)

        self.assertEqual(result["repo_name"], "Blog")
        self.assertTrue(result["dsr"]["success"])
        self.assertEqual(result["pass_at_1"]["passed"], 3)

    @patch("eval_harness.run_evaluation.build_image")
    def test_build_failure(self, mock_build):
        mock_build.return_value = (False, "Build failed: out of memory")

        with tempfile.TemporaryDirectory() as tmpdir:
            spec = self._make_spec(Path(tmpdir))
            result = evaluate_single_repo(spec)

        self.assertEqual(result["exit_code"], -3)
        self.assertIn("build_error", result)

    def test_on_stage_callback_called_skip_docker(self):
        """Verify on_stage is invoked for AC and SKIP_DOCKER stages."""
        stages_called = []

        with tempfile.TemporaryDirectory() as tmpdir:
            spec = self._make_spec(Path(tmpdir))
            result = evaluate_single_repo(
                spec, skip_docker=True, on_stage=stages_called.append,
            )

        self.assertIn("Computing API Coverage", stages_called)
        self.assertIn("AC only (Docker skipped)", stages_called)
        self.assertEqual(result["repo_name"], "Blog")

    @patch("eval_harness.run_evaluation.run_eval_container")
    @patch("eval_harness.run_evaluation.build_image")
    def test_on_stage_callback_called_full(self, mock_build, mock_run):
        """Verify on_stage is invoked for all 5 stages in a full evaluation."""
        from eval_harness.progress import (
            STAGE_AC, STAGE_BUILD, STAGE_CONTAINER, STAGE_GRADE, STAGE_CLEANUP,
        )

        mock_build.return_value = (True, "image:latest")
        mock_run.return_value = (0, f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}true
{DSR_MESSAGE_PREFIX}OK
{DSR_END_MARKER}
{TEST_START_MARKER}
===== 1 passed in 1.00s =====
{TEST_END_MARKER}
""")

        stages_called = []
        with tempfile.TemporaryDirectory() as tmpdir:
            spec = self._make_spec(Path(tmpdir))
            with patch("eval_harness.run_evaluation.remove_image"):
                result = evaluate_single_repo(
                    spec, on_stage=stages_called.append,
                )

        self.assertEqual(
            stages_called,
            [STAGE_AC, STAGE_BUILD, STAGE_CONTAINER, STAGE_GRADE, STAGE_CLEANUP],
        )

    def test_on_stage_none_does_not_crash(self):
        """Passing on_stage=None (default) should not raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec = self._make_spec(Path(tmpdir))
            result = evaluate_single_repo(spec, skip_docker=True, on_stage=None)
            self.assertEqual(result["repo_name"], "Blog")


class TestRunEvaluation(unittest.TestCase):
    """Test the full evaluation pipeline with mocks."""

    @patch("eval_harness.run_evaluation.create_progress_display", side_effect=_noop_display)
    @patch("eval_harness.run_evaluation.is_docker_available", return_value=True)
    @patch("eval_harness.run_evaluation.run_eval_container")
    @patch("eval_harness.run_evaluation.build_image")
    @patch("eval_harness.run_evaluation.remove_image")
    def test_full_pipeline(self, mock_remove, mock_build, mock_run, mock_docker, mock_display):
        mock_build.return_value = (True, "image:latest")
        container_logs = f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}true
{DSR_MESSAGE_PREFIX}OK
{DSR_END_MARKER}
{TEST_START_MARKER}
===== 2 passed in 1.00s =====
{TEST_END_MARKER}
"""
        mock_run.return_value = (0, container_logs)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create predictions
            predictions_dir = tmpdir / "predictions"
            (predictions_dir / "Blog").mkdir(parents=True)
            (predictions_dir / "Blog" / "app.py").write_text("pass")

            # Create readme dir
            readme_dir = tmpdir / "readme"
            (readme_dir / "Blog").mkdir(parents=True)
            (readme_dir / "Blog" / "README.md").write_text("# Blog\nGET /api/posts - List\n")

            output_dir = tmpdir / "output"

            report = run_evaluation(
                predictions_dir=predictions_dir,
                output_dir=output_dir,
                readme_dir_python=readme_dir,
                repo_names=["Blog"],
            )

        self.assertIn("summary", report)
        self.assertIn("results", report)
        self.assertEqual(len(report["results"]), 1)
        self.assertEqual(report["results"][0]["repo_name"], "Blog")

    def test_skip_docker_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            predictions_dir = tmpdir / "predictions"
            (predictions_dir / "Blog").mkdir(parents=True)
            (predictions_dir / "Blog" / "app.py").write_text("pass")

            readme_dir = tmpdir / "readme"
            (readme_dir / "Blog").mkdir(parents=True)
            (readme_dir / "Blog" / "README.md").write_text("# Blog\nGET /api/posts - List\n")

            output_dir = tmpdir / "output"

            with patch("eval_harness.run_evaluation.create_progress_display", side_effect=_noop_display):
                report = run_evaluation(
                    predictions_dir=predictions_dir,
                    output_dir=output_dir,
                    readme_dir_python=readme_dir,
                    repo_names=["Blog"],
                    skip_docker=True,
                )

        self.assertEqual(len(report["results"]), 1)
        self.assertFalse(report["results"][0]["dsr"]["success"])

    def test_empty_predictions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            predictions_dir = tmpdir / "predictions"
            predictions_dir.mkdir()
            output_dir = tmpdir / "output"

            with patch("eval_harness.run_evaluation.create_progress_display", side_effect=_noop_display):
                report = run_evaluation(
                    predictions_dir=predictions_dir,
                    output_dir=output_dir,
                    skip_docker=True,
                )

        self.assertEqual(len(report["results"]), 0)
        self.assertEqual(report["summary"]["total_repos"], 0)

    @patch("eval_harness.run_evaluation.create_progress_display", side_effect=_noop_display)
    @patch("eval_harness.run_evaluation.is_docker_available", return_value=True)
    @patch("eval_harness.run_evaluation.run_eval_container")
    @patch("eval_harness.run_evaluation.build_image")
    @patch("eval_harness.run_evaluation.remove_image")
    def test_resume(self, mock_remove, mock_build, mock_run, mock_docker, mock_display):
        mock_build.return_value = (True, "image:latest")
        mock_run.return_value = (0, f"""
{DSR_START_MARKER}
{DSR_RESULT_PREFIX}true
{DSR_MESSAGE_PREFIX}OK
{DSR_END_MARKER}
{TEST_START_MARKER}
===== 1 passed in 1.00s =====
{TEST_END_MARKER}
""")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            predictions_dir = tmpdir / "predictions"
            (predictions_dir / "Blog").mkdir(parents=True)
            (predictions_dir / "Blog" / "app.py").write_text("pass")
            (predictions_dir / "flask").mkdir(parents=True)
            (predictions_dir / "flask" / "app.py").write_text("pass")

            output_dir = tmpdir / "output"

            # Save a fake intermediate result for Blog
            intermediate_dir = output_dir / "intermediate"
            intermediate_dir.mkdir(parents=True)
            blog_result = {
                "repo_name": "Blog",
                "lang": "python",
                "port": 8000,
                "framework": "fastapi",
                "exit_code": 0,
                "dsr": {"success": True, "message": "OK"},
                "pass_at_1": {"passed": 5, "failed": 0, "errors": 0, "skipped": 0, "total": 5, "score": 1.0},
            }
            (intermediate_dir / "Blog.json").write_text(json.dumps(blog_result))

            readme_dir = tmpdir / "readme"
            (readme_dir / "Blog").mkdir(parents=True)
            (readme_dir / "Blog" / "README.md").write_text("# Blog")
            (readme_dir / "flask").mkdir(parents=True)
            (readme_dir / "flask" / "README.md").write_text("# Flask")

            report = run_evaluation(
                predictions_dir=predictions_dir,
                output_dir=output_dir,
                readme_dir_python=readme_dir,
                repo_names=["Blog", "flask"],
                resume=True,
            )

        # Should have 2 results (Blog from resume, flask from eval)
        self.assertEqual(len(report["results"]), 2)
        # Blog should still have score 1.0 (from resume)
        blog = next(r for r in report["results"] if r["repo_name"] == "Blog")
        self.assertAlmostEqual(blog["pass_at_1"]["score"], 1.0)


class TestMain(unittest.TestCase):
    """Test the main entry point."""

    @patch("eval_harness.run_evaluation.cleanup_all_eval_containers", return_value=3)
    @patch("eval_harness.run_evaluation.cleanup_all_eval_images", return_value=2)
    def test_cleanup_mode(self, mock_imgs, mock_containers):
        # Should not raise
        main(["--predictions_dir", "/tmp/fake", "--cleanup"])

    @patch("eval_harness.run_evaluation.run_evaluation")
    def test_main_calls_run_evaluation(self, mock_run_eval):
        mock_run_eval.return_value = {"summary": {}, "results": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions = Path(tmpdir) / "preds"
            predictions.mkdir()
            main([
                "--predictions_dir", str(predictions),
                "--skip_docker",
                "--output_dir", str(Path(tmpdir) / "output"),
            ])
        mock_run_eval.assert_called_once()


if __name__ == "__main__":
    unittest.main()
