"""
RepoGenesis Evaluation Harness - Constants and Repository Specifications

Defines the 30 Verified benchmark repositories (22 Python + 8 Java),
their ports, frameworks, timeouts, and evaluation configuration.
"""

from pathlib import Path
from typing import Dict, Any


# =============================================================================
# Repo Specifications for all 30 Verified Repos
# =============================================================================

REPO_SPECS: Dict[str, Dict[str, Any]] = {
    # ---- Python repos (22) ----
    "Blog": {
        "lang": "python",
        "port": 8000,
        "framework": "fastapi",
    },
    "Chatroom": {
        "lang": "python",
        "port": 8083,
        "framework": "any",
    },
    "Customization": {
        "lang": "python",
        "port": 8082,
        "framework": "fastapi",
    },
    "Data_Rank_Searcher": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "django-rest-framework-crud": {
        "lang": "python",
        "port": 8000,
        "framework": "django",
    },
    "eve": {
        "lang": "python",
        "port": 5001,
        "framework": "eve",
    },
    "File_Relay": {
        "lang": "python",
        "port": 8085,
        "framework": "any",
    },
    "flask": {
        "lang": "python",
        "port": 5000,
        "framework": "flask",
    },
    "GameBackend": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "mail_service": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "Multilingual": {
        "lang": "python",
        "port": 5000,
        "framework": "flask",
    },
    "rock-paper-scissors-flask": {
        "lang": "python",
        "port": 5000,
        "framework": "flask",
    },
    "simple-rbac-service": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "SimpleFastPyAPI": {
        "lang": "python",
        "port": 8000,
        "framework": "fastapi",
    },
    "StructuredDataConvertor": {
        "lang": "python",
        "port": 8000,
        "framework": "any",
    },
    "synapse": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "TaskManagement": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "Tic-Tac-Toe": {
        "lang": "python",
        "port": 8082,
        "framework": "any",
    },
    "Timer4Tasker": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "UserManagement": {
        "lang": "python",
        "port": 8081,
        "framework": "any",
    },
    "UserManagement_2": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    "WebPan": {
        "lang": "python",
        "port": 8080,
        "framework": "any",
    },
    # ---- Java repos (8) ----
    "javalin-online-judge": {
        "lang": "java",
        "port": 7000,
        "framework": "javalin",
    },
    "javalin-task-manager": {
        "lang": "java",
        "port": 7000,
        "framework": "javalin",
    },
    "javalin-user-auth-platform": {
        "lang": "java",
        "port": 7070,
        "framework": "javalin",
    },
    "micronaut-ci-status": {
        "lang": "java",
        "port": 8080,
        "framework": "micronaut",
    },
    "quarkus-blog-cms": {
        "lang": "java",
        "port": 8080,
        "framework": "quarkus",
    },
    "spark-dashboard-backend": {
        "lang": "java",
        "port": 4567,
        "framework": "spark",
    },
    "spring-boot-course-scheduling": {
        "lang": "java",
        "port": 8080,
        "framework": "springboot",
    },
    "springboot-chat-gateway": {
        "lang": "java",
        "port": 8080,
        "framework": "springboot",
    },
}


# =============================================================================
# Timeout Configuration (in seconds)
# =============================================================================

PYTHON_STARTUP_TIMEOUT = 15
JAVA_STARTUP_TIMEOUT = 20

PYTHON_TEST_TIMEOUT = 300   # 5 min
JAVA_TEST_TIMEOUT = 600     # 10 min

PYTHON_BUILD_TIMEOUT = 120  # pip install
JAVA_BUILD_TIMEOUT = 300    # mvn install

CONTAINER_TIMEOUT = 900     # overall container timeout (15 min)


# =============================================================================
# Docker Image Configuration
# =============================================================================

DOCKER_IMAGE_PREFIX = "repogenesis-eval"
DOCKER_WORKDIR = "/repo"
DOCKER_RESULTS_DIR = "/results"
DOCKER_MEMORY_LIMIT = "2g"

BASE_IMAGE_PYTHON = "python:3.10-slim"
BASE_IMAGE_JAVA = "maven:3.9-eclipse-temurin-17"


# =============================================================================
# Log Markers (SWE-bench style delimiters for structured log parsing)
# =============================================================================

DSR_START_MARKER = ">>>>> DSR_START"
DSR_END_MARKER = ">>>>> DSR_END"
DSR_RESULT_PREFIX = "DSR_RESULT="
DSR_MESSAGE_PREFIX = "DSR_MESSAGE="

TEST_START_MARKER = ">>>>> TEST_START"
TEST_END_MARKER = ">>>>> TEST_END"
TEST_EXIT_CODE_PREFIX = "TEST_EXIT_CODE="


# =============================================================================
# Default Paths (relative to project root)
# =============================================================================

DEFAULT_GOLDEN_TEST_DIR_PYTHON = Path("repo_readme_verified")
DEFAULT_GOLDEN_TEST_DIR_JAVA = Path("repo_readme_verified_java_with_t_p")

DEFAULT_README_DIR_PYTHON = Path("repo_readme_verified_python_no_t")
DEFAULT_README_DIR_JAVA = Path("repo_readme_verified_java_no_t_with_p")

DEFAULT_OUTPUT_DIR = Path("eval_results")


# =============================================================================
# Repo Counts (for validation)
# =============================================================================

TOTAL_PYTHON_REPOS = 22
TOTAL_JAVA_REPOS = 8
TOTAL_VERIFIED_REPOS = TOTAL_PYTHON_REPOS + TOTAL_JAVA_REPOS  # 30


# =============================================================================
# Service Health Check Paths
# =============================================================================

HEALTH_CHECK_PATHS = [
    "/",
    "/health",
    "/api/health",
    "/api/v1/health",
    "/actuator/health",
]


# =============================================================================
# Success Patterns for DSR (process exited but printed success message)
# =============================================================================

PYTHON_SUCCESS_PATTERNS = [
    "Running on",
    "Started",
    "Uvicorn running",
    "Application startup complete",
    "Listening on",
    "Accepting connections",
    "Serving Flask app",
]

JAVA_SUCCESS_PATTERNS = [
    "Started",
    "Javalin started",
    "Server started",
    "Application started",
    "Listening on",
    "Tomcat started",
    "Micronaut",
    "Quarkus",
    "Spark has ignited",
]

# "Address already in use" means the app is deployable, just port-conflicted
PORT_CONFLICT_PATTERNS = [
    "Address already in use",
    "Port already in use",
    "EADDRINUSE",
]


# =============================================================================
# File Extensions for API Coverage static analysis
# =============================================================================

SOURCE_EXTENSIONS = {".py", ".java", ".js", ".ts", ".kt"}

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", "venv", ".venv",
    "target", "build", ".pytest_cache", "dist", "egg-info",
    "test", "tests", ".idea", ".vscode",
}


def get_repo_lang(repo_name: str) -> str:
    """Get the language of a repo by name."""
    spec = REPO_SPECS.get(repo_name)
    if spec is None:
        raise ValueError(f"Unknown repo: {repo_name}")
    return spec["lang"]


def get_repo_port(repo_name: str) -> int:
    """Get the expected service port of a repo by name."""
    spec = REPO_SPECS.get(repo_name)
    if spec is None:
        raise ValueError(f"Unknown repo: {repo_name}")
    return spec["port"]


def get_python_repos() -> Dict[str, Dict[str, Any]]:
    """Return only the Python repo specs."""
    return {k: v for k, v in REPO_SPECS.items() if v["lang"] == "python"}


def get_java_repos() -> Dict[str, Dict[str, Any]]:
    """Return only the Java repo specs."""
    return {k: v for k, v in REPO_SPECS.items() if v["lang"] == "java"}


def get_startup_timeout(lang: str) -> int:
    """Get startup timeout based on language."""
    if lang == "java":
        return JAVA_STARTUP_TIMEOUT
    return PYTHON_STARTUP_TIMEOUT


def get_test_timeout(lang: str) -> int:
    """Get test execution timeout based on language."""
    if lang == "java":
        return JAVA_TEST_TIMEOUT
    return PYTHON_TEST_TIMEOUT


def get_build_timeout(lang: str) -> int:
    """Get dependency install/build timeout based on language."""
    if lang == "java":
        return JAVA_BUILD_TIMEOUT
    return PYTHON_BUILD_TIMEOUT


def get_success_patterns(lang: str):
    """Get DSR success patterns based on language."""
    if lang == "java":
        return JAVA_SUCCESS_PATTERNS
    return PYTHON_SUCCESS_PATTERNS
