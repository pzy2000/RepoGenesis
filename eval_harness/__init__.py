"""
RepoGenesis Evaluation Harness

A Docker-based evaluation framework for the RepoGenesis benchmark.
Evaluates generated microservice repositories across three metrics:
- Pass@1: Functional correctness (test pass rate)
- AC: API Coverage (fraction of specified endpoints implemented)
- DSR: Deployment Success Rate (service startup success)

Modeled after SWE-bench's harness architecture.

Usage:
    python -m eval_harness.run_evaluation \
        --predictions_dir ./generated_repos \
        --output_dir ./eval_results
"""

__version__ = "1.0.0"
