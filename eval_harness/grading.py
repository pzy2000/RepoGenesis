"""
RepoGenesis Evaluation Harness - Grading

Parses container logs to compute Pass@1 and DSR metrics for a single repo.
Uses SWE-bench-style marker-based log section extraction.
"""

from typing import Dict, Any

from eval_harness.constants import (
    DSR_START_MARKER,
    DSR_END_MARKER,
    DSR_RESULT_PREFIX,
    DSR_MESSAGE_PREFIX,
    TEST_START_MARKER,
    TEST_END_MARKER,
    TEST_EXIT_CODE_PREFIX,
)
from eval_harness.log_parsers import (
    extract_section,
    parse_pytest_output,
    parse_maven_surefire_output,
)
from eval_harness.test_spec import RepoSpec


def grade_dsr(logs: str) -> Dict[str, Any]:
    """
    Grade DSR (Deployment Success Rate) from container logs.

    Extracts the DSR section between markers and parses the result.

    Args:
        logs: Full container log output.

    Returns:
        Dict with:
        - success: bool
        - message: str describing the outcome
    """
    dsr_section = extract_section(logs, DSR_START_MARKER, DSR_END_MARKER)

    if not dsr_section:
        # No DSR markers found -- check if the service might have started
        # based on overall container behavior
        return {
            "success": False,
            "message": "No DSR markers found in container output",
        }

    # Parse DSR_RESULT=true/false
    success = False
    message = "Unknown"

    for line in dsr_section.splitlines():
        line = line.strip()
        if line.startswith(DSR_RESULT_PREFIX):
            value = line[len(DSR_RESULT_PREFIX):].strip().lower()
            success = value in ("true", "1", "yes")
        elif line.startswith(DSR_MESSAGE_PREFIX):
            message = line[len(DSR_MESSAGE_PREFIX):].strip()

    return {
        "success": success,
        "message": message,
    }


def grade_pass_at_1(logs: str, lang: str) -> Dict[str, Any]:
    """
    Grade Pass@1 (functional correctness) from container logs.

    Extracts the test section between markers and parses test results.

    Args:
        logs: Full container log output.
        lang: "python" or "java".

    Returns:
        Dict with:
        - passed: int
        - failed: int
        - errors: int
        - total: int
        - score: float (0.0 to 1.0)
    """
    test_section = extract_section(logs, TEST_START_MARKER, TEST_END_MARKER)

    # If no markers, try parsing the entire log (container might not have markers)
    if not test_section:
        test_section = logs

    if lang == "python":
        results = parse_pytest_output(test_section)
    elif lang == "java":
        results = parse_maven_surefire_output(test_section)
    else:
        results = {"passed": 0, "failed": 0, "errors": 0, "total": 0}

    total = results.get("total", 0)
    passed = results.get("passed", 0)

    score = passed / total if total > 0 else 0.0

    return {
        "passed": passed,
        "failed": results.get("failed", 0),
        "errors": results.get("errors", 0),
        "skipped": results.get("skipped", 0),
        "total": total,
        "score": round(score, 4),
    }


def grade_repo(
    spec: RepoSpec,
    logs: str,
    exit_code: int,
    ac_result: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Grade a single repo across all metrics.

    Args:
        spec: The RepoSpec for this repo.
        logs: Full container log output.
        exit_code: Container exit code.
        ac_result: Pre-computed API Coverage result (or None to skip).

    Returns:
        Complete grading result dict.
    """
    dsr = grade_dsr(logs)
    pass_at_1 = grade_pass_at_1(logs, spec.lang)

    result = {
        "repo_name": spec.repo_name,
        "lang": spec.lang,
        "port": spec.port,
        "framework": spec.framework,
        "exit_code": exit_code,
        "dsr": dsr,
        "pass_at_1": pass_at_1,
    }

    if ac_result is not None:
        result["api_coverage"] = {
            "total_apis": ac_result.get("total_apis", 0),
            "implemented_apis": ac_result.get("implemented_apis", 0),
            "score": ac_result.get("score", 0.0),
        }

    return result
