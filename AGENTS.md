# AGENTS.md — RepoGenesis Codebase Guide

RepoGenesis benchmarks LLMs' ability to generate web microservice repos from
README specs. It evaluates 106 repos (60 Python, 46 Java) across three metrics:
**Pass@1** (test pass rate), **AC** (API Coverage), and **DSR** (Deployment Success Rate).

Active development is in `eval_harness/` — a Docker-based evaluation harness
modeled after SWE-bench. Legacy scripts live at the root level.

## Repository Layout

```
eval_harness/               # Docker-based evaluation harness (active)
├── run_evaluation.py       #   CLI entry point + orchestrator
├── constants.py            #   Repo specs, timeouts, markers, paths
├── test_spec.py            #   RepoSpec dataclass
├── log_parsers.py          #   pytest / Maven Surefire output parsers
├── api_coverage.py         #   AC metric (static analysis)
├── grading.py              #   DSR + Pass@1 grading
├── reporting.py            #   Report generation + summary table
├── docker_build.py         #   Docker image building
├── docker_utils.py         #   Container lifecycle management
├── progress.py             #   Rich progress display (SWE-bench style)
├── requirements.txt        #   Harness deps (rich>=13.0.0)
├── dockerfiles/            #   Dockerfile.python, Dockerfile.java
├── scripts/entrypoint.sh   #   3-phase container entrypoint
└── tests/                  #   228 unit tests (10 modules)
evaluate_repos.py           # Legacy Python evaluator
evaluate_repos_java.py      # Legacy Java evaluator
test_evaluate_repos.py      # Legacy orchestrator tests (unittest)
config.json                 # LLM config (base_url, api_key, model)
requirements.txt            # Root-level deps (openai, etc.)
```

## Build / Install

```bash
pip install -r requirements.txt              # Root orchestrator deps
pip install -r eval_harness/requirements.txt  # Harness deps (rich)
pip install pytest                            # For running tests
```

## Test Commands

The eval_harness tests use `unittest.TestCase` classes, run via **pytest**.
The `--import-mode=importlib` flag is required because the parent directory is
named `code`, which shadows Python's built-in `code` module.

```bash
# Run ALL eval_harness tests (228 tests)
python -m pytest eval_harness/tests/ -v --import-mode=importlib

# Run a single test file
python -m pytest eval_harness/tests/test_progress.py -v --import-mode=importlib

# Run a single test class
python -m pytest eval_harness/tests/test_run_evaluation.py::TestEvaluateSingleRepo -v --import-mode=importlib

# Run a single test method
python -m pytest eval_harness/tests/test_run_evaluation.py::TestEvaluateSingleRepo::test_skip_docker_returns_ac_only -v --import-mode=importlib

# Legacy orchestrator tests (root level, pure unittest)
python -m unittest test_evaluate_repos.py -v
```

## Code Style

### Formatting & Language
- Python 3.10+. No formatter enforced (no black/ruff config).
- PEP 8: 4-space indent, ~100 char line limit.
- Two blank lines before top-level class/function definitions.
- Section dividers: `# ====...====` banner comments between logical sections.

### Imports
Ordered: stdlib → third-party → local. Blank line between groups.
Absolute imports only. No wildcard imports.

```python
import logging
import subprocess
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional, Tuple

from rich.console import Console   # third-party

from eval_harness.constants import REPO_SPECS   # local
```

### Naming
| Entity    | Convention         | Example                                 |
|-----------|--------------------|-----------------------------------------|
| Modules   | `snake_case`       | `docker_build.py`, `log_parsers.py`     |
| Functions | `snake_case`       | `grade_repo`, `run_eval_container`      |
| Classes   | `PascalCase`       | `RepoSpec`, `EvalProgressDisplay`       |
| Constants | `UPPER_SNAKE_CASE` | `CONTAINER_TIMEOUT`, `DSR_START_MARKER` |
| Private   | `_leading_under`   | `_NoOpDisplay`, `_format_result_summary`|

### Type Hints
Required on all function signatures. Use `typing` module generics
(`Dict`, `List`, `Optional`, `Tuple`, `Callable`). Use `pathlib.Path`
for filesystem paths, not raw strings.

```python
def build_image(spec: RepoSpec, no_cache: bool = False) -> Tuple[bool, str]:
    ...
```

### Docstrings
Google-style with `Args:` and `Returns:` sections. Module-level docstrings
on every file.

```python
def grade_dsr(logs: str) -> Dict[str, Any]:
    """
    Grade DSR (Deployment Success Rate) from container logs.

    Args:
        logs: Full container log output.

    Returns:
        Dict with 'success' (bool) and 'message' (str) keys.
    """
```

### Error Handling
- Specific exceptions first (`subprocess.TimeoutExpired`, `CalledProcessError`,
  `FileNotFoundError`), broad `except Exception as e` only where resilience is
  needed — always log the error.
- Functions that can partially fail return `Tuple[bool, str]` — `(success, message)`.
- Silent `except: pass` only in cleanup/teardown paths.

### Subprocess
Always: `subprocess.run(cmd, timeout=..., capture_output=True, text=True)`.
Prefer `check=True` with `CalledProcessError` handling over checking returncode.

### Tests
- All tests use `unittest.TestCase`. Run via pytest.
- Mock Docker/subprocess calls with `unittest.mock.patch` at the
  `eval_harness.<module>.<function>` level.
- Use `tempfile.TemporaryDirectory()` for filesystem tests.
- Patch `create_progress_display` with `_noop_display` in integration tests
  to avoid rich `Live` display interfering with test output.
- Optional imports: wrap in `try/except ImportError` with a fallback
  (see `progress.py` for the `RICH_AVAILABLE` pattern).

## Cursor Rules (.cursorrules)

> You are a professional software requirements engineering expert. If you are
> writing code, follow **Test-Driven Development (TDD)** best practices. If
> writing requirements, do not include specific function names, but API ports
> and interface names of the microservices should be explicit.

## Development Checklist

1. Follow TDD — write or update tests before implementing functionality.
2. After any change, run: `python -m pytest eval_harness/tests/ -v --import-mode=importlib`
3. Keep `eval_harness/` self-contained with minimal deps (currently only `rich`).
4. Never hardcode API keys — read from `config.json` or environment variables.
5. Mirror existing module structure when adding new files (docstring, imports,
   logger, typed functions, tests in `eval_harness/tests/test_<module>.py`).
