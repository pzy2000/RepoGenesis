"""
RepoGenesis Evaluation Harness - Rich Progress Display

Provides a SWE-bench-style dual progress bar for the evaluation pipeline:

    ⣽ Overall Progress ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3/30  10% 0:02:45

    ⣟ GameBackend              Building Docker image              0:00:38

The top row shows overall progress across all repos. The bottom row shows
the current repo being evaluated and its stage. Log messages scroll above
the progress display.

Gracefully degrades to no-op when `rich` is not installed.
"""

from __future__ import annotations

import logging
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Graceful degradation: if rich is not installed, everything still works
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.live import Live
    from rich.logging import RichHandler
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Column, Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

logger = logging.getLogger("eval_harness")


# =============================================================================
# Stage Constants
# =============================================================================

STAGE_INIT = "Initializing"
STAGE_AC = "Computing API Coverage"
STAGE_BUILD = "Building Docker image"
STAGE_CONTAINER = "Running evaluation container"
STAGE_GRADE = "Grading results"
STAGE_CLEANUP = "Cleaning up"
STAGE_SKIPPED = "Skipped (already complete)"
STAGE_DONE = "Done"
STAGE_FAILED = "Failed"
STAGE_SKIP_DOCKER = "AC only (Docker skipped)"


# =============================================================================
# Result formatting helpers
# =============================================================================

def _format_result_summary(result: Dict[str, Any]) -> str:
    """Format a one-line summary of a repo's evaluation result."""
    dsr = result.get("dsr", {})
    dsr_str = "[green]PASS[/]" if dsr.get("success") else "[red]FAIL[/]"

    p1 = result.get("pass_at_1", {})
    passed = p1.get("passed", 0)
    total = p1.get("total", 0)
    score = p1.get("score", 0.0)
    p1_str = f"{passed}/{total} ({score:.2f})"

    ac = result.get("api_coverage", {})
    if ac:
        ac_impl = ac.get("implemented_apis", 0)
        ac_total = ac.get("total_apis", 0)
        ac_score = ac.get("score", 0.0)
        ac_str = f"{ac_impl}/{ac_total} ({ac_score:.2f})"
    else:
        ac_str = "N/A"

    elapsed = result.get("elapsed_seconds", 0)
    return (
        f"DSR={dsr_str}  Pass@1={p1_str}  AC={ac_str}  "
        f"({elapsed:.1f}s)"
    )


# =============================================================================
# Main Progress Display Class
# =============================================================================

class EvalProgressDisplay:
    """
    SWE-bench-style dual progress bar for the evaluation harness.

    Usage::

        with EvalProgressDisplay(total=len(specs)) as display:
            for spec in specs:
                display.start_repo(spec.repo_name, spec.lang, spec.port)
                # ... do work, calling display.update_stage(...) at each phase ...
                display.complete_repo(result)

    When ``rich`` is not installed, all methods are silent no-ops.
    """

    def __init__(
        self,
        total: int,
        console: Optional[Any] = None,
        verbose: bool = False,
    ) -> None:
        """
        Args:
            total: Total number of repos to evaluate.
            console: Optional rich Console instance (created if None).
            verbose: If True, log at DEBUG level.
        """
        self.total = total
        self.verbose = verbose
        self._active = False
        self._current_task: Optional[Any] = None  # TaskID for instance_progress
        self._overall_task: Optional[Any] = None  # TaskID for overall_progress

        if not RICH_AVAILABLE:
            self._console = None
            self._live = None
            return

        # Console writes to stderr so stdout stays clean for piping
        if console is not None:
            self._console = console
        else:
            self._console = Console(stderr=True)

        # ---- Overall progress bar (top row) ----
        self._overall_progress = Progress(
            SpinnerColumn("dots2"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self._console,
            auto_refresh=False,
        )

        # ---- Per-repo status line (bottom row) ----
        self._instance_progress = Progress(
            SpinnerColumn("dots2"),
            TextColumn(
                "{task.description}",
                table_column=Column(min_width=28),
                style="bold",
            ),
            TextColumn(
                "{task.fields[status]}",
                table_column=Column(min_width=34),
                style="cyan",
            ),
            TimeElapsedColumn(),
            console=self._console,
            auto_refresh=False,
        )

        # ---- Single Live instance drives both ----
        self._live = Live(
            console=self._console,
            refresh_per_second=10,
            get_renderable=self._compose,
            redirect_stdout=True,
            redirect_stderr=True,
        )

    # ----- Composition -----

    def _compose(self) -> "Table":
        """Compose both progress displays into one renderable."""
        grid = Table.grid(expand=False)
        grid.add_row(self._overall_progress)
        grid.add_row(Text(""))  # blank separator line
        grid.add_row(self._instance_progress)
        return grid

    # ----- Context manager -----

    def __enter__(self) -> "EvalProgressDisplay":
        if not RICH_AVAILABLE or self._live is None:
            return self

        self._live.__enter__()
        self._active = True

        # Create overall task
        self._overall_task = self._overall_progress.add_task(
            "Overall Progress",
            total=self.total,
        )

        # Wire up RichHandler for the eval_harness logger so log messages
        # scroll above the progress bar instead of fighting with it
        self._setup_rich_logging()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._active or self._live is None:
            return

        # Remove any leftover instance task
        if self._current_task is not None:
            try:
                self._instance_progress.remove_task(self._current_task)
            except Exception:
                pass
            self._current_task = None

        self._restore_logging()
        self._active = False
        self._live.__exit__(exc_type, exc_val, exc_tb)

    # ----- Logging integration -----

    def _setup_rich_logging(self) -> None:
        """Replace the console StreamHandler with a RichHandler on the same Console."""
        harness_logger = logging.getLogger("eval_harness")
        self._saved_handlers: List[logging.Handler] = list(harness_logger.handlers)
        self._saved_level = harness_logger.level

        # Remove existing handlers
        harness_logger.handlers.clear()

        # Add RichHandler on the same console as the progress bar
        rich_handler = RichHandler(
            console=self._console,
            show_path=False,
            show_time=True,
            rich_tracebacks=True,
            markup=True,
            log_time_format="%H:%M:%S",
        )
        level = logging.DEBUG if self.verbose else logging.INFO
        rich_handler.setLevel(level)
        harness_logger.addHandler(rich_handler)
        harness_logger.setLevel(level)

    def _restore_logging(self) -> None:
        """Restore original logging handlers."""
        harness_logger = logging.getLogger("eval_harness")
        harness_logger.handlers.clear()
        for handler in self._saved_handlers:
            harness_logger.addHandler(handler)
        harness_logger.setLevel(self._saved_level)

    # ----- Public API -----

    def start_repo(
        self,
        repo_name: str,
        lang: str,
        port: int,
    ) -> None:
        """
        Signal that evaluation has started for a new repo.

        Args:
            repo_name: Name of the repo.
            lang: Language ("python" or "java").
            port: Service port number.
        """
        if not self._active:
            return

        # Remove the previous instance task (if any)
        if self._current_task is not None:
            try:
                self._instance_progress.remove_task(self._current_task)
            except Exception:
                pass

        # Add a new instance task (indeterminate — no bar, just spinner)
        self._current_task = self._instance_progress.add_task(
            repo_name,
            total=None,
            status=STAGE_INIT,
        )

    def update_stage(self, stage: str) -> None:
        """
        Update the current repo's evaluation stage.

        Args:
            stage: Human-readable stage description (use STAGE_* constants).
        """
        if not self._active or self._current_task is None:
            return
        self._instance_progress.update(self._current_task, status=stage)

    def complete_repo(self, result: Dict[str, Any]) -> None:
        """
        Signal that evaluation is complete for the current repo.

        Advances the overall progress bar and logs the result summary.

        Args:
            result: The per-repo grading result dict.
        """
        if not self._active:
            return

        repo_name = result.get("repo_name", "?")

        # Update instance to show final summary briefly
        if self._current_task is not None:
            self._instance_progress.update(
                self._current_task, status=f"[green]{STAGE_DONE}[/green]"
            )

        # Advance overall progress
        if self._overall_task is not None:
            self._overall_progress.advance(self._overall_task)

        # Log result summary above the progress bar
        summary = _format_result_summary(result)
        self._console.log(
            f"[bold]{repo_name}[/bold]: {summary}"
        )

        # Remove the instance task so it's clean for the next repo
        if self._current_task is not None:
            try:
                self._instance_progress.remove_task(self._current_task)
            except Exception:
                pass
            self._current_task = None

    def skip_repo(self, repo_name: str) -> None:
        """
        Signal that a repo is being skipped (already completed in resume).

        Advances the overall progress without showing a long-lived instance task.

        Args:
            repo_name: Name of the skipped repo.
        """
        if not self._active:
            return

        # Brief flash of the skip status
        task = self._instance_progress.add_task(
            repo_name,
            total=None,
            status=f"[dim]{STAGE_SKIPPED}[/dim]",
        )

        # Advance overall
        if self._overall_task is not None:
            self._overall_progress.advance(self._overall_task)

        # Remove immediately
        try:
            self._instance_progress.remove_task(task)
        except Exception:
            pass

    def fail_repo(self, repo_name: str, error: str) -> None:
        """
        Signal that evaluation failed for a repo with an unexpected error.

        Args:
            repo_name: Name of the repo.
            error: Error message.
        """
        if not self._active:
            return

        # Update instance to show failure
        if self._current_task is not None:
            self._instance_progress.update(
                self._current_task, status=f"[red]{STAGE_FAILED}[/red]"
            )

        # Advance overall
        if self._overall_task is not None:
            self._overall_progress.advance(self._overall_task)

        # Log error above the progress bar
        self._console.log(
            f"[bold red]{repo_name}[/bold red]: {error}"
        )

        # Remove instance task
        if self._current_task is not None:
            try:
                self._instance_progress.remove_task(self._current_task)
            except Exception:
                pass
            self._current_task = None


# =============================================================================
# No-op fallback when rich is not available
# =============================================================================

class _NoOpDisplay:
    """Silent no-op display used when rich is not installed."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __enter__(self) -> "_NoOpDisplay":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def start_repo(self, *args: Any, **kwargs: Any) -> None:
        pass

    def update_stage(self, *args: Any, **kwargs: Any) -> None:
        pass

    def complete_repo(self, *args: Any, **kwargs: Any) -> None:
        pass

    def skip_repo(self, *args: Any, **kwargs: Any) -> None:
        pass

    def fail_repo(self, *args: Any, **kwargs: Any) -> None:
        pass


def create_progress_display(
    total: int,
    console: Optional[Any] = None,
    verbose: bool = False,
) -> "EvalProgressDisplay | _NoOpDisplay":
    """
    Factory function that returns a progress display.

    Returns an :class:`EvalProgressDisplay` if ``rich`` is installed,
    otherwise a silent :class:`_NoOpDisplay`.

    Args:
        total: Total number of repos to evaluate.
        console: Optional rich Console instance.
        verbose: Enable verbose/debug output.

    Returns:
        A progress display context manager.
    """
    if RICH_AVAILABLE:
        return EvalProgressDisplay(total=total, console=console, verbose=verbose)
    return _NoOpDisplay()
