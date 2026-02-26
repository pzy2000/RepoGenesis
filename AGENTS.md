# AGENTS.md — RepoGenesis Codebase Guide

RepoGenesis is a research benchmark that evaluates LLMs' ability to generate complete
web microservice repositories from natural language README specifications. It benchmarks
106 microservice repos (60 Python, 46 Java) across 11 web frameworks and multiple
agent systems (MetaGPT, DeepCode, Qwen-Agent, ms-agent, Cursor, GitHub Copilot).

---

## Repository Structure

```
.
├── gen_and_eval.py            # Main Python repo generation + evaluation entry point
├── gen_and_eval_Java.py       # Main Java repo generation + evaluation entry point
├── evaluate_repos.py          # Python evaluation pipeline (Pass@1)
├── evaluate_repos_java.py     # Java evaluation pipeline (Pass@1)
├── calculate_api_coverage.py  # API Coverage (AC) metric calculator
├── test_dsr_repos.py          # Deployment Success Rate (DSR) testing
├── test_evaluate_repos.py     # Unit tests for the orchestrator
├── requirements.txt           # Root orchestrator dependencies
├── config.json                # LLM config (base_url, api_key, model)
├── agent/                     # Agent framework adapter integrations
├── evaluation/                # LLM-based scoring workflow (scorers, workflow, run_eval)
├── exps/                      # Experiment scripts, DSR scripts, saved results
├── repo/                      # Seed repos (READMEs only, for generation)
├── repo_golden_oracle/        # Ground truth repos with full code + tests
├── repo_readme/               # README specs for all 106 benchmark repos
└── sft_training/              # SFT training pipeline
```

---

## Build / Install Commands

```bash
# Install root orchestrator dependencies
pip install -r requirements.txt

# Set up LLM credentials
cp config.json config.local.json  # edit base_url, api_key, model as needed
```

---

## Run Commands

```bash
# Generate a Python microservice repo with an agent, then evaluate it
python gen_and_eval.py \
  --agent metagpt \
  --repo_root repo \
  --repo_name <repo_name> \
  --llm_model gpt-4o \
  --llm_api_key $OPENAI_API_KEY

# Generate a Java microservice repo
python gen_and_eval_Java.py \
  --agent <agent> \
  --repo_root repo_java \
  --repo_name <repo_name> \
  --llm_model gpt-4o \
  --llm_api_key $OPENAI_API_KEY

# Evaluate a directory of generated Python repos (Pass@1)
python evaluate_repos.py \
  --answer_dir <generated_repo_dir> \
  --test_dir repo_golden_oracle \
  --output evaluation_results.json

# Evaluate a directory of generated Java repos (Pass@1)
python evaluate_repos_java.py \
  --answer_dir <generated_repo_dir> \
  --test_dir <golden_oracle_java_dir> \
  --output evaluation_results_java.json

# Calculate API Coverage
python calculate_api_coverage.py
python calculate_api_coverage_ide.py      # IDE agent configs
python calculate_api_coverage_agents.py   # Agentic framework configs

# Run Deployment Success Rate tests
python test_dsr_repos.py
python exps/test_dsr.py      # Java DSR
python exps/test_all_dsr.py  # Comprehensive DSR (Python + Java)
bash exps/test_dsr.sh

# Run LLM-based evaluation scoring workflow
python -m evaluation.run_eval --repo-root code/repo_readme --output results.json
```

---

## Test Commands

The orchestrator uses Python's built-in `unittest` module (not pytest).

```bash
# Run all unit tests
python -m unittest test_evaluate_repos.py

# Run a single test class
python -m unittest test_evaluate_repos.TestEvaluateRepos

# Run a single test method
python -m unittest test_evaluate_repos.TestEvaluateRepos.test_parse_pytest_output

# Run tests with verbose output
python -m unittest test_evaluate_repos.py -v
```

Child (generated) repos use pytest with conda isolation:

```bash
# Inside a golden oracle or generated Python repo
pytest tests/ -v
pytest tests/test_api.py -v                     # Single test file
pytest tests/test_api.py::test_create_item -v  # Single test function
pytest --cov=. --cov-report=term-missing tests/
```

Java repos use Maven Surefire:

```bash
# Inside a Java repo
./mvnw test
./mvnw test -Dtest=MyTestClass             # Single class
./mvnw test -Dtest=MyTestClass#myMethod    # Single method
```

---

## Code Style Guidelines

### Language & Version
- Python 3.10+ for all orchestrator scripts
- Java 11/17 for benchmark microservice repos (varies by repo)
- No TypeScript, no JavaScript at root level

### Formatting
- No enforced formatter is configured (no `.black`, `ruff`, `isort` config)
- Follow PEP 8: 4-space indentation, max ~100 chars per line
- Blank line between top-level functions/classes; two blank lines before class definitions

### Imports
- Order: standard library → third-party → local modules (no enforced tool)
- One import per line for clarity; avoid wildcard imports (`from x import *`)
- Use absolute imports for top-level modules; relative imports only within packages

```python
# Good
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import openai

from evaluation.scorers import OpenAILLMScorer
```

### Naming Conventions
| Entity        | Convention     | Example                              |
|---------------|----------------|--------------------------------------|
| Files/modules | `snake_case`   | `evaluate_repos.py`, `gen_and_eval.py` |
| Functions     | `snake_case`   | `find_files_recursive`, `kill_process_group` |
| Classes       | `PascalCase`   | `ScoreResult`, `EvaluationWorkflow`  |
| Variables     | `snake_case`   | `repo_name`, `test_results`          |
| Constants     | `UPPER_SNAKE_CASE` | `BASE_DIR`, `RESULTS_FILE`       |

### Type Hints
- Use type hints in all function signatures
- Use `typing` module types: `Optional`, `Tuple`, `Dict`, `List`, `Union`
- Prefer `Path` (from `pathlib`) over raw strings for filesystem paths

```python
def run_tests(repo_dir: Path, timeout: int = 120) -> Tuple[bool, str]:
    ...

def parse_pytest_output(output: str) -> Dict[str, int]:
    ...
```

### Error Handling
- Use specific exceptions where possible (`subprocess.CalledProcessError`,
  `subprocess.TimeoutExpired`, `FileNotFoundError`)
- Broad `except Exception as e` is acceptable in evaluation pipelines where
  resilience is required; always log the error
- Silent `except: pass` is acceptable only in cleanup/teardown (killing processes,
  releasing ports)
- Functions that can partially fail should return `(bool, str)` — `(success, message)`

```python
# Preferred in evaluation pipelines
try:
    result = subprocess.run(cmd, timeout=60, check=True, capture_output=True, text=True)
except subprocess.TimeoutExpired:
    return False, "Test timed out"
except subprocess.CalledProcessError as e:
    return False, f"Test failed: {e.stderr}"
except Exception as e:
    return False, f"Unexpected error: {e}"
```

### Subprocess Usage
- Always use `subprocess.run` with explicit `timeout`, `capture_output=True`, `text=True`
- Prefer `check=True` and catch `CalledProcessError` rather than checking returncode
- Use `subprocess.Popen` with process groups (`os.setpgrp`) when you need to kill child processes

### Path Handling
- Use `pathlib.Path` for all filesystem operations; avoid raw string concatenation
- Use `Path.resolve()` when passing paths to subprocesses

---

## Architecture & Key Patterns

### Agent Adapter Pattern
Each agent framework has a dedicated adapter in `agent/` that wraps the agent's API
and normalizes output into a standard repo contract:
- `start.sh` — starts the service, binds to `0.0.0.0` (not `localhost`)
- `requirements.txt` — Python deps (or `pom.xml` for Java)
- `tests/` — test directory

### Evaluation Pipeline (per repo)
1. Install dependencies (pip or maven)
2. Start service (`start.sh`)
3. Run tests (pytest or maven surefire)
4. Kill service and clean up ports
5. Collect and persist metrics to JSON

### Git Backup Pattern
Before generation, the repo state is committed. After generation, golden oracle tests
are restored from the backup commit to prevent agent contamination.

### Conda Isolation
Each Python repo's tests are run in a dedicated conda environment to prevent
dependency conflicts across the 60+ benchmark repos.

### Three Evaluation Metrics
- **Pass@1**: Functional correctness — fraction of tests passing
- **AC (API Coverage)**: Fraction of required API endpoints implemented
- **DSR (Deployment Success Rate)**: Whether the service starts and passes health checks

---

## Cursor Rules (.cursorrules)

> You are a professional software requirements engineering expert. If you are writing
> code, follow **Test-Driven Development (TDD)** best practices. If writing requirements,
> do not include specific function names, but API ports and interface names of the
> microservices should be explicit.

---

## Development Guidelines for Agents

- Follow TDD: write or update tests before implementing new functionality
- When adding a new script, mirror the structure of existing evaluation scripts
  (argument parsing via `argparse`, JSON output, logging via `print`)
- Keep orchestrator scripts self-contained — minimize new dependencies beyond
  what is already in `requirements.txt`
- When modifying evaluation logic, always run the unit tests first:
  `python -m unittest test_evaluate_repos.py -v`
- Do not hardcode API keys or credentials; read from `config.json` or environment variables
- Generated repos must satisfy the standard contract: `start.sh` + `requirements.txt`
  (or `pom.xml`) + `tests/` directory

## Note
请叫我主人
