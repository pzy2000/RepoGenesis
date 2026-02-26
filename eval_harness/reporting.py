"""
RepoGenesis Evaluation Harness - Reporting

Aggregates per-repo results into a final evaluation report.
Outputs JSON with summary statistics and per-repo details.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def compute_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute summary statistics across all evaluated repos.

    Args:
        results: List of per-repo grading results.

    Returns:
        Summary dict with aggregated metrics.
    """
    total_repos = len(results)
    if total_repos == 0:
        return {
            "total_repos": 0,
            "evaluated": 0,
            "avg_pass_at_1": 0.0,
            "avg_api_coverage": 0.0,
            "deployment_success_rate": 0.0,
        }

    # Split by language
    python_results = [r for r in results if r.get("lang") == "python"]
    java_results = [r for r in results if r.get("lang") == "java"]

    # Pass@1: average score across repos with at least 1 test
    def avg_pass_at_1(res_list: List[Dict]) -> float:
        scores = [
            r["pass_at_1"]["score"]
            for r in res_list
            if r.get("pass_at_1", {}).get("total", 0) > 0
        ]
        return sum(scores) / len(scores) if scores else 0.0

    # DSR: fraction of repos where service started successfully
    def dsr(res_list: List[Dict]) -> float:
        if not res_list:
            return 0.0
        success_count = sum(
            1 for r in res_list if r.get("dsr", {}).get("success", False)
        )
        return success_count / len(res_list)

    # AC: average score across repos with at least 1 API endpoint
    def avg_ac(res_list: List[Dict]) -> float:
        scores = [
            r["api_coverage"]["score"]
            for r in res_list
            if "api_coverage" in r and r["api_coverage"].get("total_apis", 0) > 0
        ]
        return sum(scores) / len(scores) if scores else 0.0

    overall_pass_at_1 = avg_pass_at_1(results)
    overall_dsr = dsr(results)
    overall_ac = avg_ac(results)

    summary = {
        "total_repos": total_repos,
        "python_repos": len(python_results),
        "java_repos": len(java_results),
        "avg_pass_at_1": round(overall_pass_at_1, 4),
        "avg_api_coverage": round(overall_ac, 4),
        "deployment_success_rate": round(overall_dsr, 4),
        "pass_at_1_by_lang": {
            "python": round(avg_pass_at_1(python_results), 4),
            "java": round(avg_pass_at_1(java_results), 4),
        },
        "ac_by_lang": {
            "python": round(avg_ac(python_results), 4),
            "java": round(avg_ac(java_results), 4),
        },
        "dsr_by_lang": {
            "python": round(dsr(python_results), 4),
            "java": round(dsr(java_results), 4),
        },
    }

    return summary


def generate_report(
    results: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate the final evaluation report.

    Args:
        results: List of per-repo grading results.
        metadata: Optional metadata dict (e.g., model name, timestamp).

    Returns:
        Complete report dict ready for JSON serialization.
    """
    if metadata is None:
        metadata = {}

    metadata.setdefault("timestamp", datetime.now().isoformat())
    metadata.setdefault("harness_version", "1.0.0")

    summary = compute_summary(results)

    report = {
        "metadata": metadata,
        "summary": summary,
        "results": results,
    }

    return report


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the evaluation report to a JSON file.

    Args:
        report: The report dict.
        output_path: Path to write the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))


def save_intermediate_result(
    result: Dict[str, Any],
    output_dir: Path,
    repo_name: str,
    run_id: Optional[str] = None,
) -> None:
    """
    Save an intermediate result for crash recovery.

    Args:
        result: Single repo grading result.
        output_dir: Directory to save intermediate results.
        repo_name: Name of the repo.
        run_id: Optional run identifier (timestamp string) to isolate runs
                into separate subdirectories, preventing cross-run conflicts.
    """
    if run_id:
        intermediate_dir = output_dir / "intermediate" / run_id
    else:
        intermediate_dir = output_dir / "intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    filepath = intermediate_dir / f"{repo_name}.json"
    filepath.write_text(json.dumps(result, indent=2, ensure_ascii=False))


def load_intermediate_results(
    output_dir: Path,
    run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load all intermediate results from a previous (possibly crashed) run.

    Args:
        output_dir: Directory containing intermediate results.
        run_id: If provided, load from that specific run's subdirectory.
                If None, automatically pick the most recent run subdirectory.

    Returns:
        List of per-repo result dicts.
    """
    intermediate_dir = output_dir / "intermediate"
    if not intermediate_dir.exists():
        return []

    # Determine target directory
    if run_id:
        target_dir = intermediate_dir / run_id
    else:
        # Pick the most recent subdirectory (lexicographic descending = most recent timestamp first)
        subdirs = sorted(
            [d for d in intermediate_dir.iterdir() if d.is_dir()],
            reverse=True,
        )
        if not subdirs:
            return []
        target_dir = subdirs[0]

    results = []
    for filepath in sorted(target_dir.glob("*.json")):
        try:
            data = json.loads(filepath.read_text())
            results.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    return results


def format_summary_table(results: List[Dict[str, Any]]) -> str:
    """
    Format a human-readable summary table for terminal output.

    Args:
        results: List of per-repo grading results.

    Returns:
        Formatted string table.
    """
    lines = []
    lines.append("")
    lines.append("=" * 90)
    lines.append("  RepoGenesis Evaluation Results")
    lines.append("=" * 90)
    lines.append("")

    # Header
    header = f"{'Repo Name':<35} {'Lang':<8} {'DSR':<6} {'Pass@1':<10} {'AC':<10}"
    lines.append(header)
    lines.append("-" * 90)

    # Per-repo rows
    for r in sorted(results, key=lambda x: x.get("repo_name", "")):
        name = r.get("repo_name", "?")[:34]
        lang = r.get("lang", "?")
        dsr_ok = "PASS" if r.get("dsr", {}).get("success", False) else "FAIL"
        p1 = r.get("pass_at_1", {})
        p1_str = f"{p1.get('passed', 0)}/{p1.get('total', 0)} ({p1.get('score', 0.0):.2f})"
        ac = r.get("api_coverage", {})
        if ac:
            ac_str = f"{ac.get('implemented_apis', 0)}/{ac.get('total_apis', 0)} ({ac.get('score', 0.0):.2f})"
        else:
            ac_str = "N/A"
        lines.append(f"{name:<35} {lang:<8} {dsr_ok:<6} {p1_str:<10} {ac_str:<10}")

    # Summary
    summary = compute_summary(results)
    lines.append("-" * 90)
    lines.append(f"  Total repos:              {summary['total_repos']}")
    lines.append(f"  Avg Pass@1:               {summary['avg_pass_at_1']:.4f}")
    lines.append(f"  Deployment Success Rate:   {summary['deployment_success_rate']:.4f}")
    lines.append(f"  Avg API Coverage:          {summary['avg_api_coverage']:.4f}")

    # Per-language breakdown (only present when results are non-empty)
    if "pass_at_1_by_lang" in summary:
        lines.append("")
        lines.append(f"  Pass@1 (Python):  {summary['pass_at_1_by_lang']['python']:.4f}  "
                     f"| Pass@1 (Java):  {summary['pass_at_1_by_lang']['java']:.4f}")
        lines.append(f"  DSR (Python):     {summary['dsr_by_lang']['python']:.4f}  "
                     f"| DSR (Java):     {summary['dsr_by_lang']['java']:.4f}")
        lines.append(f"  AC (Python):      {summary['ac_by_lang']['python']:.4f}  "
                     f"| AC (Java):      {summary['ac_by_lang']['java']:.4f}")

    lines.append("=" * 90)
    lines.append("")

    return "\n".join(lines)
