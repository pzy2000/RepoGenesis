"""
Tests for eval_harness.test_spec module.
"""

import tempfile
import unittest
from pathlib import Path

from eval_harness.test_spec import RepoSpec, make_repo_spec, make_repo_specs
from eval_harness.constants import (
    DOCKER_IMAGE_PREFIX,
    PYTHON_STARTUP_TIMEOUT,
    JAVA_STARTUP_TIMEOUT,
    PYTHON_TEST_TIMEOUT,
    JAVA_TEST_TIMEOUT,
    PYTHON_BUILD_TIMEOUT,
    JAVA_BUILD_TIMEOUT,
)


class TestRepoSpec(unittest.TestCase):
    """Test the RepoSpec dataclass."""

    def setUp(self):
        self.python_spec = RepoSpec(
            repo_name="Blog",
            lang="python",
            port=8000,
            framework="fastapi",
            generated_repo_path=Path("/tmp/generated/Blog"),
            golden_test_path=Path("/tmp/tests/Blog/tests"),
            readme_path=Path("/tmp/readme/Blog/README.md"),
        )
        self.java_spec = RepoSpec(
            repo_name="javalin-online-judge",
            lang="java",
            port=7000,
            framework="javalin",
            generated_repo_path=Path("/tmp/generated/javalin-online-judge"),
            golden_test_path=Path("/tmp/tests/javalin-online-judge"),
            readme_path=Path("/tmp/readme/javalin-online-judge/README.md"),
        )

    def test_image_tag(self):
        """Image tag should use lowercase repo name with prefix."""
        self.assertEqual(
            self.python_spec.image_tag,
            f"{DOCKER_IMAGE_PREFIX}-blog:latest",
        )

    def test_image_tag_java(self):
        self.assertEqual(
            self.java_spec.image_tag,
            f"{DOCKER_IMAGE_PREFIX}-javalin-online-judge:latest",
        )

    def test_container_name(self):
        self.assertEqual(
            self.python_spec.container_name,
            f"{DOCKER_IMAGE_PREFIX}-blog",
        )

    def test_dockerfile_name_python(self):
        self.assertEqual(self.python_spec.dockerfile_name, "Dockerfile.python")

    def test_dockerfile_name_java(self):
        self.assertEqual(self.java_spec.dockerfile_name, "Dockerfile.java")

    def test_startup_timeout_python(self):
        self.assertEqual(self.python_spec.startup_timeout, PYTHON_STARTUP_TIMEOUT)

    def test_startup_timeout_java(self):
        self.assertEqual(self.java_spec.startup_timeout, JAVA_STARTUP_TIMEOUT)

    def test_test_timeout_python(self):
        self.assertEqual(self.python_spec.test_timeout, PYTHON_TEST_TIMEOUT)

    def test_test_timeout_java(self):
        self.assertEqual(self.java_spec.test_timeout, JAVA_TEST_TIMEOUT)

    def test_build_timeout_python(self):
        self.assertEqual(self.python_spec.build_timeout, PYTHON_BUILD_TIMEOUT)

    def test_build_timeout_java(self):
        self.assertEqual(self.java_spec.build_timeout, JAVA_BUILD_TIMEOUT)

    def test_test_dir_in_container_python(self):
        self.assertEqual(self.python_spec.test_dir_in_container, "tests")

    def test_test_dir_in_container_java(self):
        self.assertEqual(self.java_spec.test_dir_in_container, "src/test")

    def test_to_dict(self):
        d = self.python_spec.to_dict()
        self.assertEqual(d["repo_name"], "Blog")
        self.assertEqual(d["lang"], "python")
        self.assertEqual(d["port"], 8000)
        self.assertEqual(d["framework"], "fastapi")
        self.assertIn("generated_repo_path", d)
        self.assertIn("golden_test_path", d)
        self.assertIn("readme_path", d)

    def test_to_dict_none_paths(self):
        spec = RepoSpec(repo_name="X", lang="python", port=8000, framework="any")
        d = spec.to_dict()
        self.assertIsNone(d["generated_repo_path"])
        self.assertIsNone(d["golden_test_path"])
        self.assertIsNone(d["readme_path"])

    def test_repr(self):
        r = repr(self.python_spec)
        self.assertIn("Blog", r)
        self.assertIn("python", r)
        self.assertIn("8000", r)

    def test_image_tag_spaces_replaced(self):
        """Spaces in repo names should be replaced with hyphens."""
        spec = RepoSpec(repo_name="My Repo", lang="python", port=8080, framework="any")
        self.assertEqual(spec.image_tag, f"{DOCKER_IMAGE_PREFIX}-my-repo:latest")


class TestMakeRepoSpec(unittest.TestCase):
    """Test the make_repo_spec factory function."""

    def test_returns_none_for_unknown_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = make_repo_spec("nonexistent-repo", Path(tmpdir))
            self.assertIsNone(result)

    def test_returns_none_if_generated_dir_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Blog is a known repo, but no Blog/ subdir exists
            result = make_repo_spec("Blog", Path(tmpdir))
            self.assertIsNone(result)

    def test_returns_spec_when_generated_dir_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions_dir = Path(tmpdir)
            (predictions_dir / "Blog").mkdir()
            result = make_repo_spec("Blog", predictions_dir)
            self.assertIsNotNone(result)
            self.assertEqual(result.repo_name, "Blog")
            self.assertEqual(result.lang, "python")
            self.assertEqual(result.port, 8000)

    def test_python_golden_test_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions_dir = Path(tmpdir)
            (predictions_dir / "Blog").mkdir()
            result = make_repo_spec("Blog", predictions_dir)
            # Should point to golden_test_dir_python / Blog / tests
            self.assertTrue(str(result.golden_test_path).endswith("Blog/tests"))

    def test_java_golden_test_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions_dir = Path(tmpdir)
            (predictions_dir / "javalin-online-judge").mkdir()
            result = make_repo_spec("javalin-online-judge", predictions_dir)
            # Should point to golden_test_dir_java / javalin-online-judge
            self.assertTrue(
                str(result.golden_test_path).endswith("javalin-online-judge")
            )


class TestMakeRepoSpecs(unittest.TestCase):
    """Test the make_repo_specs factory function."""

    def test_empty_predictions_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            specs = make_repo_specs(Path(tmpdir))
            self.assertEqual(specs, [])

    def test_discovers_known_repos(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions_dir = Path(tmpdir)
            (predictions_dir / "Blog").mkdir()
            (predictions_dir / "flask").mkdir()
            (predictions_dir / "unknown_repo").mkdir()  # Not in REPO_SPECS
            specs = make_repo_specs(predictions_dir)
            names = {s.repo_name for s in specs}
            self.assertIn("Blog", names)
            self.assertIn("flask", names)
            self.assertNotIn("unknown_repo", names)

    def test_lang_filter_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions_dir = Path(tmpdir)
            (predictions_dir / "Blog").mkdir()
            (predictions_dir / "javalin-online-judge").mkdir()
            specs = make_repo_specs(predictions_dir, lang_filter="python")
            for s in specs:
                self.assertEqual(s.lang, "python")
            names = {s.repo_name for s in specs}
            self.assertIn("Blog", names)
            self.assertNotIn("javalin-online-judge", names)

    def test_lang_filter_java(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions_dir = Path(tmpdir)
            (predictions_dir / "Blog").mkdir()
            (predictions_dir / "javalin-online-judge").mkdir()
            specs = make_repo_specs(predictions_dir, lang_filter="java")
            for s in specs:
                self.assertEqual(s.lang, "java")

    def test_explicit_repo_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions_dir = Path(tmpdir)
            (predictions_dir / "Blog").mkdir()
            (predictions_dir / "flask").mkdir()
            (predictions_dir / "GameBackend").mkdir()
            specs = make_repo_specs(
                predictions_dir, repo_names=["Blog", "flask"]
            )
            names = {s.repo_name for s in specs}
            self.assertEqual(names, {"Blog", "flask"})

    def test_nonexistent_predictions_dir(self):
        specs = make_repo_specs(Path("/tmp/nonexistent_dir_12345"))
        self.assertEqual(specs, [])


if __name__ == "__main__":
    unittest.main()
