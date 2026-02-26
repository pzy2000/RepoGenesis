"""
RepoGenesis Evaluation Harness - Docker Container Utilities

Manages container lifecycle: create, run, collect logs, cleanup.
Uses subprocess calls to docker CLI (no docker SDK dependency required).
"""

import logging
import subprocess
import threading
import time
from typing import Tuple, Optional

from eval_harness.constants import (
    DOCKER_RESULTS_DIR,
    DOCKER_MEMORY_LIMIT,
    CONTAINER_TIMEOUT,
)
from eval_harness.test_spec import RepoSpec

logger = logging.getLogger(__name__)


def run_eval_container(
    spec: RepoSpec,
    timeout: int = CONTAINER_TIMEOUT,
    verbose: bool = False,
) -> Tuple[int, str]:
    """
    Run an evaluation container for a single repo.

    The container runs the entrypoint.sh script which:
    1. Starts the service (DSR check)
    2. Waits for it to be ready
    3. Runs tests (Pass@1)
    4. Cleans up and exits

    Args:
        spec: RepoSpec for this repo.
        timeout: Overall container timeout in seconds.
        verbose: Whether to stream container logs to stdout.

    Returns:
        Tuple of (exit_code, full_log_output).
        exit_code is -1 on timeout, -2 on other errors.
    """
    cmd = [
        "docker", "run",
        "--rm",                                 # Auto-remove container
        "--name", spec.container_name,
        "--network", "bridge",                  # Isolated network
        "--memory", DOCKER_MEMORY_LIMIT,        # Memory limit
        "-e", f"REPO_LANG={spec.lang}",
        "-e", f"SERVICE_PORT={spec.port}",
        "-e", f"STARTUP_TIMEOUT={spec.startup_timeout}",
        "-e", f"TEST_TIMEOUT={spec.test_timeout}",
        spec.image_tag,
    ]

    logger.info("[%s] Starting container: %s", spec.repo_name, spec.container_name)

    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
        )

        logs = result.stdout + "\n" + result.stderr
        exit_code = result.returncode

        if verbose:
            print(f"\n--- Container logs for {spec.repo_name} ---")
            print(logs)
            print(f"--- End logs (exit code: {exit_code}) ---\n")

        logger.info(
            "[%s] Container finished with exit code %d",
            spec.repo_name, exit_code,
        )
        return exit_code, logs

    except subprocess.TimeoutExpired:
        logger.error(
            "[%s] Container timed out after %ds, killing...",
            spec.repo_name, timeout,
        )
        # Kill the timed-out container
        _force_remove_container(spec.container_name)
        return -1, f"Container timed out after {timeout}s"

    except Exception as e:
        logger.error("[%s] Container error: %s", spec.repo_name, e)
        _force_remove_container(spec.container_name)
        return -2, f"Container error: {e}"


def _force_remove_container(container_name: str) -> None:
    """
    Force-remove a Docker container.

    Args:
        container_name: Name of the container to remove.
    """
    try:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            timeout=15,
            capture_output=True,
            text=True,
        )
    except Exception:
        pass  # Best-effort cleanup


def stop_container(container_name: str, timeout: int = 10) -> bool:
    """
    Gracefully stop a Docker container.

    Args:
        container_name: Name of the container.
        timeout: Seconds to wait before force-killing.

    Returns:
        True if stopped successfully.
    """
    try:
        result = subprocess.run(
            ["docker", "stop", "-t", str(timeout), container_name],
            timeout=timeout + 10,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_container_logs(container_name: str) -> Optional[str]:
    """
    Get logs from a running or stopped container.

    Args:
        container_name: Name of the container.

    Returns:
        Log output, or None if the container doesn't exist.
    """
    try:
        result = subprocess.run(
            ["docker", "logs", container_name],
            timeout=30,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout + "\n" + result.stderr
        return None
    except Exception:
        return None


def is_docker_available() -> bool:
    """
    Check if Docker is installed and the daemon is running.

    Returns:
        True if Docker is available and ready.
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            timeout=10,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def cleanup_all_eval_containers() -> int:
    """
    Remove all containers with the repogenesis-eval prefix.

    Returns:
        Number of containers removed.
    """
    try:
        # List containers with our prefix
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=repogenesis-eval",
             "--format", "{{.Names}}"],
            timeout=15,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return 0

        containers = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]
        if not containers:
            return 0

        # Remove all at once
        subprocess.run(
            ["docker", "rm", "-f"] + containers,
            timeout=30,
            capture_output=True,
            text=True,
        )
        return len(containers)
    except Exception:
        return 0


def cleanup_all_eval_images() -> int:
    """
    Remove all Docker images with the repogenesis-eval prefix.

    Returns:
        Number of images removed.
    """
    try:
        result = subprocess.run(
            ["docker", "images", "--filter", "reference=repogenesis-eval-*",
             "--format", "{{.Repository}}:{{.Tag}}"],
            timeout=15,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return 0

        images = [i.strip() for i in result.stdout.strip().split("\n") if i.strip()]
        if not images:
            return 0

        subprocess.run(
            ["docker", "rmi", "-f"] + images,
            timeout=60,
            capture_output=True,
            text=True,
        )
        return len(images)
    except Exception:
        return 0
