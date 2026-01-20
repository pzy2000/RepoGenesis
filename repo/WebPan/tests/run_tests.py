#!/usr/bin/env python3

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type: str = "all", verbose: bool = True, coverage: bool = False):
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    if test_type == "auth":
        cmd.extend(["-m", "auth"])
    elif test_type == "upload":
        cmd.extend(["-m", "upload"])
    elif test_type == "download":
        cmd.extend(["-m", "download"])
    elif test_type == "share":
        cmd.extend(["-m", "share"])
    elif test_type == "storage":
        cmd.extend(["-m", "storage"])
    elif test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    else:
        cmd.append(".")
    
    cmd.append(".")
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="WebPan API Test Runner")
    parser.add_argument(
        "--type", 
        choices=["all", "auth", "upload", "download", "share", "storage", "unit", "integration", "fast", "slow"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Run tests in quiet mode"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--html-report", 
        action="store_true",
        help="Generate HTML test report"
    )
    
    args = parser.parse_args()
    
    cmd = ["python", "-m", "pytest"]
    
    if not args.quiet:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    if args.html_report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])
    
    if args.type == "auth":
        cmd.extend(["-m", "auth"])
    elif args.type == "upload":
        cmd.extend(["-m", "upload"])
    elif args.type == "download":
        cmd.extend(["-m", "download"])
    elif args.type == "share":
        cmd.extend(["-m", "share"])
    elif args.type == "storage":
        cmd.extend(["-m", "storage"])
    elif args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "fast":
        cmd.extend(["-m", "not slow"])
    elif args.type == "slow":
        cmd.extend(["-m", "slow"])
    else:
        cmd.append(".")
    
    cmd.append(".")
    
    print(f"Running WebPan API tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
