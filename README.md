# RepoGenesis: Benchmarking End-to-End Microservice Generation from Readme to Repository

This repository contains the code and data for **RepoGenesis**, the first multilingual benchmark for repository-level end-to-end web microservice generation. RepoGenesis assesses LLMs' capability in generating complete web microservice repositories from natural language requirements.

## Table of Contents

- [Overview](#overview)
- [Benchmark Statistics](#benchmark-statistics)
- [Evaluation Metrics](#evaluation-metrics)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Evaluation Workflow](#evaluation-workflow)
  - [Step 1 — Generate Repositories](#step-1--generate-repositories)
  - [Step 2 — Docker-based Evaluation (Recommended)](#step-2--docker-based-evaluation-recommended)
  - [Step 3 — Legacy Script Evaluation](#step-3--legacy-script-evaluation)
  - [Step 4 — Aggregate and Reproduce Paper Results](#step-4--aggregate-and-reproduce-paper-results)
- [Repository Structure](#repository-structure)
- [Verified Benchmark Repos](#verified-benchmark-repos)
- [Development](#development)

---

## Overview

<div align="center">
  <img width="90%" src="RepoGenesis.png">
</div>

RepoGenesis is the first benchmark for evaluating repository-level microservice generation from natural language requirements. Unlike existing benchmarks that focus on function-level or class-level code generation, RepoGenesis challenges LLMs to generate repositories from scratch — given only a README, produce a fully working, deployable web microservice.

**Key Features:**

- **106 diverse web microservice repositories** (60 Python, 46 Java)
- **11 frameworks** including Django, FastAPI, Flask, Javalin, Spring Boot, Quarkus, Micronaut, and more
- **18 application domains** covering authentication, content management, gaming, file management, and more
- **Multi-dimensional metrics**: Pass@1 for functional correctness, API Coverage (AC) for implementation completeness, and Deployment Success Rate (DSR) for deployability
- **Docker-based isolated evaluation** via `eval_harness` — reproducible, hermetic, no conda required
- **Support for multiple agents**: MetaGPT, DeepCode, Qwen-Agent, MS-Agent, and commercial IDEs like Cursor and GitHub Copilot

---

## Benchmark Statistics

| Split | Python | Java | Total |
|---|---|---|---|
| Full benchmark | 60 | 46 | 106 |
| **Verified (with golden oracle tests)** | **22** | **8** | **30** |

The **Verified** subset is the primary evaluation target. Each repo has a README specification, a set of golden oracle tests (never seen by the agent), and a known service port.

---

## Evaluation Metrics

### Pass@1 — Functional Correctness

Measures the fraction of golden oracle test cases that pass on the first attempt:

```
Pass@1 = passed_tests / max(AST_count, total_pytest_tests)
```

Tests are run against the running service using black-box HTTP requests (Python: `pytest`; Java: Maven Surefire). The golden oracle tests are injected into the generated repo by the harness — the agent never sees them.

### API Coverage (AC) — Implementation Completeness

Measures what fraction of the API endpoints specified in the README are implemented in the generated code:

```
AC = implemented_endpoints / total_required_endpoints
```

Endpoints are extracted from the README using four regex patterns (explicit `METHOD /path` notation, markdown tables, code blocks, and feature-list fallback). Implementation is verified by static analysis — searching for the matching decorator and path string in the same source file.

### Deployment Success Rate (DSR) — Deployability

Measures whether the generated service can actually start up:

1. Install dependencies (`pip install -r requirements.txt` or `mvn install`)
2. Start the service (`bash start.sh` or `mvn spring-boot:run`)
3. Check that the process stays alive and/or prints a recognisable startup message (e.g., `"Uvicorn running"`, `"Tomcat started"`)

DSR is binary per repo (1 = deployed successfully, 0 = failed), then averaged across repos.

---

## Installation

### Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Orchestrator scripts |
| Docker | 20.10+ | Isolated evaluation (recommended) |
| Java JDK | 17+ | Java repo evaluation (legacy scripts) |
| Conda | Any | Isolated test envs (legacy scripts only) |
| Git | Any | Repository management |

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Configure API Keys

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"   # optional, for custom endpoints
```

### Install Agent Frameworks (Optional)

Only needed if you want to run generation with a specific agent framework:

```bash
# MetaGPT
git clone https://github.com/FoundationAgents/MetaGPT.git && cd MetaGPT && pip install -e .

# DeepCode
git clone https://github.com/HKUDS/DeepCode.git && cd DeepCode && pip install -e .

# Qwen-Agent
git clone https://github.com/QwenLM/Qwen-Agent.git && cd Qwen-Agent && pip install -e .

# MS-Agent
git clone https://github.com/modelscope/ms-agent.git && cd ms-agent && pip install -e .
```

---

## Quick Start

The fastest path to evaluate a set of generated repos end-to-end:

```bash
# 1. Generate repos (example: MetaGPT on Blog)
python gen_and_eval.py \
    --agent metagpt \
    --repo_root ./my_generated_repos \
    --repo_name Blog \
    --llm_model gpt-4o \
    --llm_api_key $OPENAI_API_KEY

# 2. Evaluate with Docker harness (all 3 metrics, 30 verified repos)
python -m eval_harness.run_evaluation \
    --predictions_dir ./my_generated_repos \
    --output_dir ./eval_results

# 3. View the results
cat eval_results/report.json
```

---

## Evaluation Workflow

The evaluation pipeline consists of four stages. Stages 1–2 are the recommended path. Stage 3 (legacy scripts) is kept for reproducing earlier paper results.

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  1. Generation  │────▶│  2. Docker Harness   │────▶│  4. Report / Paper  │
│  (agent + LLM)  │     │  (DSR + Pass@1 + AC) │     │  Results            │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
                                   │
                          ┌────────┴────────┐
                          │  3. Legacy eval │
                          │  (optional)     │
                          └─────────────────┘
```

---

### Step 1 — Generate Repositories

The agent receives only the README for each benchmark repo and must produce a complete repository (source code + `start.sh` + `requirements.txt` or `pom.xml`). Golden oracle tests are **never** shown to the agent.

#### Python Repos

```bash
# MetaGPT
python gen_and_eval.py \
    --agent metagpt \
    --repo_root ./generated \
    --repo_name <repo-name> \
    --llm_model gpt-4o \
    --llm_api_key $OPENAI_API_KEY

# DeepCode
python gen_and_eval.py \
    --agent deepcode \
    --repo_root ./generated \
    --repo_name <repo-name> \
    --deepcode_openai_key $OPENAI_API_KEY

# Qwen-Agent
python gen_and_eval.py \
    --agent qwen-agent \
    --repo_root ./generated \
    --repo_name <repo-name> \
    --llm_model qwen-max-latest \
    --llm_api_key $DASHSCOPE_API_KEY \
    --llm_base_url https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### Java Repos

```bash
python gen_and_eval_Java.py \
    --agent <agent-name> \
    --repo_root ./generated_java \
    --repo_name <repo-name> \
    --llm_model gpt-4o \
    --llm_api_key $OPENAI_API_KEY
```

After generation, your `--repo_root` will contain one subdirectory per repo, each with the generated source code. This directory is then passed to the evaluation harness as `--predictions_dir`.

---

### Step 2 — Docker-based Evaluation (Recommended)

The `eval_harness` package provides a hermetic, Docker-based evaluation pipeline that computes all three metrics (DSR, Pass@1, AC) in a single command. Each repo is evaluated in its own container — no conda environments, no port conflicts, no dependency pollution between repos.

#### How it Works

```
predictions_dir/
└── <repo_name>/          ← agent-generated source code
    ├── start.sh
    ├── requirements.txt  (Python) or pom.xml (Java)
    └── ...

          │
          ▼ eval_harness
          
1. AC computed via static analysis (no Docker needed)
2. Docker image built:
   ├── Base image: python:3.10-slim or maven:3.9-eclipse-temurin-17
   ├── Generated repo copied in
   └── Golden oracle tests injected (overwrite any agent-generated tests)
3. Container runs entrypoint.sh:
   ├── Phase 1 — DSR: install deps → start server → health check
   │   └── Emits >>>>> DSR_START ... >>>>> DSR_END markers
   └── Phase 2 — Pass@1: run pytest (Python) or mvn test (Java)
       └── Emits >>>>> TEST_START ... >>>>> TEST_END markers
4. Container logs parsed → DSR + Pass@1 graded
5. Image removed; intermediate result saved for crash recovery
6. Final JSON report + summary table printed
```

#### Run the Full Evaluation

```bash
python -m eval_harness.run_evaluation \
    --predictions_dir ./generated \
    --output_dir ./eval_results
```

#### Common Options

| Flag | Default | Description |
|---|---|---|
| `--predictions_dir` | *(required)* | Directory of generated repos (one subdir per repo) |
| `--output_dir` | `eval_results/` | Where to write `report.json` and intermediate results |
| `--repo_names Blog flask` | all found | Evaluate only specific repos |
| `--lang python` | all | Filter to `python` or `java` repos only |
| `--skip_docker` | off | Compute AC only, skip Docker (no DSR/Pass@1) |
| `--resume` | off | Resume from a previously interrupted run |
| `--keep_images` | off | Do not remove Docker images after evaluation |
| `--no_cache` | off | Build Docker images with `--no-cache` |
| `--verbose` / `-v` | off | Stream container logs + DEBUG logging |
| `--log_file eval.log` | none | Also write logs to a file |
| `--model_name gpt-4o` | none | Record model name in report metadata |
| `--agent_name metagpt` | none | Record agent name in report metadata |
| `--cleanup` | — | Remove all eval containers/images and exit |
| `--timeout` | 900 | Per-container timeout in seconds |

#### Example: Evaluate a Single Repo with Verbose Output

```bash
python -m eval_harness.run_evaluation \
    --predictions_dir ./generated \
    --repo_names Blog \
    --output_dir ./eval_results \
    --verbose \
    --model_name gpt-4o \
    --agent_name metagpt
```

#### Example: AC-only Evaluation (No Docker Required)

```bash
python -m eval_harness.run_evaluation \
    --predictions_dir ./generated \
    --skip_docker \
    --output_dir ./eval_results
```

#### Example: Resume an Interrupted Run

Intermediate results are saved after each repo under `eval_results/intermediate/<repo_name>.json`. If the run crashes, resume it:

```bash
python -m eval_harness.run_evaluation \
    --predictions_dir ./generated \
    --output_dir ./eval_results \
    --resume
```

#### Output Format

The final report is written to `eval_results/report.json`:

```jsonc
{
  "metadata": {
    "timestamp": "2026-02-25T12:00:00",
    "harness_version": "1.0.0",
    "model_name": "gpt-4o",
    "agent_name": "metagpt",
    "total_elapsed_seconds": 1234.5,
    "predictions_dir": "./generated"
  },
  "summary": {
    "total_repos": 30,
    "python_repos": 22,
    "java_repos": 8,
    "avg_pass_at_1": 0.4123,
    "avg_api_coverage": 0.7654,
    "deployment_success_rate": 0.6000,
    "pass_at_1_by_lang": { "python": 0.4500, "java": 0.3200 },
    "ac_by_lang":         { "python": 0.8100, "java": 0.6800 },
    "dsr_by_lang":        { "python": 0.6364, "java": 0.5000 }
  },
  "results": [
    {
      "repo_name": "Blog",
      "lang": "python",
      "port": 8000,
      "framework": "fastapi",
      "exit_code": 0,
      "elapsed_seconds": 47.2,
      "dsr": { "success": true, "message": "Service started successfully" },
      "pass_at_1": { "passed": 8, "failed": 2, "errors": 0, "skipped": 0, "total": 10, "score": 0.8 },
      "api_coverage": { "total_apis": 5, "implemented_apis": 4, "score": 0.8 }
    }
  ]
}
```

A human-readable summary table is also printed to stdout:

```
==========================================================================================
  RepoGenesis Evaluation Results
==========================================================================================
Repo Name                           Lang     DSR    Pass@1     AC
------------------------------------------------------------------------------------------
Blog                                python   PASS   8/10 (0.80) 4/5 (0.80)
flask                               python   PASS   6/8 (0.75)  3/4 (0.75)
javalin-online-judge                java     FAIL   0/6 (0.00)  2/4 (0.50)
...
------------------------------------------------------------------------------------------
  Total repos:              30
  Avg Pass@1:               0.4123
  Deployment Success Rate:  0.6000
  Avg API Coverage:         0.7654

  Pass@1 (Python):  0.4500  | Pass@1 (Java):  0.3200
  DSR (Python):     0.6364  | DSR (Java):     0.5000
  AC (Python):      0.8100  | AC (Java):      0.6800
==========================================================================================
```

#### Timeouts Reference

| Stage | Python | Java |
|---|---|---|
| Dependency install / build | 120 s | 300 s |
| Service startup | 15 s | 20 s |
| Test suite execution | 300 s | 600 s |
| Overall container timeout | 900 s | 900 s |

---

### Step 3 — Legacy Script Evaluation

These scripts are retained for reproducing results from the original paper. They require conda and run without Docker.

#### Pass@1 — Python

```bash
python evaluate_repos.py \
    --answer_dir <path-to-generated-repos> \
    --test_dir repo_golden_oracle \
    --output evaluation_results.json
```

Steps performed internally:
1. Install repo dependencies (`pip install -r requirements.txt`)
2. Start the service via `start.sh` (10 s startup wait)
3. Run `pytest tests/` with a 300 s timeout
4. Kill the service and clean up ports
5. Save per-repo Pass@1, coverage, and code metrics to JSON

#### Pass@1 — Java

```bash
python evaluate_repos_java.py \
    --answer_dir <path-to-generated-repos> \
    --test_dir <golden-oracle-java-dir> \
    --output evaluation_results_java.json
```

#### API Coverage (AC)

```bash
# All agent configurations
python calculate_api_coverage.py

# IDE-specific configurations
python calculate_api_coverage_ide.py

# Open-source agent configurations
python calculate_api_coverage_agents.py
```

#### Deployment Success Rate (DSR)

```bash
# Python repos
python test_dsr_repos.py

# Java repos
python exps/test_dsr.py

# Both Python and Java
python exps/test_all_dsr.py

# Shell-based DSR runner
bash exps/test_dsr.sh
```

---

### Step 4 — Aggregate and Reproduce Paper Results

1. **Generate** repositories for all agent/model configurations using the scripts in Step 1.
2. **Evaluate** each configuration using the Docker harness (Step 2) or legacy scripts (Step 3).
3. **Collect** the `report.json` files from each `--output_dir`.
4. **Compare** `summary.avg_pass_at_1`, `summary.deployment_success_rate`, and `summary.avg_api_coverage` across configurations.

The LLM-based scoring workflow (used in the paper for qualitative evaluation) can be run separately:

```bash
python -m evaluation.run_eval \
    --repo-root repo_readme \
    --output results.json
```

---

## Repository Structure

```
.
├── gen_and_eval.py                          # Python repo generation + evaluation entry point
├── gen_and_eval_Java.py                     # Java repo generation + evaluation entry point
├── evaluate_repos.py                        # Legacy Python Pass@1 evaluator (conda-based)
├── evaluate_repos_java.py                   # Legacy Java Pass@1 evaluator (conda-based)
├── calculate_api_coverage.py                # AC metric calculator
├── calculate_api_coverage_ide.py            # AC calculator (IDE configs)
├── calculate_api_coverage_agents.py         # AC calculator (agent configs)
├── test_dsr_repos.py                        # DSR tester (Python)
├── test_evaluate_repos.py                   # Unit tests for legacy orchestrator
├── requirements.txt                         # Root orchestrator dependencies
├── config.json                              # LLM config (base_url, api_key, model)
│
├── eval_harness/                            # Docker-based evaluation harness (recommended)
│   ├── run_evaluation.py                    # Main CLI entry point
│   ├── constants.py                         # 30 verified repo specs, timeouts, markers
│   ├── test_spec.py                         # RepoSpec dataclass + factory functions
│   ├── docker_build.py                      # Docker image build/remove/check
│   ├── docker_utils.py                      # Container lifecycle management
│   ├── grading.py                           # DSR + Pass@1 result grading
│   ├── log_parsers.py                       # pytest and Maven Surefire log parsers
│   ├── api_coverage.py                      # AC metric (static analysis)
│   ├── reporting.py                         # Report generation and summary table
│   ├── dockerfiles/
│   │   ├── Dockerfile.python                # Python evaluation image
│   │   └── Dockerfile.java                  # Java evaluation image
│   ├── scripts/
│   │   └── entrypoint.sh                    # 3-phase container entrypoint
│   └── tests/                               # 200 unit tests for eval_harness
│
├── agent/                                   # Agent framework adapters
├── evaluation/                              # LLM-based scoring workflow
├── exps/                                    # Experiment scripts and saved results
├── repo/                                    # Seed repos (READMEs for generation)
├── repo_golden_oracle/                      # Ground truth repos (code + tests)
├── repo_readme_verified/                    # 22 Python verified repos (README + tests)
├── repo_readme_verified_java_with_t_p/      # 8 Java verified repos (README + pom.xml + tests)
├── repo_readme_verified_python_no_t/        # 22 Python READMEs only (agent input)
├── repo_readme_verified_java_no_t_with_p/   # 8 Java READMEs + pom.xml (agent input)
└── sft_training/                            # SFT training pipeline
```

---

## Verified Benchmark Repos

### Python (22 repos)

| Repo Name | Framework | Port |
|---|---|---|
| Blog | FastAPI | 8000 |
| Chatroom | any | 8083 |
| Customization | FastAPI | 8082 |
| Data_Rank_Searcher | any | 8080 |
| django-rest-framework-crud | Django | 8000 |
| eve | Eve | 5001 |
| File_Relay | any | 8085 |
| flask | Flask | 5000 |
| GameBackend | any | 8080 |
| mail_service | any | 8080 |
| Multilingual | Flask | 5000 |
| rock-paper-scissors-flask | Flask | 5000 |
| simple-rbac-service | any | 8080 |
| SimpleFastPyAPI | FastAPI | 8000 |
| StructuredDataConvertor | any | 8000 |
| synapse | any | 8080 |
| TaskManagement | any | 8080 |
| Tic-Tac-Toe | any | 8082 |
| Timer4Tasker | any | 8080 |
| UserManagement | any | 8081 |
| UserManagement_2 | any | 8080 |
| WebPan | any | 8080 |

### Java (8 repos)

| Repo Name | Framework | Port |
|---|---|---|
| javalin-online-judge | Javalin | 7000 |
| javalin-task-manager | Javalin | 7000 |
| javalin-user-auth-platform | Javalin | 7070 |
| micronaut-ci-status | Micronaut | 8080 |
| quarkus-blog-cms | Quarkus | 8080 |
| spark-dashboard-backend | Spark | 4567 |
| spring-boot-course-scheduling | Spring Boot | 8080 |
| springboot-chat-gateway | Spring Boot | 8080 |

---

## Development

### Running the Harness Test Suite

```bash
# Run all 200 unit tests for eval_harness
python -m pytest eval_harness/tests/ -v --import-mode=importlib

# Run a specific test module
python -m pytest eval_harness/tests/test_grading.py -v --import-mode=importlib

# Run with coverage
python -m pytest eval_harness/tests/ --cov=eval_harness --cov-report=term-missing \
    --import-mode=importlib
```

### Running Legacy Unit Tests

```bash
python -m unittest test_evaluate_repos.py -v
```

### Code Style

- Python 3.10+, PEP 8, 4-space indentation, max ~100 chars per line
- Type hints on all function signatures (`Optional`, `Tuple`, `Dict`, `List` from `typing`)
- Use `pathlib.Path` for all filesystem paths
- Follow TDD: write or update tests before implementing new functionality
- When adding a new evaluation script, mirror the structure of existing ones: `argparse` for CLI, JSON output, `print`-based logging

### Adding a New Benchmark Repo

1. Add the repo spec to `eval_harness/constants.py`:

```python
REPO_SPECS["my-new-service"] = {
    "lang": "python",   # or "java"
    "port": 8080,
    "framework": "fastapi",
}
```

2. Add the README to `repo_readme_verified_python_no_t/my-new-service/README.md`.
3. Add golden oracle tests to `repo_readme_verified/my-new-service/tests/`.
4. Update `TOTAL_PYTHON_REPOS` (or `TOTAL_JAVA_REPOS`) in `constants.py`.
5. Add a test row to `eval_harness/tests/test_constants.py`.
