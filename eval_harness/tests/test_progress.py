"""
Tests for eval_harness.progress module.

Validates the rich progress display, no-op fallback, result formatting,
and stage constants.
"""

import logging
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

from eval_harness.progress import (
    EvalProgressDisplay,
    _NoOpDisplay,
    _format_result_summary,
    create_progress_display,
    RICH_AVAILABLE,
    STAGE_AC,
    STAGE_BUILD,
    STAGE_CLEANUP,
    STAGE_CONTAINER,
    STAGE_DONE,
    STAGE_FAILED,
    STAGE_GRADE,
    STAGE_INIT,
    STAGE_SKIP_DOCKER,
    STAGE_SKIPPED,
)


# =============================================================================
# Stage Constants
# =============================================================================

class TestStageConstants(unittest.TestCase):
    """Verify that all stage constants are non-empty strings."""

    def test_all_stage_constants_are_strings(self):
        stages = [
            STAGE_INIT, STAGE_AC, STAGE_BUILD, STAGE_CONTAINER,
            STAGE_GRADE, STAGE_CLEANUP, STAGE_SKIPPED, STAGE_DONE,
            STAGE_FAILED, STAGE_SKIP_DOCKER,
        ]
        for stage in stages:
            self.assertIsInstance(stage, str)
            self.assertTrue(len(stage) > 0, f"Stage constant is empty: {stage!r}")

    def test_stage_constants_are_unique(self):
        stages = [
            STAGE_INIT, STAGE_AC, STAGE_BUILD, STAGE_CONTAINER,
            STAGE_GRADE, STAGE_CLEANUP, STAGE_SKIPPED, STAGE_DONE,
            STAGE_FAILED, STAGE_SKIP_DOCKER,
        ]
        self.assertEqual(len(stages), len(set(stages)), "Stage constants must be unique")


# =============================================================================
# _format_result_summary
# =============================================================================

class TestFormatResultSummary(unittest.TestCase):
    """Test the one-line result summary formatter."""

    def test_full_result(self):
        result = {
            "repo_name": "Blog",
            "dsr": {"success": True, "message": "OK"},
            "pass_at_1": {"passed": 5, "failed": 1, "total": 6, "score": 0.83},
            "api_coverage": {"implemented_apis": 3, "total_apis": 4, "score": 0.75},
            "elapsed_seconds": 42.5,
        }
        summary = _format_result_summary(result)
        # Should contain DSR, Pass@1, AC
        self.assertIn("PASS", summary)
        self.assertIn("5/6", summary)
        self.assertIn("0.83", summary)
        self.assertIn("3/4", summary)
        self.assertIn("0.75", summary)
        self.assertIn("42.5", summary)

    def test_failed_dsr(self):
        result = {
            "repo_name": "Broken",
            "dsr": {"success": False, "message": "timeout"},
            "pass_at_1": {"passed": 0, "failed": 3, "total": 3, "score": 0.0},
            "elapsed_seconds": 120.0,
        }
        summary = _format_result_summary(result)
        self.assertIn("FAIL", summary)
        self.assertIn("0/3", summary)

    def test_no_api_coverage(self):
        result = {
            "repo_name": "NoAC",
            "dsr": {"success": True, "message": "OK"},
            "pass_at_1": {"passed": 2, "total": 2, "score": 1.0},
            "elapsed_seconds": 10.0,
        }
        summary = _format_result_summary(result)
        self.assertIn("N/A", summary)

    def test_empty_result(self):
        # Minimal result dict — should not crash
        result = {}
        summary = _format_result_summary(result)
        self.assertIsInstance(summary, str)


# =============================================================================
# _NoOpDisplay
# =============================================================================

class TestNoOpDisplay(unittest.TestCase):
    """Test the silent no-op fallback display."""

    def test_context_manager(self):
        display = _NoOpDisplay()
        with display as d:
            self.assertIs(d, display)

    def test_all_methods_are_noop(self):
        display = _NoOpDisplay()
        with display as d:
            # None of these should raise
            d.start_repo("Blog", "python", 8000)
            d.update_stage(STAGE_BUILD)
            d.complete_repo({"repo_name": "Blog"})
            d.skip_repo("Blog")
            d.fail_repo("Blog", "error")

    def test_constructor_accepts_kwargs(self):
        # Should not raise with arbitrary args
        display = _NoOpDisplay(total=10, console=None, verbose=True)
        self.assertIsInstance(display, _NoOpDisplay)


# =============================================================================
# create_progress_display factory
# =============================================================================

class TestCreateProgressDisplay(unittest.TestCase):
    """Test the factory function."""

    def test_returns_display_when_rich_available(self):
        if not RICH_AVAILABLE:
            self.skipTest("rich not installed")
        display = create_progress_display(total=5)
        self.assertIsInstance(display, EvalProgressDisplay)

    def test_factory_with_verbose(self):
        display = create_progress_display(total=3, verbose=True)
        # Should return something that implements the context manager protocol
        self.assertTrue(hasattr(display, "__enter__"))
        self.assertTrue(hasattr(display, "__exit__"))

    def test_factory_with_console(self):
        if not RICH_AVAILABLE:
            self.skipTest("rich not installed")
        from rich.console import Console
        console = Console(file=StringIO())
        display = create_progress_display(total=2, console=console)
        self.assertIsInstance(display, EvalProgressDisplay)


# =============================================================================
# EvalProgressDisplay (requires rich)
# =============================================================================

class TestEvalProgressDisplay(unittest.TestCase):
    """Test the rich progress display class."""

    def setUp(self):
        if not RICH_AVAILABLE:
            self.skipTest("rich not installed")
        from rich.console import Console
        self.console = Console(file=StringIO(), force_terminal=True, width=120)

    def test_context_manager_enter_exit(self):
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            self.assertIs(d, display)
            self.assertTrue(d._active)
        self.assertFalse(display._active)

    def test_start_repo(self):
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            d.start_repo("Blog", "python", 8000)
            self.assertIsNotNone(d._current_task)

    def test_update_stage(self):
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            d.start_repo("Blog", "python", 8000)
            # Should not raise
            d.update_stage(STAGE_BUILD)
            d.update_stage(STAGE_CONTAINER)

    def test_update_stage_without_start_is_noop(self):
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            # No start_repo called — should not raise
            d.update_stage(STAGE_BUILD)

    def test_complete_repo(self):
        display = EvalProgressDisplay(total=3, console=self.console)
        result = {
            "repo_name": "Blog",
            "dsr": {"success": True, "message": "OK"},
            "pass_at_1": {"passed": 3, "total": 3, "score": 1.0},
            "elapsed_seconds": 10.5,
        }
        with display as d:
            d.start_repo("Blog", "python", 8000)
            d.complete_repo(result)
            # After complete, the instance task should be removed
            self.assertIsNone(d._current_task)

    def test_skip_repo(self):
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            d.skip_repo("Blog")
            # No current task should be left
            self.assertIsNone(d._current_task)

    def test_fail_repo(self):
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            d.start_repo("Blog", "python", 8000)
            d.fail_repo("Blog", "Build failed")
            self.assertIsNone(d._current_task)

    def test_full_lifecycle(self):
        """Simulate evaluating 3 repos: one complete, one skip, one fail."""
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            # Repo 1: success
            d.start_repo("Blog", "python", 8000)
            d.update_stage(STAGE_AC)
            d.update_stage(STAGE_BUILD)
            d.update_stage(STAGE_CONTAINER)
            d.update_stage(STAGE_GRADE)
            d.update_stage(STAGE_CLEANUP)
            d.complete_repo({
                "repo_name": "Blog",
                "dsr": {"success": True, "message": "OK"},
                "pass_at_1": {"passed": 5, "total": 5, "score": 1.0},
                "elapsed_seconds": 30.0,
            })

            # Repo 2: skip
            d.skip_repo("flask")

            # Repo 3: fail
            d.start_repo("GameBackend", "java", 8080)
            d.update_stage(STAGE_AC)
            d.update_stage(STAGE_BUILD)
            d.fail_repo("GameBackend", "Build timeout")

    def test_multiple_start_repo_removes_previous(self):
        """Calling start_repo twice should remove the first task."""
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            d.start_repo("Blog", "python", 8000)
            first_task = d._current_task
            d.start_repo("flask", "python", 8001)
            second_task = d._current_task
            self.assertIsNotNone(second_task)
            # Tasks should be different
            self.assertNotEqual(first_task, second_task)

    def test_methods_before_enter_are_noop(self):
        """Calling methods before __enter__ should be safe no-ops."""
        display = EvalProgressDisplay(total=3, console=self.console)
        # Not inside context — _active is False
        display.start_repo("Blog", "python", 8000)
        display.update_stage(STAGE_BUILD)
        display.complete_repo({"repo_name": "Blog"})
        display.skip_repo("Blog")
        display.fail_repo("Blog", "error")
        # Should not raise

    def test_compose_returns_renderable(self):
        """The _compose method should return a valid renderable."""
        display = EvalProgressDisplay(total=3, console=self.console)
        with display as d:
            renderable = d._compose()
            # Should be a rich Table (grid)
            from rich.table import Table
            self.assertIsInstance(renderable, Table)


# =============================================================================
# Logging Integration
# =============================================================================

class TestLoggingIntegration(unittest.TestCase):
    """Test that RichHandler is swapped in/out correctly."""

    def setUp(self):
        if not RICH_AVAILABLE:
            self.skipTest("rich not installed")
        from rich.console import Console
        self.console = Console(file=StringIO(), force_terminal=True, width=120)

    def test_rich_handler_added_on_enter(self):
        from rich.logging import RichHandler
        harness_logger = logging.getLogger("eval_harness")
        original_handlers = list(harness_logger.handlers)

        display = EvalProgressDisplay(total=3, console=self.console)
        with display:
            # Should have a RichHandler now
            rich_handlers = [
                h for h in harness_logger.handlers
                if isinstance(h, RichHandler)
            ]
            self.assertTrue(len(rich_handlers) > 0, "RichHandler should be added")

        # After exit, original handlers should be restored
        self.assertEqual(harness_logger.handlers, original_handlers)

    def test_logging_restored_on_exit(self):
        harness_logger = logging.getLogger("eval_harness")
        # Set up a known handler
        test_handler = logging.StreamHandler(StringIO())
        harness_logger.handlers.clear()
        harness_logger.addHandler(test_handler)
        original_level = harness_logger.level

        display = EvalProgressDisplay(total=2, console=self.console)
        with display:
            # Handlers changed inside
            pass

        # After exit, should be back to our test_handler
        self.assertIn(test_handler, harness_logger.handlers)
        self.assertEqual(harness_logger.level, original_level)


if __name__ == "__main__":
    unittest.main()
