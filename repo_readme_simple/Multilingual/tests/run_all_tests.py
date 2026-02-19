"""
Comprehensive test runner for all API endpoints
Calculates test case pass rate and repository pass rate
"""

import subprocess
import sys
import time
import requests


BASE_URL = "http://localhost:5000"


def check_service_availability():
    """Check if the service is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/languages", timeout=2)
        return response.status_code == 200
    except:
        return False


def wait_for_service(max_retries=30, delay=1):
    """Wait for the service to be available"""
    print("Checking if service is available...")
    for i in range(max_retries):
        if check_service_availability():
            print(f"✓ Service is available at {BASE_URL}")
            return True
        if i < max_retries - 1:
            print(f"  Waiting for service... ({i+1}/{max_retries})")
            time.sleep(delay)
    return False


def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f"\n{'='*70}")
    print(f"Running: {test_file}")
    print('='*70)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Parse results from output
        output = result.stdout
        passed = 0
        failed = 0
        
        # Look for the results line
        for line in output.split('\n'):
            if 'passed' in line and 'failed' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if 'passed' in parts[i+1] if i+1 < len(parts) else False:
                            passed = int(part)
                        elif 'failed' in parts[i+1] if i+1 < len(parts) else False:
                            failed = int(part)
        
        # If parsing failed, use exit code
        if passed == 0 and failed == 0:
            if result.returncode == 0:
                # Assume all tests passed if exit code is 0
                # Count test functions
                with open(test_file, 'r') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                    passed = test_count
            else:
                # Assume all tests failed if exit code is not 0
                with open(test_file, 'r') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                    failed = test_count
        
        return {
            'file': test_file,
            'passed': passed,
            'failed': failed,
            'exit_code': result.returncode,
            'success': result.returncode == 0
        }
    
    except subprocess.TimeoutExpired:
        print(f"✗ Test timeout: {test_file}")
        return {
            'file': test_file,
            'passed': 0,
            'failed': 1,
            'exit_code': -1,
            'success': False
        }
    except Exception as e:
        print(f"✗ Error running test: {e}")
        return {
            'file': test_file,
            'passed': 0,
            'failed': 1,
            'exit_code': -1,
            'success': False
        }


def calculate_metrics(results):
    """Calculate test case pass rate and repository pass rate"""
    total_passed = sum(r['passed'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_tests = total_passed + total_failed
    
    # Test case pass rate
    test_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Repository pass rate (all test files must pass)
    repos_passed = sum(1 for r in results if r['success'])
    repos_total = len(results)
    repo_pass_rate = (repos_passed / repos_total * 100) if repos_total > 0 else 0
    
    return {
        'total_tests': total_tests,
        'total_passed': total_passed,
        'total_failed': total_failed,
        'test_pass_rate': test_pass_rate,
        'repos_total': repos_total,
        'repos_passed': repos_passed,
        'repo_pass_rate': repo_pass_rate
    }


def print_summary(results, metrics):
    """Print test summary and metrics"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for result in results:
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        print(f"{status} | {result['file']}")
        print(f"       | Passed: {result['passed']}, Failed: {result['failed']}")
    
    print("\n" + "="*70)
    print("METRICS")
    print("="*70)
    print(f"Test Case Pass Rate:")
    print(f"  - Total Tests: {metrics['total_tests']}")
    print(f"  - Passed: {metrics['total_passed']}")
    print(f"  - Failed: {metrics['total_failed']}")
    print(f"  - Pass Rate: {metrics['test_pass_rate']:.2f}%")
    print()
    print(f"Repository Pass Rate:")
    print(f"  - Total Test Files: {metrics['repos_total']}")
    print(f"  - Passed: {metrics['repos_passed']}")
    print(f"  - Failed: {metrics['repos_total'] - metrics['repos_passed']}")
    print(f"  - Pass Rate: {metrics['repo_pass_rate']:.2f}%")
    print("="*70)


def main():
    """Main test runner"""
    print("="*70)
    print("MULTILINGUAL API TEST SUITE")
    print("="*70)
    print(f"Target URL: {BASE_URL}")
    print(f"Python: {sys.version}")
    print()
    
    # Check service availability
    if not wait_for_service():
        print("\n✗ ERROR: Service is not available!")
        print(f"Please ensure the service is running at {BASE_URL}")
        print("Start the service with: python app.py")
        sys.exit(1)
    
    # Test files to run
    test_files = [
        'test_translate.py',
        'test_timezone.py',
        'test_localize.py',
        'test_languages.py'
    ]
    
    print(f"\nFound {len(test_files)} test files")
    
    # Run all tests
    results = []
    for test_file in test_files:
        result = run_test_file(test_file)
        results.append(result)
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    
    # Print summary
    print_summary(results, metrics)
    
    # Exit with appropriate code
    if metrics['repo_pass_rate'] == 100:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ Some tests failed. Repository pass rate: {metrics['repo_pass_rate']:.2f}%")
        sys.exit(1)


if __name__ == "__main__":
    main()

