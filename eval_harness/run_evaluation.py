"""
RepoGenesis Evaluation Harness - Main Orchestrator

CLI entry point that evaluates generated microservice repositories
across three metrics: DSR, Pass@1, and API Coverage.

Usage:
    python -m eval_harness.run_evaluation \
        --predictions_dir ./generated_repos \
        --output_dir ./eval_results

    # Evaluate a single repo
    python -m eval_harness.run_evaluation \
        --predictions_dir ./generated_repos \
        --repo_names Blog \
        --output_dir ./eval_results

    # Only Python repos, skip Docker (AC only)
    python -m eval_harness.run_evaluation \
        --predictions_dir ./generated_repos \
        --lang python \
        --skip_docker \
        --output_dir ./eval_results
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional

from eval_harness.constants import (
    REPO_SPECS,
    CONTAINER_TIMEOUT,
    DEFAULT_GOLDEN_TEST_DIR_PYTHON,
    DEFAULT_GOLDEN_TEST_DIR_JAVA,
    DEFAULT_README_DIR_PYTHON,
    DEFAULT_README_DIR_JAVA,
    DEFAULT_OUTPUT_DIR,
)
from eval_harness.test_spec import RepoSpec, make_repo_specs
from eval_harness.docker_build import build_image, remove_image, image_exists
from eval_harness.docker_utils import (
    run_eval_container,
    is_docker_available,
    cleanup_all_eval_containers,
    cleanup_all_eval_images,
)
from eval_harness.grading import grade_repo
from eval_harness.api_coverage import calculate_repo_api_coverage
from eval_harness.reporting import (
    generate_report,
    save_report,
    save_intermediate_result,
    load_intermediate_results,
    format_summary_table,
)
from eval_harness.progress import (
    create_progress_display,
    STAGE_AC,
    STAGE_BUILD,
    STAGE_CONTAINER,
    STAGE_GRADE,
    STAGE_CLEANUP,
    STAGE_SKIP_DOCKER,
)

logger = logging.getLogger("eval_harness")


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None) -> None:
    """
    Configure logging for the harness.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO.
        log_file: Optional path to also write logs to a file.
    """
    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    root_logger = logging.getLogger("eval_harness")
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # File handler
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), mode="a")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)


def evaluate_single_repo(
    spec: RepoSpec,
    timeout: int = CONTAINER_TIMEOUT,
    verbose: bool = False,
    skip_docker: bool = False,
    no_cache: bool = False,
    keep_image: bool = False,
    on_stage: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Evaluate a single generated repo end-to-end.

    Steps:
    1. Compute API Coverage (static analysis, no Docker needed)
    2. Build Docker image
    3. Run evaluation container
    4. Grade results from logs
    5. Cleanup

    Args:
        spec: RepoSpec for this repo.
        timeout: Container execution timeout in seconds.
        verbose: Stream container logs to stdout.
        skip_docker: If True, only compute API Coverage (no Docker).
        no_cache: Build Docker image with --no-cache.
        keep_image: If True, don't remove the image after evaluation.
        on_stage: Optional callback invoked with a STAGE_* constant at each phase.

    Returns:
        Complete grading result dict for this repo.
    """
    repo_name = spec.repo_name

    def _stage(s: str) -> None:
        if on_stage is not None:
            on_stage(s)

    logger.info("=" * 60)
    logger.info("Evaluating: %s (%s, port %d)", repo_name, spec.lang, spec.port)
    logger.info("=" * 60)

    start_time = time.time()

    # Step 1: API Coverage (always runs, doesn't need Docker)
    _stage(STAGE_AC)
    ac_result = None
    if spec.readme_path and spec.readme_path.exists():
        logger.info("[%s] Computing API Coverage...", repo_name)
        if spec.generated_repo_path and spec.generated_repo_path.exists():
            ac_result = calculate_repo_api_coverage(
                repo_path=spec.generated_repo_path,
                readme_path=spec.readme_path,
            )
            logger.info(
                "[%s] AC: %d/%d (%.2f)",
                repo_name,
                ac_result.get("implemented_apis", 0),
                ac_result.get("total_apis", 0),
                ac_result.get("score", 0.0),
            )
        else:
            logger.warning("[%s] No generated repo found, skipping AC", repo_name)
    else:
        logger.warning("[%s] No README found at %s, skipping AC", repo_name, spec.readme_path)

    if skip_docker:
        _stage(STAGE_SKIP_DOCKER)
        # Return AC-only result
        result = {
            "repo_name": repo_name,
            "lang": spec.lang,
            "port": spec.port,
            "framework": spec.framework,
            "exit_code": None,
            "dsr": {"success": False, "message": "Docker evaluation skipped"},
            "pass_at_1": {
                "passed": 0, "failed": 0, "errors": 0,
                "skipped": 0, "total": 0, "score": 0.0,
            },
        }
        if ac_result is not None:
            result["api_coverage"] = {
                "total_apis": ac_result.get("total_apis", 0),
                "implemented_apis": ac_result.get("implemented_apis", 0),
                "score": ac_result.get("score", 0.0),
            }
        result["elapsed_seconds"] = round(time.time() - start_time, 2)
        return result

    # Step 2: Build Docker image
    _stage(STAGE_BUILD)
    logger.info("[%s] Building Docker image...", repo_name)
    build_ok, build_msg = build_image(spec, no_cache=no_cache)

    if not build_ok:
        logger.error("[%s] Image build failed: %s", repo_name, build_msg)
        result = grade_repo(spec, logs="", exit_code=-3, ac_result=ac_result)
        result["build_error"] = build_msg
        result["elapsed_seconds"] = round(time.time() - start_time, 2)
        return result

    logger.info("[%s] Image built: %s", repo_name, build_msg)

    # Step 3: Run evaluation container
    _stage(STAGE_CONTAINER)
    logger.info("[%s] Running evaluation container (timeout: %ds)...", repo_name, timeout)
    exit_code, logs = run_eval_container(spec, timeout=timeout, verbose=verbose)

    logger.info("[%s] Container exited with code: %d", repo_name, exit_code)

    # Step 4: Grade results
    _stage(STAGE_GRADE)
    result = grade_repo(spec, logs=logs, exit_code=exit_code, ac_result=ac_result)
    result["elapsed_seconds"] = round(time.time() - start_time, 2)

    # Log summary
    dsr_ok = result.get("dsr", {}).get("success", False)
    p1 = result.get("pass_at_1", {})
    logger.info(
        "[%s] Results: DSR=%s, Pass@1=%d/%d (%.2f), time=%.1fs",
        repo_name,
        "PASS" if dsr_ok else "FAIL",
        p1.get("passed", 0),
        p1.get("total", 0),
        p1.get("score", 0.0),
        result["elapsed_seconds"],
    )

    # Step 5: Cleanup image (unless keep_image)
    _stage(STAGE_CLEANUP)
    if not keep_image:
        logger.debug("[%s] Removing Docker image...", repo_name)
        remove_image(spec.image_tag)

    return result


def run_evaluation(
    predictions_dir: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    golden_test_dir_python: Path = DEFAULT_GOLDEN_TEST_DIR_PYTHON,
    golden_test_dir_java: Path = DEFAULT_GOLDEN_TEST_DIR_JAVA,
    readme_dir_python: Path = DEFAULT_README_DIR_PYTHON,
    readme_dir_java: Path = DEFAULT_README_DIR_JAVA,
    repo_names: Optional[List[str]] = None,
    lang_filter: Optional[str] = None,
    timeout: int = CONTAINER_TIMEOUT,
    verbose: bool = False,
    skip_docker: bool = False,
    no_cache: bool = False,
    keep_images: bool = False,
    resume: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline across all repos.

    Evaluates repos serially (one container at a time). Saves intermediate
    results after each repo for crash recovery.

    Args:
        predictions_dir: Directory containing generated repos.
        output_dir: Directory to write evaluation results.
        golden_test_dir_python: Path to Python golden oracle tests.
        golden_test_dir_java: Path to Java golden oracle tests.
        readme_dir_python: Path to Python README specs.
        readme_dir_java: Path to Java README specs.
        repo_names: Specific repos to evaluate (None = all found).
        lang_filter: Only evaluate "python" or "java" repos.
        timeout: Per-container timeout in seconds.
        verbose: Stream container output.
        skip_docker: Only compute AC metric, skip Docker.
        no_cache: Build images with --no-cache.
        keep_images: Don't remove images after evaluation.
        resume: Resume from a previous interrupted run.
        metadata: Optional metadata to include in the report.

    Returns:
        Complete evaluation report dict.
    """
    overall_start = time.time()
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Validate Docker availability (unless skip_docker)
    if not skip_docker:
        if not is_docker_available():
            logger.error(
                "Docker is not available. Install Docker and start the daemon, "
                "or use --skip_docker for AC-only evaluation."
            )
            sys.exit(1)
        logger.info("Docker is available.")

    # Create RepoSpecs
    specs = make_repo_specs(
        predictions_dir=predictions_dir,
        golden_test_dir_python=golden_test_dir_python,
        golden_test_dir_java=golden_test_dir_java,
        readme_dir_python=readme_dir_python,
        readme_dir_java=readme_dir_java,
        repo_names=repo_names,
        lang_filter=lang_filter,
    )

    if not specs:
        logger.warning("No repos found to evaluate in %s", predictions_dir)
        report = generate_report([], metadata=metadata)
        save_report(report, output_dir / f"report_{run_id}.json")
        return report

    logger.info("Found %d repos to evaluate.", len(specs))
    for s in specs:
        logger.info("  - %s (%s, port %d)", s.repo_name, s.lang, s.port)

    # Resume support: load previous intermediate results
    completed_names: set = set()
    results: List[Dict[str, Any]] = []
    if resume:
        prev_results = load_intermediate_results(output_dir, run_id=None)  # auto-pick most recent run
        if prev_results:
            for r in prev_results:
                completed_names.add(r["repo_name"])
                results.append(r)
            logger.info(
                "Resumed %d previously completed repos: %s",
                len(prev_results),
                sorted(completed_names),
            )

    # Evaluate each repo serially with progress display
    with create_progress_display(total=len(specs), verbose=verbose) as display:
        for i, spec in enumerate(specs, 1):
            if spec.repo_name in completed_names:
                logger.info(
                    "[%d/%d] Skipping %s (already completed)",
                    i, len(specs), spec.repo_name,
                )
                display.skip_repo(spec.repo_name)
                continue

            logger.info(
                "[%d/%d] Starting evaluation: %s",
                i, len(specs), spec.repo_name,
            )

            display.start_repo(spec.repo_name, spec.lang, spec.port)

            try:
                result = evaluate_single_repo(
                    spec=spec,
                    timeout=timeout,
                    verbose=verbose,
                    skip_docker=skip_docker,
                    no_cache=no_cache,
                    keep_image=keep_images,
                    on_stage=display.update_stage,
                )
                display.complete_repo(result)
            except Exception as e:
                logger.error(
                    "[%s] Unexpected error during evaluation: %s", spec.repo_name, e
                )
                result = {
                    "repo_name": spec.repo_name,
                    "lang": spec.lang,
                    "port": spec.port,
                    "framework": spec.framework,
                    "exit_code": -99,
                    "dsr": {"success": False, "message": f"Evaluation error: {e}"},
                    "pass_at_1": {
                        "passed": 0, "failed": 0, "errors": 0,
                        "skipped": 0, "total": 0, "score": 0.0,
                    },
                    "error": str(e),
                }
                display.fail_repo(spec.repo_name, str(e))

            results.append(result)

            # Save intermediate result for crash recovery
            save_intermediate_result(result, output_dir, spec.repo_name, run_id=run_id)

    # Generate final report
    elapsed_total = round(time.time() - overall_start, 2)
    if metadata is None:
        metadata = {}
    metadata["total_elapsed_seconds"] = elapsed_total
    metadata["predictions_dir"] = str(predictions_dir)

    report = generate_report(results, metadata=metadata)
    report_path = output_dir / f"report_{run_id}.json"
    save_report(report, report_path)

    # Print summary table
    table = format_summary_table(results)
    print(table)

    logger.info("Evaluation complete. Total time: %.1fs", elapsed_total)
    logger.info("Report saved to: %s", report_path)

    return report


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: Arguments to parse (None = sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="RepoGenesis Evaluation Harness - Evaluate generated microservice repos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate all repos
  python -m eval_harness.run_evaluation --predictions_dir ./generated_repos

  # Evaluate specific repos
  python -m eval_harness.run_evaluation --predictions_dir ./generated_repos \\
      --repo_names Blog flask GameBackend

  # Only Python repos
  python -m eval_harness.run_evaluation --predictions_dir ./generated_repos --lang python

  # AC-only (no Docker)
  python -m eval_harness.run_evaluation --predictions_dir ./generated_repos --skip_docker

  # Resume interrupted run
  python -m eval_harness.run_evaluation --predictions_dir ./generated_repos --resume
""",
    )

    parser.add_argument(
        "--predictions_dir",
        type=Path,
        required=True,
        help="Directory containing generated repos (one subdirectory per repo).",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for results (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--golden_test_dir_python",
        type=Path,
        default=DEFAULT_GOLDEN_TEST_DIR_PYTHON,
        help="Python golden oracle test directory.",
    )
    parser.add_argument(
        "--golden_test_dir_java",
        type=Path,
        default=DEFAULT_GOLDEN_TEST_DIR_JAVA,
        help="Java golden oracle test directory.",
    )
    parser.add_argument(
        "--readme_dir_python",
        type=Path,
        default=DEFAULT_README_DIR_PYTHON,
        help="Python README spec directory.",
    )
    parser.add_argument(
        "--readme_dir_java",
        type=Path,
        default=DEFAULT_README_DIR_JAVA,
        help="Java README spec directory.",
    )
    parser.add_argument(
        "--repo_names",
        nargs="+",
        default=None,
        help="Specific repo names to evaluate (default: all found).",
    )
    parser.add_argument(
        "--lang",
        choices=["python", "java"],
        default=None,
        help="Only evaluate repos of this language.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=CONTAINER_TIMEOUT,
        help=f"Per-container timeout in seconds (default: {CONTAINER_TIMEOUT}).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (stream container logs, DEBUG logging).",
    )
    parser.add_argument(
        "--skip_docker",
        action="store_true",
        help="Skip Docker evaluation (only compute API Coverage).",
    )
    parser.add_argument(
        "--no_cache",
        action="store_true",
        help="Build Docker images with --no-cache.",
    )
    parser.add_argument(
        "--keep_images",
        action="store_true",
        help="Keep Docker images after evaluation (default: remove).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from a previous interrupted evaluation run.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove all eval containers/images and exit.",
    )
    parser.add_argument(
        "--log_file",
        type=Path,
        default=None,
        help="Path to write log file.",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default=None,
        help="Model name to record in report metadata.",
    )
    parser.add_argument(
        "--agent_name",
        type=str,
        default=None,
        help="Agent name to record in report metadata.",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    """
    Main entry point for the evaluation harness CLI.

    Args:
        argv: Command-line arguments (None = sys.argv[1:]).
    """
    args = parse_args(argv)

    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Handle --cleanup
    if args.cleanup:
        logger.info("Cleaning up all evaluation containers and images...")
        n_containers = cleanup_all_eval_containers()
        logger.info("Removed %d containers.", n_containers)
        n_images = cleanup_all_eval_images()
        logger.info("Removed %d images.", n_images)
        return

    # Build metadata
    metadata: Dict[str, Any] = {}
    if args.model_name:
        metadata["model_name"] = args.model_name
    if args.agent_name:
        metadata["agent_name"] = args.agent_name

    # Run evaluation
    run_evaluation(
        predictions_dir=args.predictions_dir,
        output_dir=args.output_dir,
        golden_test_dir_python=args.golden_test_dir_python,
        golden_test_dir_java=args.golden_test_dir_java,
        readme_dir_python=args.readme_dir_python,
        readme_dir_java=args.readme_dir_java,
        repo_names=args.repo_names,
        lang_filter=args.lang,
        timeout=args.timeout,
        verbose=args.verbose,
        skip_docker=args.skip_docker,
        no_cache=args.no_cache,
        keep_images=args.keep_images,
        resume=args.resume,
        metadata=metadata,
    )


if __name__ == "__main__":
    main()
