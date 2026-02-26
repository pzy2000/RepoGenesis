"""
RepoGenesis Evaluation Harness - Repository Specification

Defines the RepoSpec dataclass representing a single benchmark instance.
Modeled after SWE-bench's TestSpec.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

from eval_harness.constants import (
    REPO_SPECS,
    DOCKER_IMAGE_PREFIX,
    DEFAULT_GOLDEN_TEST_DIR_PYTHON,
    DEFAULT_GOLDEN_TEST_DIR_JAVA,
    DEFAULT_README_DIR_PYTHON,
    DEFAULT_README_DIR_JAVA,
    get_startup_timeout,
    get_test_timeout,
    get_build_timeout,
)


@dataclass
class RepoSpec:
    """
    Specification for a single benchmark repository evaluation instance.

    Contains all paths and metadata needed to build a Docker image,
    run the evaluation container, and grade the results.
    """

    repo_name: str
    lang: str                              # "python" or "java"
    port: int                              # Service port
    framework: str                         # Framework hint (e.g., "fastapi", "javalin")
    generated_repo_path: Optional[Path] = None   # Agent's generated code
    golden_test_path: Optional[Path] = None      # Golden oracle test directory
    readme_path: Optional[Path] = None           # README spec for AC analysis

    @property
    def image_tag(self) -> str:
        """Docker image tag for this repo."""
        safe_name = self.repo_name.lower().replace(" ", "-")
        return f"{DOCKER_IMAGE_PREFIX}-{safe_name}:latest"

    @property
    def container_name(self) -> str:
        """Docker container name for this repo."""
        safe_name = self.repo_name.lower().replace(" ", "-")
        return f"{DOCKER_IMAGE_PREFIX}-{safe_name}"

    @property
    def dockerfile_name(self) -> str:
        """Which Dockerfile to use."""
        return f"Dockerfile.{self.lang}"

    @property
    def startup_timeout(self) -> int:
        """Service startup timeout in seconds."""
        return get_startup_timeout(self.lang)

    @property
    def test_timeout(self) -> int:
        """Test execution timeout in seconds."""
        return get_test_timeout(self.lang)

    @property
    def build_timeout(self) -> int:
        """Dependency install/build timeout in seconds."""
        return get_build_timeout(self.lang)

    @property
    def test_dir_in_container(self) -> str:
        """Where tests live inside the container."""
        if self.lang == "java":
            return "src/test"
        return "tests"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON output."""
        return {
            "repo_name": self.repo_name,
            "lang": self.lang,
            "port": self.port,
            "framework": self.framework,
            "generated_repo_path": str(self.generated_repo_path) if self.generated_repo_path else None,
            "golden_test_path": str(self.golden_test_path) if self.golden_test_path else None,
            "readme_path": str(self.readme_path) if self.readme_path else None,
        }

    def __repr__(self) -> str:
        return (
            f"RepoSpec(repo_name={self.repo_name!r}, lang={self.lang!r}, "
            f"port={self.port}, framework={self.framework!r})"
        )


def make_repo_spec(
    repo_name: str,
    predictions_dir: Path,
    golden_test_dir_python: Path = DEFAULT_GOLDEN_TEST_DIR_PYTHON,
    golden_test_dir_java: Path = DEFAULT_GOLDEN_TEST_DIR_JAVA,
    readme_dir_python: Path = DEFAULT_README_DIR_PYTHON,
    readme_dir_java: Path = DEFAULT_README_DIR_JAVA,
) -> Optional[RepoSpec]:
    """
    Create a RepoSpec for a single repo.

    Args:
        repo_name: Name of the repo (must exist in REPO_SPECS).
        predictions_dir: Directory containing generated repos.
        golden_test_dir_python: Directory with Python golden oracle tests.
        golden_test_dir_java: Directory with Java golden oracle tests.
        readme_dir_python: Directory with Python README specs.
        readme_dir_java: Directory with Java README specs.

    Returns:
        RepoSpec if the repo exists and has a generated counterpart, None otherwise.
    """
    if repo_name not in REPO_SPECS:
        return None

    spec_data = REPO_SPECS[repo_name]
    lang = spec_data["lang"]

    generated_repo_path = predictions_dir / repo_name
    if not generated_repo_path.exists():
        return None

    # Select golden test directory based on language
    if lang == "python":
        golden_test_path = golden_test_dir_python / repo_name / "tests"
        readme_path = readme_dir_python / repo_name / "README.md"
    else:
        golden_test_path = golden_test_dir_java / repo_name
        readme_path = readme_dir_java / repo_name / "README.md"

    return RepoSpec(
        repo_name=repo_name,
        lang=lang,
        port=spec_data["port"],
        framework=spec_data["framework"],
        generated_repo_path=generated_repo_path,
        golden_test_path=golden_test_path,
        readme_path=readme_path,
    )


def make_repo_specs(
    predictions_dir: Path,
    golden_test_dir_python: Path = DEFAULT_GOLDEN_TEST_DIR_PYTHON,
    golden_test_dir_java: Path = DEFAULT_GOLDEN_TEST_DIR_JAVA,
    readme_dir_python: Path = DEFAULT_README_DIR_PYTHON,
    readme_dir_java: Path = DEFAULT_README_DIR_JAVA,
    repo_names: Optional[List[str]] = None,
    lang_filter: Optional[str] = None,
) -> List[RepoSpec]:
    """
    Create RepoSpec objects for all repos found in predictions_dir.

    Args:
        predictions_dir: Directory containing generated repos.
        golden_test_dir_python: Directory with Python golden oracle tests.
        golden_test_dir_java: Directory with Java golden oracle tests.
        readme_dir_python: Directory with Python README specs.
        readme_dir_java: Directory with Java README specs.
        repo_names: If provided, only create specs for these repos.
        lang_filter: If provided, only create specs for this language ("python"/"java").

    Returns:
        List of RepoSpec objects for repos that have generated code.
    """
    if repo_names is None:
        # Discover from predictions_dir
        if predictions_dir.exists():
            repo_names = [
                d.name for d in sorted(predictions_dir.iterdir())
                if d.is_dir() and d.name in REPO_SPECS
            ]
        else:
            repo_names = []

    specs: List[RepoSpec] = []
    for name in repo_names:
        if lang_filter and REPO_SPECS.get(name, {}).get("lang") != lang_filter:
            continue
        spec = make_repo_spec(
            repo_name=name,
            predictions_dir=predictions_dir,
            golden_test_dir_python=golden_test_dir_python,
            golden_test_dir_java=golden_test_dir_java,
            readme_dir_python=readme_dir_python,
            readme_dir_java=readme_dir_java,
        )
        if spec is not None:
            specs.append(spec)

    return specs
