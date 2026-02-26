"""
Tests for eval_harness.docker_build module.

Uses unittest.mock to avoid actual Docker operations.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from eval_harness.docker_build import (
    prepare_build_context,
    build_image,
    remove_image,
    image_exists,
)
from eval_harness.test_spec import RepoSpec


class TestPrepareBuildContext(unittest.TestCase):
    """Test Docker build context preparation."""

    def _make_spec(self, tmpdir: Path) -> RepoSpec:
        # Create a generated repo with some files
        generated = tmpdir / "generated" / "Blog"
        generated.mkdir(parents=True)
        (generated / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n")
        (generated / "requirements.txt").write_text("flask\n")

        # Create golden tests
        golden = tmpdir / "golden" / "Blog" / "tests"
        golden.mkdir(parents=True)
        (golden / "test_api.py").write_text("def test_hello(): pass\n")

        return RepoSpec(
            repo_name="Blog",
            lang="python",
            port=8000,
            framework="fastapi",
            generated_repo_path=generated,
            golden_test_path=golden,
        )

    def test_copies_generated_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            spec = self._make_spec(tmpdir)
            context = tmpdir / "context"
            context.mkdir()
            prepare_build_context(spec, context)

            # Check generated repo was copied
            self.assertTrue((context / "generated_repo" / "app.py").exists())
            self.assertTrue((context / "generated_repo" / "requirements.txt").exists())

    def test_copies_golden_tests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            spec = self._make_spec(tmpdir)
            context = tmpdir / "context"
            context.mkdir()
            prepare_build_context(spec, context)

            # Check golden tests were copied
            self.assertTrue((context / "golden_tests" / "test_api.py").exists())

    def test_copies_dockerfile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            spec = self._make_spec(tmpdir)
            context = tmpdir / "context"
            context.mkdir()
            prepare_build_context(spec, context)

            # Check Dockerfile was copied
            self.assertTrue((context / "Dockerfile").exists())

    def test_copies_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            spec = self._make_spec(tmpdir)
            context = tmpdir / "context"
            context.mkdir()
            prepare_build_context(spec, context)

            # Check entrypoint.sh was copied
            self.assertTrue((context / "entrypoint.sh").exists())

    def test_missing_generated_repo_creates_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            spec = RepoSpec(
                repo_name="Blog",
                lang="python",
                port=8000,
                framework="fastapi",
                generated_repo_path=tmpdir / "nonexistent",
                golden_test_path=tmpdir / "nonexistent_tests",
            )
            context = tmpdir / "context"
            context.mkdir()
            prepare_build_context(spec, context)
            self.assertTrue((context / "generated_repo").is_dir())
            self.assertTrue((context / "golden_tests").is_dir())

    def test_excludes_git_and_pycache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            generated = tmpdir / "generated" / "Blog"
            generated.mkdir(parents=True)
            (generated / "app.py").write_text("pass")
            (generated / ".git").mkdir()
            (generated / ".git" / "config").write_text("x")
            (generated / "__pycache__").mkdir()
            (generated / "__pycache__" / "app.cpython-310.pyc").write_text("x")

            golden = tmpdir / "golden"
            golden.mkdir()

            spec = RepoSpec(
                repo_name="Blog", lang="python", port=8000, framework="fastapi",
                generated_repo_path=generated,
                golden_test_path=golden,
            )
            context = tmpdir / "context"
            context.mkdir()
            prepare_build_context(spec, context)
            self.assertFalse((context / "generated_repo" / ".git").exists())
            self.assertFalse((context / "generated_repo" / "__pycache__").exists())


class TestBuildImage(unittest.TestCase):
    """Test Docker image building (mocked)."""

    @patch("eval_harness.docker_build.subprocess.run")
    @patch("eval_harness.docker_build.prepare_build_context")
    def test_build_success(self, mock_prepare, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        spec = RepoSpec(
            repo_name="Blog", lang="python", port=8000, framework="fastapi",
            generated_repo_path=Path("/tmp/gen/Blog"),
        )
        success, msg = build_image(spec)
        self.assertTrue(success)
        self.assertIn("repogenesis-eval-blog", msg)

    @patch("eval_harness.docker_build.subprocess.run")
    @patch("eval_harness.docker_build.prepare_build_context")
    def test_build_failure(self, mock_prepare, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="ERROR: build failed"
        )
        spec = RepoSpec(
            repo_name="Blog", lang="python", port=8000, framework="fastapi",
            generated_repo_path=Path("/tmp/gen/Blog"),
        )
        success, msg = build_image(spec)
        self.assertFalse(success)
        self.assertIn("Build failed", msg)

    @patch("eval_harness.docker_build.subprocess.run")
    @patch("eval_harness.docker_build.prepare_build_context")
    def test_build_timeout(self, mock_prepare, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker build", timeout=600)
        spec = RepoSpec(
            repo_name="Blog", lang="python", port=8000, framework="fastapi",
            generated_repo_path=Path("/tmp/gen/Blog"),
        )
        success, msg = build_image(spec)
        self.assertFalse(success)
        self.assertIn("timed out", msg)


class TestRemoveImage(unittest.TestCase):
    """Test Docker image removal (mocked)."""

    @patch("eval_harness.docker_build.subprocess.run")
    def test_remove_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        # Should not raise
        remove_image("repogenesis-eval-blog:latest")
        mock_run.assert_called_once()

    @patch("eval_harness.docker_build.subprocess.run")
    def test_remove_failure_silent(self, mock_run):
        mock_run.side_effect = Exception("docker not found")
        # Should not raise (cleanup failures are silent)
        remove_image("repogenesis-eval-blog:latest")


class TestImageExists(unittest.TestCase):
    """Test Docker image existence check (mocked)."""

    @patch("eval_harness.docker_build.subprocess.run")
    def test_image_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(image_exists("repogenesis-eval-blog:latest"))

    @patch("eval_harness.docker_build.subprocess.run")
    def test_image_not_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(image_exists("repogenesis-eval-blog:latest"))

    @patch("eval_harness.docker_build.subprocess.run")
    def test_image_exists_error(self, mock_run):
        mock_run.side_effect = Exception("docker error")
        self.assertFalse(image_exists("repogenesis-eval-blog:latest"))


if __name__ == "__main__":
    unittest.main()
