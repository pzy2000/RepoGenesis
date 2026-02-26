"""
RepoGenesis Evaluation Harness - Docker Image Building

Builds Docker images for repo evaluation. Creates a temporary build context
with generated code + golden oracle tests, then builds using the appropriate
Dockerfile (Python or Java).

Modeled after SWE-bench's docker_build.py.
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional

from eval_harness.test_spec import RepoSpec
from eval_harness.constants import DOCKER_MEMORY_LIMIT

logger = logging.getLogger("eval_harness.docker_build")


def _get_harness_dir() -> Path:
    """Get the eval_harness package directory."""
    return Path(__file__).parent


def prepare_build_context(
    spec: RepoSpec,
    context_dir: Path,
) -> None:
    """
    Prepare the Docker build context directory.

    Copies:
    - generated_repo/ -> context_dir/generated_repo/
    - golden_tests/   -> context_dir/golden_tests/
    - Dockerfile       -> context_dir/Dockerfile
    - entrypoint.sh    -> context_dir/entrypoint.sh

    Args:
        spec: The RepoSpec for this repo.
        context_dir: Temporary directory to use as Docker build context.
    """
    harness_dir = _get_harness_dir()

    # Copy generated repo
    generated_dest = context_dir / "generated_repo"
    if spec.generated_repo_path and spec.generated_repo_path.exists():
        shutil.copytree(
            spec.generated_repo_path,
            generated_dest,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "*.pyc", ".DS_Store",
                "node_modules", ".venv", "venv",
            ),
        )
    else:
        generated_dest.mkdir(parents=True, exist_ok=True)

    # Copy golden oracle tests
    golden_dest = context_dir / "golden_tests"
    if spec.golden_test_path and spec.golden_test_path.exists():
        if spec.golden_test_path.is_dir():
            shutil.copytree(
                spec.golden_test_path,
                golden_dest,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )
        else:
            golden_dest.mkdir(parents=True, exist_ok=True)
    else:
        golden_dest.mkdir(parents=True, exist_ok=True)

    # Copy Dockerfile
    dockerfile_src = harness_dir / "dockerfiles" / spec.dockerfile_name
    if dockerfile_src.exists():
        shutil.copy2(dockerfile_src, context_dir / "Dockerfile")
    else:
        raise FileNotFoundError(
            f"Dockerfile not found: {dockerfile_src}. "
            f"Expected {spec.dockerfile_name} in {harness_dir / 'dockerfiles'}"
        )

    # Copy entrypoint script
    entrypoint_src = harness_dir / "scripts" / "entrypoint.sh"
    if entrypoint_src.exists():
        shutil.copy2(entrypoint_src, context_dir / "entrypoint.sh")
    else:
        raise FileNotFoundError(f"entrypoint.sh not found: {entrypoint_src}")


def build_image(
    spec: RepoSpec,
    timeout: int = 600,
    no_cache: bool = False,
) -> Tuple[bool, str]:
    """
    Build a Docker image for a single repo.

    Args:
        spec: The RepoSpec for this repo.
        timeout: Build timeout in seconds.
        no_cache: If True, build with --no-cache.

    Returns:
        (success, image_tag_or_error_message)
    """
    image_tag = spec.image_tag

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            context_dir = Path(tmpdir)
            prepare_build_context(spec, context_dir)

            cmd = [
                "docker", "build",
                "-t", image_tag,
                "--memory", DOCKER_MEMORY_LIMIT,
            ]
            if no_cache:
                cmd.append("--no-cache")
            cmd.append(str(context_dir))

            logger.info(f"Building image {image_tag} for {spec.repo_name}...")
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                error_msg = result.stderr[-3000:] if result.stderr else "Unknown build error"
                logger.error(f"Build failed for {spec.repo_name}: {error_msg}")
                return False, f"Build failed (exit {result.returncode}): {error_msg}"

            logger.info(f"Image built successfully: {image_tag}")
            return True, image_tag

    except subprocess.TimeoutExpired:
        logger.error(f"Build timed out for {spec.repo_name} ({timeout}s)")
        return False, f"Build timed out ({timeout}s)"
    except FileNotFoundError as e:
        logger.error(f"File not found during build: {e}")
        return False, f"File not found: {e}"
    except Exception as e:
        logger.error(f"Unexpected error building {spec.repo_name}: {e}")
        return False, f"Unexpected error: {e}"


def remove_image(image_tag: str) -> None:
    """
    Remove a Docker image.

    Args:
        image_tag: The image tag to remove.
    """
    try:
        subprocess.run(
            ["docker", "rmi", "-f", image_tag],
            capture_output=True,
            text=True,
            timeout=30,
        )
        logger.debug(f"Removed image: {image_tag}")
    except Exception:
        pass  # Cleanup failure is not critical


def image_exists(image_tag: str) -> bool:
    """
    Check if a Docker image exists locally.

    Args:
        image_tag: The image tag to check.

    Returns:
        True if the image exists.
    """
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_tag],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False
