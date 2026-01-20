# RepoGenesis: Benchmark for End-to-End Repository-Level Code Generation

This repository contains the code and data for the RepoGenesis benchmark, a comprehensive evaluation framework for assessing large language models' capability in generating complete web microservice repositories from natural language requirements.

> **Anonymous Submission**: This repository is provided for anonymous review. All author-identifying information has been removed.

## Overview

RepoGenesis is the first comprehensive benchmark for evaluating repository-level code generation from natural language requirements. Unlike existing benchmarks that focus on function-level or class-level code generation, RepoGenesis challenges models to generate complete, functional repositories from scratch.

**Key Features:**
- **106 diverse web microservice repositories** (60 Python, 46 Java)
- **11 web frameworks** including Flask, Django, FastAPI, Javalin, Spring Boot, and more
- **18 application domains** covering authentication, content management, gaming, file management, and more
- **Multi-dimensional metrics**: Pass@1 for functional correctness, API Coverage (AC) for implementation completeness, and Deployment Success Rate (DSR) for deployability
- **Support for multiple agents**: MetaGPT, DeepCode, Qwen-Agent, MS-Agent, and commercial IDEs

## Directory Structure

```
code/
├── README.md                                    # This file
├── config.json                                  # Configuration file
├── requirements.txt                             # Dependencies
│
├── repo/                                        # Verified repositories (30 repos)
│
├── gen_and_eval.py                              # Main generation and evaluation script
├── gen_and_eval_Java.py                         # Java-specific generation and evaluation
│
├── evaluate_repos.py                            # Repository evaluation script
├── evaluate_repos_java.py                       # Java repository evaluation script
│
├── calculate_api_coverage.py                   # API Coverage metric calculation
├── calculate_api_coverage_agents.py             # AC calculation for open-source agents
├── calculate_api_coverage_ide.py                # AC calculation for IDE experiments
│
├── analyze_difficulty.py                        # Python repository difficulty classification
├── analyze_java_difficulty.py                   # Java repository difficulty classification
│
├── agent/                                       # Agent framework
│   ├── MetaGPT/                                 # MetaGPT agent
│   ├── DeepCode/                                # DeepCode agent
│   ├── Qwen-Agent/                              # Qwen-Agent framework
│   └── ms-agent/                                # MS-Agent framework
```

## Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Java**: JDK 17 or higher (for Java repository evaluation)
- **Conda**: Required for isolated test environments
- **Git**: For repository management

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd code
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure API Keys

The benchmark supports multiple LLM providers. Configure your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional
```

### Step 4: Install Agent Frameworks (Optional)

If you want to evaluate specific agent frameworks:

```bash
# MetaGPT
git clone https://github.com/FoundationAgents/MetaGPT.git
cd MetaGPT
pip install -e .

# DeepCode (requires additional configuration)
git clone https://github.com/HKUDS/DeepCode.git
cd DeepCode
pip install -e .

# Qwen-Agent
git clone https://github.com/QwenLM/Qwen-Agent.git
cd Qwen-Agent
pip install -e .

# MS-Agent
git clone https://github.com/modelscope/ms-agent.git
cd ms-agent
pip install -e .
```

## Dataset

### Repository Structure

Each repository in RepoGenesis consists of:

1. **README.md**: Comprehensive requirement document specifying:
   - Service functionality description
   - API endpoint definitions with input/output schemas
   - Authentication mechanisms
   - Error handling specifications
   - Operational constraints (ports, deployment requirements)

2. **tests/**: Black-box test suite containing:
   - Functional correctness tests
   - Error handling tests
   - Edge case tests
   - Integration tests

## Usage

### 1. Generate Repositories with Agents

#### Using Open-Source Agents

```bash
# MetaGPT
python gen_and_eval.py \
    --agent metagpt \
    --repo_root repo_readme_verified \
    --repo_name <repository-name> \
    --llm_model gpt-4o \
    --llm_api_key $OPENAI_API_KEY

# DeepCode
python gen_and_eval.py \
    --agent deepcode \
    --repo_root repo_readme_verified \
    --repo_name <repository-name> \
    --deepcode_openai_key $OPENAI_API_KEY

# Qwen-Agent
python gen_and_eval.py \
    --agent qwen-agent \
    --repo_root repo_readme_verified \
    --repo_name <repository-name> \
    --llm_model qwen-max-latest \
    --llm_api_key $DASHSCOPE_API_KEY \
    --llm_base_url https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### For Java Repositories

```bash
python gen_and_eval_Java.py \
    --agent <agent-name> \
    --repo_root repo_readme_verified_java \
    --repo_name <java-repository-name> \
    --llm_model gpt-4o \
    --llm_api_key $OPENAI_API_KEY
```

### 2. Evaluate Generated Repositories

#### Basic Evaluation (Pass@1)

```bash
python evaluate_repos.py \
    --answer_dir <path-to-generated-repos> \
    --test_dir repo_golden_oracle \
    --output evaluation_results.json
```

This will:
1. Install repository dependencies
2. Start the service (if `start.sh` exists)
3. Run pytest test suite
4. Calculate Pass@1, coverage, and code metrics
5. Save results to JSON

#### Calculate API Coverage

```bash
# For IDE experiments
python calculate_api_coverage_ide.py

# For open-source agents
python calculate_api_coverage_agents.py
```

API Coverage (AC) measures what percentage of required API endpoints are correctly implemented in the generated repository.

#### Deployment Success Rate (DSR)

DSR evaluation checks if generated repositories can be successfully deployed. See the paper for detailed methodology.

### 3. Analyze Difficulty Classification

```bash
# Analyze Python repositories
python analyze_difficulty.py

# Analyze Java repositories  
python analyze_java_difficulty.py

# Visualize difficulty distributions
python visualize_difficulty.py
```

These scripts compute composite scores based on:
- Lines of Code (LOC)
- Cyclomatic Complexity
- File Count
- API Endpoints
- Functions and Classes

## Evaluation Metrics

### Pass@1 (Functional Correctness)

Measures whether the generated repository passes all test cases on the first attempt:

```
Pass@1 = (Number of passed test cases) / (Total test cases)
```

A repository achieves Pass@1 = 1.0 only if all test cases pass.

### API Coverage (AC)

Measures implementation completeness by checking if all required API endpoints are present:

```
AC = (Number of implemented API endpoints) / (Total required API endpoints)
```

API endpoints are extracted from README specifications and validated in the generated code.

### Deployment Success Rate (DSR)

Measures basic deployability by checking if:
1. Dependencies can be installed
2. Service can start without errors
3. Health check endpoint responds

### Reproducing Paper Results

1. **Generate repositories** for all agent/IDE configurations
2. **Run evaluations** using `evaluate_repos.py` and `evaluate_repos_java.py`
3. **Calculate metrics** using AC and DSR scripts
4. **Aggregate results** - metrics are automatically saved to JSON files

## Citation

If you use RepoGenesis in your research, please cite our paper:

```bibtex
@article{anonymous2025RepoGenesis,
  title={RepoGenesis: Benchmarking End-to-End Microservice Generation from Readme to Repository},
  author={Anonymous},
  journal={Under Review},
  year={2025}
}
```
