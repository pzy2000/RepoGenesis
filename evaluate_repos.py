import argparse
import os
import subprocess
import json
import time
import signal
import sys
import glob
import re
import ast

def count_tests_ast(test_dir):
    """Count test functions in a directory using AST."""
    total_tests = 0
    # Walk through the directory
    for root, _, files in os.walk(test_dir):
        for file in files:
            # Check for test files (test_*.py or *_test.py)
            if file.endswith('.py') and (file.startswith('test_') or file.endswith('_test.py')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=file_path)
                        
                    # Count functions starting with test_
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                            total_tests += 1
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
    return total_tests

def find_files_recursive(root_dir, filename):
    """Recursively find all files with a given name in a directory."""
    matches = []
    for root, dirnames, filenames in os.walk(root_dir):
        if filename in filenames:
            matches.append(os.path.join(root, filename))
    return matches

def install_requirements(requirements_path):
    """Install dependencies from a requirements.txt file."""
    print(f"Installing requirements from {requirements_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements from {requirements_path}: {e}")

def start_service(script_path):
    """Start the service using the start.sh script."""
    print(f"Starting service with {script_path}...")
    # Use preexec_fn to set a new process group so we can kill the whole tree later
    process = subprocess.Popen(
        ["bash", script_path],
        cwd=os.path.dirname(script_path),
        preexec_fn=os.setsid,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

def kill_process_group(process):
    """Kill the process group of the given process."""
    if process:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except Exception as e:
            print(f"Error killing process group: {e}")
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

def count_lines_and_tokens(directory):
    """Count files, lines of code, and estimate tokens."""
    total_files = 0
    total_lines = 0
    total_tokens = 0
    
    # Simple token estimation: split by whitespace
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'): # Only counting python files for now as per common practice, or should we count all?
                # User asked for "Files/LOC/Tokens", usually implies source code. 
                # Let's stick to text files that are likely code.
                ext = os.path.splitext(file)[1]
                if ext not in ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.h', '.sh', '.md']:
                    continue
                
                path = os.path.join(root, file)
                total_files += 1
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines()
                        total_lines += len(lines)
                        # Rough token count: words + punctuation
                        # A very rough approximation: len(content) / 4 is often used for char count, 
                        # but let's use a simple split for now.
                        tokens = len(re.findall(r'\w+|[^\w\s]', content))
                        total_tokens += tokens
                except Exception:
                    pass
    return total_files, total_lines, total_tokens

def run_pytest(test_dir, answer_dir):
    """Run pytest and return the output."""
    print(f"Running tests in {test_dir}...")
    # We want to measure coverage of the answer_dir
    cmd = [
        sys.executable, "-m", "pytest",
        test_dir,
        f"--cov={answer_dir}",
        "--cov-report=term-missing"
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300 # 5 minute timeout for tests
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1

def parse_pytest_output(output):
    """Parse pytest output for pass/fail counts and coverage."""
    passed = 0
    failed = 0
    coverage = 0.0
    
    # Parse passed/failed
    # Example: " 15 passed, 2 failed in 2.50s "
    match = re.search(r'(\d+) passed', output)
    if match:
        passed = int(match.group(1))
    
    match = re.search(r'(\d+) failed', output)
    if match:
        failed = int(match.group(1))
        
    # If no "passed" or "failed" found, but tests ran, maybe all passed or all failed?
    # Pytest output usually summarizes. If "collected X items" and then errors, we might miss it.
    # Let's rely on the summary line at the bottom.
    
    # Parse coverage
    # Example: "TOTAL     100      10    90%"
    # We look for the TOTAL line
    cov_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
    if cov_match:
        coverage = float(cov_match.group(1))
        
    return passed, failed, coverage

def evaluate_repo(repo_name, answer_repo_path, test_repo_path):
    print(f"=== Evaluating {repo_name} ===")
    
    # 1. Install global dependencies
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov", "uvicorn", "requests", "fastapi", "flask", "django"])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install global dependencies: {e}. Continuing assuming they are present or managed externally.")
    
    # 2. Install Answer Repo Requirements
    reqs = find_files_recursive(answer_repo_path, "requirements.txt")
    for req in reqs:
        install_requirements(req)
        
    # 3. Start Service
    start_scripts = find_files_recursive(answer_repo_path, "start.sh")
    service_process = None
    if start_scripts:
        # Assuming the first one is the main one or we need to run all?
        # User said "run ... start.sh (recursively search)". 
        # Usually there is only one entry point. Let's pick the one in the root-most directory if multiple.
        start_scripts.sort(key=lambda x: len(x.split(os.sep)))
        script_to_run = start_scripts[0]
        service_process = start_service(script_to_run)
        print("Waiting 10 seconds for service to start...")
        time.sleep(10)
    else:
        print("No start.sh found!")
        
    # 4. Install Test Repo Requirements
    test_reqs = find_files_recursive(test_repo_path, "requirements.txt")
    for req in test_reqs:
        install_requirements(req)
        
    # 5. Run Tests
    # Copy tests from test_repo_path to answer_repo_path if they are different
    # This ensures we run the golden tests against the answer code, and coverage is calculated correctly
    if os.path.abspath(answer_repo_path) != os.path.abspath(test_repo_path):
        print(f"Copying tests from {test_repo_path} to {answer_repo_path}...")
        tests_src = os.path.join(test_repo_path, "tests")
        tests_dst = os.path.join(answer_repo_path, "tests")
        
        if os.path.exists(tests_src):
            # Remove existing tests in answer repo if any, to ensure clean state
            if os.path.exists(tests_dst):
                print(f"Removing existing tests at {tests_dst}...")
                subprocess.run(["rm", "-rf", tests_dst], check=True)
            
            # Copy tests
            subprocess.run(["cp", "-R", tests_src, answer_repo_path], check=True)
            print(f"Copied tests to {tests_dst}")
        else:
             print(f"Warning: No 'tests' directory found in {test_repo_path}")

    # Run tests in the answer directory (where we just copied them)
    test_output, return_code = run_pytest(os.path.join(answer_repo_path, "tests"), answer_repo_path)
    print("Test output:", test_output)
    print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    # 6. Kill Service
    if service_process:
        kill_process_group(service_process)
        
    # 7. Collect Metrics
    passed, failed_pytest, coverage = parse_pytest_output(test_output)
    
    # Use AST to count total tests to account for collection failures/skips
    total_tests = count_tests_ast(os.path.join(test_repo_path, "tests"))
    
    # If AST count is 0 (maybe structure is different), fallback to pytest output or 0
    if total_tests == 0:
        print(f"Warning: AST found 0 tests in {test_repo_path}. Using pytest output count.")
        total_tests = passed + failed_pytest
        failed = failed_pytest
    else:
        # AST count might be lower than pytest count if there are parameterized tests.
        # But AST count might be higher than pytest count if there are collection failures.
        # We want to capture collection failures (AST > pytest), but avoid negative failures (AST < pytest).
        # So we take the max of AST count and pytest reported total.
        pytest_total = passed + failed_pytest
        if total_tests < pytest_total:
             print(f"Note: AST count ({total_tests}) is lower than pytest total ({pytest_total}). This is likely due to parameterized tests.")
             total_tests = pytest_total
             
        # Calculate failed as total - passed
        failed = total_tests - passed
        
    pass_rate = (passed / total_tests) if total_tests > 0 else 0.0
    
    files, loc, tokens = count_lines_and_tokens(answer_repo_path)
    
    return {
        "repo": repo_name,
        "pass_rate": pass_rate,
        "passed": passed,
        "failed": failed,
        "coverage": coverage,
        "files": files,
        "loc": loc,
        "tokens": tokens
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate repositories.")
    parser.add_argument("--answer_dir", default="/Volumes/T7/Real_Swe-bench/code/repo_readme_1128_msagent_answer")
    parser.add_argument("--test_dir", default="/Volumes/T7/Real_Swe-bench/code/repo_readme_test_oracle")
    parser.add_argument("--output", default="evaluation_results.json")
    parser.add_argument("--filter", help="Filter repos by name")
    
    args = parser.parse_args()
    
    results = []
    
    if not os.path.exists(args.answer_dir):
        print(f"Answer directory {args.answer_dir} does not exist.")
        return

    repos = [d for d in os.listdir(args.answer_dir) if os.path.isdir(os.path.join(args.answer_dir, d))]
    repos.sort()
    
    for repo in repos:
        if args.filter and args.filter not in repo:
            continue
            
        answer_repo_path = os.path.join(args.answer_dir, repo)
        test_repo_path = os.path.join(args.test_dir, repo)
        
        if not os.path.exists(test_repo_path):
            print(f"Test repo for {repo} not found at {test_repo_path}. Skipping.")
            continue
            
        try:
            metrics = evaluate_repo(repo, answer_repo_path, test_repo_path)
            results.append(metrics)
            print(f"Result for {repo}: {metrics}")
        except Exception as e:
            print(f"Error evaluating {repo}: {e}")
            
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
