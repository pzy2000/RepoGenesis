"""
RepoGenesis Evaluation Harness - Log Parsers

Parses pytest and Maven Surefire test output to extract pass/fail/error counts.
Adapted from evaluate_repos.py and evaluate_repos_java.py.
"""

import re
import json
from pathlib import Path
from typing import Dict, Optional, Tuple


def parse_pytest_output(log: str) -> Dict[str, int]:
    """
    Parse pytest output to extract test result counts.

    Handles multiple output formats:
    1. Standard pytest summary: "5 passed, 2 failed, 1 error in 3.45s"
    2. Short form: "5 passed"
    3. Edge cases: "no tests ran", timeouts

    Args:
        log: Full pytest stdout/stderr output.

    Returns:
        Dict with keys: passed, failed, errors, total.
    """
    passed = 0
    failed = 0
    errors = 0

    if not log or log.strip() == "TIMEOUT":
        return {"passed": 0, "failed": 0, "errors": 0, "total": 0}

    # Look for the pytest summary line (the last one wins)
    # Formats:
    #   "===== 5 passed in 1.23s ====="
    #   "===== 3 passed, 2 failed in 2.34s ====="
    #   "===== 1 passed, 1 failed, 1 error in 1.00s ====="
    for line in log.splitlines():
        line_stripped = line.strip()

        # Match pytest summary patterns
        m_passed = re.search(r"(\d+)\s+passed", line_stripped)
        m_failed = re.search(r"(\d+)\s+failed", line_stripped)
        m_errors = re.search(r"(\d+)\s+error", line_stripped)

        if m_passed:
            passed = int(m_passed.group(1))
        if m_failed:
            failed = int(m_failed.group(1))
        if m_errors:
            errors = int(m_errors.group(1))

    total = passed + failed + errors
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": total,
    }


def parse_pytest_json_report(report_path: Path) -> Optional[Dict[str, int]]:
    """
    Parse pytest-json-report output for precise test counts.

    Args:
        report_path: Path to the pytest JSON report file.

    Returns:
        Dict with keys: passed, failed, errors, total, or None if file not found.
    """
    if not report_path.exists():
        return None

    try:
        data = json.loads(report_path.read_text())
        summary = data.get("summary", {})
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        errors = summary.get("error", 0)
        total = summary.get("total", passed + failed + errors)
        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": total,
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def parse_maven_surefire_output(log: str) -> Dict[str, int]:
    """
    Parse Maven Surefire test output to extract test result counts.

    Handles two formats:
    1. Maven console: "Tests run: 10, Failures: 2, Errors: 1, Skipped: 0"
    2. May have multiple such lines (multi-module projects) -- sums them.

    Args:
        log: Full Maven stdout/stderr output.

    Returns:
        Dict with keys: passed, failed, errors, skipped, total.
    """
    total_run = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    if not log or log.strip() == "TIMEOUT":
        return {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total": 0}

    # Pattern: "Tests run: X, Failures: Y, Errors: Z, Skipped: W"
    pattern = re.compile(
        r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)"
    )

    for line in log.splitlines():
        match = pattern.search(line)
        if match:
            total_run += int(match.group(1))
            total_failures += int(match.group(2))
            total_errors += int(match.group(3))
            total_skipped += int(match.group(4))

    passed = total_run - total_failures - total_errors - total_skipped
    passed = max(passed, 0)  # guard against negative

    return {
        "passed": passed,
        "failed": total_failures,
        "errors": total_errors,
        "skipped": total_skipped,
        "total": total_run,
    }


def parse_maven_surefire_xml(surefire_dir: Path) -> Optional[Dict[str, int]]:
    """
    Parse Maven Surefire XML reports for precise test counts.

    Looks for TEST-*.xml files in target/surefire-reports/.

    Args:
        surefire_dir: Path to the surefire-reports directory.

    Returns:
        Dict with keys: passed, failed, errors, skipped, total, or None if dir not found.
    """
    if not surefire_dir.exists():
        return None

    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    xml_files = list(surefire_dir.glob("TEST-*.xml"))
    if not xml_files:
        return None

    for xml_file in xml_files:
        content = xml_file.read_text()

        # Parse <testsuite> attributes
        m = re.search(
            r'<testsuite[^>]*'
            r'\btests="(\d+)"[^>]*'
            r'\bfailures="(\d+)"[^>]*'
            r'\berrors="(\d+)"',
            content,
        )
        if m:
            total_tests += int(m.group(1))
            total_failures += int(m.group(2))
            total_errors += int(m.group(3))

        m_skipped = re.search(r'\bskipped="(\d+)"', content)
        if m_skipped:
            total_skipped += int(m_skipped.group(1))

    if total_tests == 0:
        return None

    passed = total_tests - total_failures - total_errors - total_skipped
    passed = max(passed, 0)

    return {
        "passed": passed,
        "failed": total_failures,
        "errors": total_errors,
        "skipped": total_skipped,
        "total": total_tests,
    }


def extract_section(log: str, start_marker: str, end_marker: str) -> str:
    """
    Extract a section of log between two markers (SWE-bench style).

    Args:
        log: Full log text.
        start_marker: Start delimiter (e.g., ">>>>> TEST_START").
        end_marker: End delimiter (e.g., ">>>>> TEST_END").

    Returns:
        The text between the markers, or empty string if not found.
    """
    start_idx = log.find(start_marker)
    end_idx = log.find(end_marker)

    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return ""

    return log[start_idx + len(start_marker):end_idx].strip()


def parse_test_output(log: str, lang: str) -> Dict[str, int]:
    """
    Parse test output from container logs, dispatching to the correct parser.

    Args:
        log: Full container log output.
        lang: "python" or "java".

    Returns:
        Dict with test result counts.
    """
    if lang == "python":
        return parse_pytest_output(log)
    elif lang == "java":
        return parse_maven_surefire_output(log)
    else:
        return {"passed": 0, "failed": 0, "errors": 0, "total": 0}
