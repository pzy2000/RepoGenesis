"""
RepoGenesis Evaluation Harness - API Coverage (AC) Metric

Computes the fraction of API endpoints specified in a repo's README
that are actually implemented in the generated codebase.

Adapted from calculate_api_coverage.py (purely static analysis, no LLM).

Formula:
    AC = (1/|R|) * SUM_r ( |{api in A_r : implemented(api, C_r)}| / |A_r| )
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from eval_harness.constants import SOURCE_EXTENSIONS, EXCLUDED_DIRS


def extract_api_endpoints_from_readme(readme_path: Path) -> List[Dict[str, str]]:
    """
    Extract API endpoints from a README specification.

    Uses 4 regex patterns:
    1. Explicit endpoint lines: "GET /api/items - List items"
    2. Markdown table rows: "| GET | /api/items |"
    3. Endpoints inside fenced code blocks
    4. Feature list items (fallback if no explicit endpoints found)

    Args:
        readme_path: Path to the README.md file.

    Returns:
        List of endpoint dicts with 'method', 'path', 'description' keys.
    """
    if not readme_path.exists():
        return []

    content = readme_path.read_text(encoding="utf-8", errors="ignore")
    endpoints: List[Dict[str, str]] = []
    seen: Set[str] = set()

    # Pattern 1: Explicit endpoint lines
    # e.g., "GET /api/items - List all items"
    #        "POST /api/items: Create a new item"
    pattern1 = re.compile(
        r"(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s\-:]+)\s*[-:]?\s*(.+?)(?:\n|$)",
        re.IGNORECASE,
    )
    for match in pattern1.finditer(content):
        method = match.group(1).upper()
        path = match.group(2).strip().rstrip("`").rstrip("*")
        desc = match.group(3).strip()
        key = f"{method}:{path}"
        if key not in seen:
            seen.add(key)
            endpoints.append({"method": method, "path": path, "description": desc})

    # Pattern 2: Markdown table rows
    # e.g., "| GET | /api/items | List all items |"
    pattern2 = re.compile(
        r"\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*`?(/[^|`]+?)`?\s*\|",
        re.IGNORECASE,
    )
    for match in pattern2.finditer(content):
        method = match.group(1).upper()
        path = match.group(2).strip()
        key = f"{method}:{path}"
        if key not in seen:
            seen.add(key)
            endpoints.append({"method": method, "path": path, "description": ""})

    # Pattern 3: Endpoints inside code blocks
    code_block_pattern = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
    for block_match in code_block_pattern.finditer(content):
        block_content = block_match.group(1)
        for match in pattern1.finditer(block_content):
            method = match.group(1).upper()
            path = match.group(2).strip().rstrip("`").rstrip("*")
            desc = match.group(3).strip()
            key = f"{method}:{path}"
            if key not in seen:
                seen.add(key)
                endpoints.append({"method": method, "path": path, "description": desc})

    # Pattern 4: Feature list items (fallback only if no explicit endpoints)
    if not endpoints:
        feature_pattern = re.compile(
            r"[-*]\s+([A-Z][A-Za-z\s]+(?:Check|Login|Register|Create|Update|Delete|"
            r"Search|List|View|Get|Add|Remove|Edit|Manage|Upload|Download|Send|Receive))",
        )
        for match in feature_pattern.finditer(content):
            feature = match.group(1).strip()
            key = f"FEATURE:{feature}"
            if key not in seen:
                seen.add(key)
                endpoints.append({
                    "method": "FEATURE",
                    "path": feature,
                    "description": feature,
                })

    return endpoints


def _build_search_patterns(endpoint: Dict[str, str]) -> List[str]:
    """
    Build search patterns for a single endpoint across multiple frameworks.

    Args:
        endpoint: Dict with 'method', 'path', 'description'.

    Returns:
        List of regex pattern strings.
    """
    method = endpoint["method"]
    path = endpoint["path"]
    patterns: List[str] = []

    if method == "FEATURE":
        # Convert feature name to search patterns
        feature = path
        snake_case = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", feature).lower()
        snake_case = re.sub(r"\s+", "_", snake_case)
        concatenated = feature.replace(" ", "").lower()
        patterns.extend([
            re.escape(snake_case),
            re.escape(concatenated),
            re.escape(feature.lower()),
        ])
        return patterns

    method_lower = method.lower()

    # Flask / FastAPI decorator patterns
    patterns.extend([
        rf"@app\.{method_lower}\s*\(",
        rf"@router\.{method_lower}\s*\(",
        rf"@bp\.{method_lower}\s*\(",
        rf"@.*\.{method_lower}\s*\(",
    ])

    # Django methods list
    patterns.append(rf'methods\s*=\s*\[.*?"{method}"')

    # Express / Node patterns
    patterns.extend([
        rf"app\.{method_lower}\s*\(",
        rf"router\.{method_lower}\s*\(",
    ])

    # Spring Boot annotation patterns
    method_capitalized = method.capitalize()
    patterns.extend([
        rf"@{method_capitalized}Mapping",
        rf"@RequestMapping.*method\s*=\s*RequestMethod\.{method}",
    ])

    # Javalin patterns
    patterns.append(rf"\.{method_lower}\s*\(")

    # Spark Java
    patterns.append(rf"Spark\.{method_lower}\s*\(")

    # Micronaut
    patterns.append(rf"@{method_capitalized}\s*\(")

    # Quarkus / JAX-RS
    patterns.append(rf"@{method}\s*$")

    return patterns


def search_implementation(repo_path: Path, endpoint: Dict[str, str]) -> bool:
    """
    Check whether a single endpoint is implemented in the repo source code.

    Searches through source files (excluding test directories) for:
    1. Framework-specific decorator/annotation patterns
    2. The actual path string

    Both must appear in the same file for non-FEATURE endpoints.

    Args:
        repo_path: Path to the generated repo.
        endpoint: Dict with 'method', 'path', 'description'.

    Returns:
        True if the endpoint appears to be implemented.
    """
    method = endpoint["method"]
    path = endpoint["path"]
    patterns = _build_search_patterns(endpoint)
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    # For path matching, extract significant path parts
    path_parts = [
        part for part in path.strip("/").split("/")
        if len(part) > 3 and not part.startswith("{") and not part.startswith("<")
    ]

    for root, dirs, files in os.walk(repo_path):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for filename in files:
            file_path = Path(root) / filename
            if file_path.suffix not in SOURCE_EXTENSIONS:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue

            # Check if any decorator/annotation pattern matches
            pattern_found = False
            for compiled in compiled_patterns:
                if compiled.search(content):
                    pattern_found = True
                    break

            if not pattern_found:
                continue

            # For FEATURE endpoints, pattern match alone is sufficient
            if method == "FEATURE":
                return True

            # For regular endpoints, also require path evidence in the same file
            # Check exact path
            if path in content:
                return True

            # Check significant path parts
            for part in path_parts:
                if part in content:
                    return True

    return False


def calculate_repo_api_coverage(
    repo_path: Path,
    readme_path: Path,
) -> Dict:
    """
    Calculate API Coverage for a single generated repo.

    Args:
        repo_path: Path to the generated repo source code.
        readme_path: Path to the README specification.

    Returns:
        Dict with coverage results:
        {
            "total_apis": int,
            "implemented_apis": int,
            "score": float,  # 0.0 to 1.0
            "endpoints": {
                "implemented": [...],
                "not_implemented": [...]
            }
        }
    """
    endpoints = extract_api_endpoints_from_readme(readme_path)

    if not endpoints:
        return {
            "total_apis": 0,
            "implemented_apis": 0,
            "score": 0.0,
            "endpoints": [],
            "note": "No API endpoints found in README",
        }

    implemented = []
    not_implemented = []

    for endpoint in endpoints:
        if search_implementation(repo_path, endpoint):
            implemented.append(endpoint)
        else:
            not_implemented.append(endpoint)

    total = len(endpoints)
    impl_count = len(implemented)
    score = impl_count / total if total > 0 else 0.0

    return {
        "total_apis": total,
        "implemented_apis": impl_count,
        "score": round(score, 4),
        "endpoints": {
            "implemented": implemented,
            "not_implemented": not_implemented,
        },
    }
