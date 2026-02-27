#!/usr/bin/env python3
"""
Test runner script for GameBackend API tests.
Provides convenient commands to run different test suites.
"""
import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    try:
        import pytest
        import requests
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False


def run_all_tests():
    """Run all test suites."""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
    return run_command(cmd, "All Test Suites")


def run_room_matching_tests():
    """Run room matching tests."""
    cmd = ["python", "-m", "pytest", "tests/test_room_matching.py", "-v", "--tb=short"]
    return run_command(cmd, "Room Matching Tests")


def run_leaderboard_tests():
    """Run leaderboard tests."""
    cmd = ["python", "-m", "pytest", "tests/test_leaderboard.py", "-v", "--tb=short"]
    return run_command(cmd, "Leaderboard Tests")


def run_game_state_tests():
    """Run game state synchronization tests."""
    cmd = ["python", "-m", "pytest", "tests/test_game_state_sync.py", "-v", "--tb=short"]
    return run_command(cmd, "Game State Synchronization Tests")


def run_smoke_tests():
    """Run smoke tests (basic functionality)."""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "smoke", "-v", "--tb=short"]
    return run_command(cmd, "Smoke Tests")


def run_integration_tests():
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "integration", "-v", "--tb=short"]
    return run_command(cmd, "Integration Tests")


def run_unit_tests():
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "unit", "-v", "--tb=short"]
    return run_command(cmd, "Unit Tests")


def run_with_coverage():
    """Run tests with coverage report."""
    cmd = [
        "python", "-m", "pytest", 
        "tests/", 
        "--cov=app", 
        "--cov-report=html", 
        "--cov-report=term-missing",
        "-v"
    ]
    return run_command(cmd, "Tests with Coverage")


def run_parallel_tests():
    """Run tests in parallel."""
    cmd = ["python", "-m", "pytest", "tests/", "-n", "auto", "-v"]
    return run_command(cmd, "Parallel Tests")


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
    return run_command(cmd, f"Specific Test: {test_path}")


def lint_code():
    """Run code linting."""
    cmd = ["flake8", "tests/", "--max-line-length=100", "--ignore=E203,W503"]
    return run_command(cmd, "Code Linting")


def format_code():
    """Format code with black."""
    cmd = ["black", "tests/", "--line-length=100"]
    return run_command(cmd, "Code Formatting")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="GameBackend API Test Runner")
    parser.add_argument(
        "command",
        choices=[
            "all", "room", "leaderboard", "game-state", "smoke", 
            "integration", "unit", "coverage", "parallel", "lint", "format"
        ],
        help="Test command to run"
    )
    parser.add_argument(
        "--test",
        help="Run specific test file or function"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies before running tests"
    )
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
    
    # Change to tests directory
    tests_dir = Path(__file__).parent
    os.chdir(tests_dir)
    
    success = True
    
    if args.command == "all":
        success = run_all_tests()
    elif args.command == "room":
        success = run_room_matching_tests()
    elif args.command == "leaderboard":
        success = run_leaderboard_tests()
    elif args.command == "game-state":
        success = run_game_state_tests()
    elif args.command == "smoke":
        success = run_smoke_tests()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "unit":
        success = run_unit_tests()
    elif args.command == "coverage":
        success = run_with_coverage()
    elif args.command == "parallel":
        success = run_parallel_tests()
    elif args.command == "lint":
        success = lint_code()
    elif args.command == "format":
        success = format_code()
    
    if args.test:
        success = run_specific_test(args.test)
    
    if success:
        print(f"\n{'='*60}")
        print("🎉 All operations completed successfully!")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n{'='*60}")
        print("💥 Some operations failed!")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
