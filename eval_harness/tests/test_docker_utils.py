"""
Tests for eval_harness.docker_utils module.

Uses unittest.mock to avoid actual Docker operations.
"""

import subprocess
import unittest
from unittest.mock import patch, MagicMock

from eval_harness.docker_utils import (
    run_eval_container,
    _force_remove_container,
    stop_container,
    get_container_logs,
    is_docker_available,
    cleanup_all_eval_containers,
    cleanup_all_eval_images,
)
from eval_harness.test_spec import RepoSpec


class TestRunEvalContainer(unittest.TestCase):
    """Test container execution (mocked)."""

    def _make_spec(self) -> RepoSpec:
        return RepoSpec(
            repo_name="Blog",
            lang="python",
            port=8000,
            framework="fastapi",
        )

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=">>>>> DSR_START\nDSR_RESULT=true\n>>>>> DSR_END\n",
            stderr="",
        )
        spec = self._make_spec()
        exit_code, logs = run_eval_container(spec)
        self.assertEqual(exit_code, 0)
        self.assertIn("DSR_RESULT=true", logs)

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_failure_exit_code(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="test output",
            stderr="some error",
        )
        spec = self._make_spec()
        exit_code, logs = run_eval_container(spec)
        self.assertEqual(exit_code, 1)

    @patch("eval_harness.docker_utils._force_remove_container")
    @patch("eval_harness.docker_utils.subprocess.run")
    def test_timeout(self, mock_run, mock_remove):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker run", timeout=900)
        spec = self._make_spec()
        exit_code, logs = run_eval_container(spec)
        self.assertEqual(exit_code, -1)
        self.assertIn("timed out", logs)
        mock_remove.assert_called_once()

    @patch("eval_harness.docker_utils._force_remove_container")
    @patch("eval_harness.docker_utils.subprocess.run")
    def test_exception(self, mock_run, mock_remove):
        mock_run.side_effect = Exception("unexpected error")
        spec = self._make_spec()
        exit_code, logs = run_eval_container(spec)
        self.assertEqual(exit_code, -2)
        self.assertIn("error", logs.lower())

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_docker_run_command_includes_env_vars(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        spec = self._make_spec()
        run_eval_container(spec)
        call_args = mock_run.call_args[0][0]
        # Should include env vars
        self.assertIn("-e", call_args)
        self.assertIn("REPO_LANG=python", call_args)
        self.assertIn("SERVICE_PORT=8000", call_args)


class TestForceRemoveContainer(unittest.TestCase):
    """Test force container removal."""

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_remove_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        _force_remove_container("test-container")
        mock_run.assert_called_once()

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_remove_failure_silent(self, mock_run):
        mock_run.side_effect = Exception("fail")
        # Should not raise
        _force_remove_container("test-container")


class TestStopContainer(unittest.TestCase):
    """Test graceful container stop."""

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_stop_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(stop_container("test-container"))

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_stop_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(stop_container("test-container"))

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_stop_exception(self, mock_run):
        mock_run.side_effect = Exception("fail")
        self.assertFalse(stop_container("test-container"))


class TestGetContainerLogs(unittest.TestCase):
    """Test container log retrieval."""

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_get_logs_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="log output", stderr=""
        )
        logs = get_container_logs("test-container")
        self.assertIn("log output", logs)

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_get_logs_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        logs = get_container_logs("test-container")
        self.assertIsNone(logs)

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_get_logs_exception(self, mock_run):
        mock_run.side_effect = Exception("fail")
        logs = get_container_logs("test-container")
        self.assertIsNone(logs)


class TestIsDockerAvailable(unittest.TestCase):
    """Test Docker availability check."""

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_docker_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(is_docker_available())

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_docker_not_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(is_docker_available())

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_docker_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError("docker not found")
        self.assertFalse(is_docker_available())

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_docker_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker info", timeout=10)
        self.assertFalse(is_docker_available())


class TestCleanupAllEvalContainers(unittest.TestCase):
    """Test bulk container cleanup."""

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_cleanup_containers(self, mock_run):
        # First call lists containers, second call removes them
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout="repogenesis-eval-blog\nrepogenesis-eval-flask\n",
            ),
            MagicMock(returncode=0),
        ]
        count = cleanup_all_eval_containers()
        self.assertEqual(count, 2)

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_cleanup_no_containers(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        count = cleanup_all_eval_containers()
        self.assertEqual(count, 0)

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_cleanup_error(self, mock_run):
        mock_run.side_effect = Exception("fail")
        count = cleanup_all_eval_containers()
        self.assertEqual(count, 0)


class TestCleanupAllEvalImages(unittest.TestCase):
    """Test bulk image cleanup."""

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_cleanup_images(self, mock_run):
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout="repogenesis-eval-blog:latest\nrepogenesis-eval-flask:latest\n",
            ),
            MagicMock(returncode=0),
        ]
        count = cleanup_all_eval_images()
        self.assertEqual(count, 2)

    @patch("eval_harness.docker_utils.subprocess.run")
    def test_cleanup_no_images(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        count = cleanup_all_eval_images()
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
