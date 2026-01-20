#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_pattern=None, verbose=False, coverage=False, parallel=False):
    cmd = ["python", "-m", "pytest"]
    
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append("test_blog_api.py")
    
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
        "--color=yes",
        "--durations=10"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Running test failed: {e}")
        return 1


def check_dependencies():
    required_packages = ["pytest", "requests"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing dependencies: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Blog CMS API Test Runner")
    parser.add_argument("--pattern", "-p", help="Test pattern (e.g., test_01_*)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", "-n", action="store_true", help="Run tests in parallel")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("All dependencies are installed")
            return 0
        else:
            return 1
    
    if not check_dependencies():
        return 1
    
    return run_tests(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel
    )


if __name__ == "__main__":
    sys.exit(main())