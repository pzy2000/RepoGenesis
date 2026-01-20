import argparse
import os
import subprocess
import json
import time
import signal
import sys
import glob
import re
import xml.etree.ElementTree as ET

# Try to import javalang, install if missing
try:
    import javalang
except ImportError:
    print("javalang not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "javalang"])
    import javalang

# Try to import pexpect, install if missing
try:
    import pexpect
except ImportError:
    print("pexpect not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pexpect"])
    import pexpect

def count_tests_java(test_dir):
    """Count test methods in a directory using javalang AST."""
    total_tests = 0
    # print(f"DEBUG: Searching for tests in {test_dir}")
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                # print(f"DEBUG: Found java file: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    tree = javalang.parse.parse(content)
                    
                    for path, node in tree.filter(javalang.tree.MethodDeclaration):
                        is_test = False
                        # Check annotations for @Test (JUnit 4/5)
                        if node.annotations:
                            for annotation in node.annotations:
                                if annotation.name == 'Test' or annotation.name.endswith('.Test'):
                                    is_test = True
                                    break
                                # Add other test annotations if needed (e.g., ParameterizedTest)
                                if 'ParameterizedTest' in annotation.name:
                                    is_test = True
                                    break
                        
                        # Check for JUnit 3 style (test* method name)
                        if not is_test and node.name.startswith('test'):
                            # Check if enclosing class extends TestCase
                            if len(path) >= 2:
                                parent = path[-2]
                                if isinstance(parent, javalang.tree.ClassDeclaration):
                                    if parent.extends and 'TestCase' in parent.extends.name:
                                        is_test = True
                                    # Heuristic: if class name ends with Test and method starts with test, count it
                                    elif parent.name.endswith('Test'):
                                        is_test = True
                        
                        if is_test:
                            # print(f"DEBUG: Found test method: {node.name} in {file}")
                            total_tests += 1
                            
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
                    # Fallback to Regex
                    try:
                        # Re-read content if needed, but we have it.
                        # Count @Test
                        matches_annotation = re.findall(r'@Test', content)
                        
                        # JUnit 3: public void test...
                        matches_junit3 = re.findall(r'public\s+void\s+test\w+', content)
                        
                        count = 0
                        if matches_annotation:
                            count = len(matches_annotation)
                        elif matches_junit3:
                            count = len(matches_junit3)
                            
                        if count > 0:
                            # print(f"DEBUG: Regex found {count} tests in {file}")
                            total_tests += count
                    except Exception as regex_e:
                        # print(f"Regex fallback failed: {regex_e}")
                        pass
    # print(f"DEBUG: Total tests found: {total_tests}")
    return total_tests

def find_file_recursive(root_dir, filename):
    """Recursively find the first occurrence of a file."""
    for root, _, files in os.walk(root_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

def run_java_tests(test_dir, answer_dir):
    """Run tests using run_tests.sh or mvnw."""
    # Search for run_tests.sh in answer_dir (which might be the root of the repo)
    run_script = find_file_recursive(answer_dir, "run_tests.sh")
    
    cmd = []
    cwd = answer_dir
    
    if run_script:
        print(f"Found test script: {run_script}")
        cmd = ["bash", run_script]
        cwd = os.path.dirname(run_script)
    else:
        # Check for mvnw
        mvnw = find_file_recursive(answer_dir, "mvnw")
        if mvnw:
            print(f"Found mvnw: {mvnw}")
            cmd = [mvnw, "clean", "test"]
            cwd = os.path.dirname(mvnw)
        else:
            # Fallback to system maven? Or just fail?
            # User prompt implies we should try to run tests.
            print("No run_tests.sh or mvnw found. Trying 'mvn test'...")
            cmd = ["mvn", "clean", "test"]
            
    print(f"Running tests with command: {' '.join(cmd)} in {cwd}")
    try:
        # Use pexpect to handle interactive prompts
        command = cmd[0]
        args = cmd[1:]
        
        # Spawn the process
        child = pexpect.spawn(command, args, cwd=cwd, encoding='utf-8', timeout=600)
        
        output = []
        
        while True:
            # Expect patterns:
            # 0: EOF (Process finished)
            # 1: TIMEOUT
            # 2: Interactive prompt "Press [r] to resume"
            # We use a list of patterns.
            index = child.expect([pexpect.EOF, pexpect.TIMEOUT, r"Press \[r\] to resume"], timeout=600)
            
            # Capture output
            if child.before:
                output.append(child.before)
                
            if index == 0: # EOF
                break
            elif index == 1: # TIMEOUT
                output.append("\nTIMEOUT")
                break
            elif index == 2: # Interactive prompt
                if isinstance(child.after, str):
                    output.append(child.after)
                print("Detected interactive prompt. Sending 'r'...")
                child.sendline('r')
        
        full_output = "".join(output)
        child.close()
        return full_output, child.exitstatus
        
    except Exception as e:
        return str(e), -1

def parse_java_test_output(answer_dir, stdout):
    """Parse test results from Surefire XML reports or stdout."""
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    
    # 1. Try parsing Surefire XML reports
    # They are usually in target/surefire-reports
    # We need to find where 'target' is. It's likely in the same dir where we ran tests.
    # But we might have multiple modules.
    
    xml_files = []
    for root, _, files in os.walk(answer_dir):
        if 'target' in root and 'surefire-reports' in root:
            for file in files:
                if file.endswith('.xml') and file.startswith('TEST-'):
                    xml_files.append(os.path.join(root, file))
                    
    if xml_files:
        print(f"Found {len(xml_files)} Surefire XML reports.")
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                # <testsuite tests="X" failures="Y" errors="Z" skipped="S" ...>
                # Note: 'tests' in XML usually means total tests run.
                # failures + errors = failed
                # skipped = skipped
                # passed = tests - failures - errors - skipped
                
                n_tests = int(root.attrib.get('tests', 0))
                n_failures = int(root.attrib.get('failures', 0))
                n_errors = int(root.attrib.get('errors', 0))
                n_skipped = int(root.attrib.get('skipped', 0))
                
                failed += n_failures + n_errors
                skipped += n_skipped
                passed += (n_tests - n_failures - n_errors - n_skipped)
            except Exception as e:
                print(f"Error parsing {xml_file}: {e}")
        
        return passed, failed, skipped
        
    # 2. Fallback to stdout parsing
    print("No Surefire XML reports found. Parsing stdout...")
    # Look for Maven summary: "Tests run: 15, Failures: 0, Errors: 0, Skipped: 0"
    # There might be multiple summaries for multi-module projects.
    # We should sum them up? Or look for the final reactor summary?
    # Actually, Maven prints a summary per module.
    # "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: ..."
    
    matches = re.findall(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)', stdout)
    if matches:
        for match in matches:
            n_tests, n_failures, n_errors, n_skipped = map(int, match)
            failed += n_failures + n_errors
            skipped += n_skipped
            passed += (n_tests - n_failures - n_errors - n_skipped)
            
    return passed, failed, skipped

def count_lines_and_tokens_java(directory):
    """Count files, lines of code, and estimate tokens for Java."""
    total_files = 0
    total_lines = 0
    total_tokens = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                path = os.path.join(root, file)
                total_files += 1
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines()
                        total_lines += len(lines)
                        tokens = len(re.findall(r'\w+|[^\w\s]', content))
                        total_tokens += tokens
                except Exception:
                    pass
    return total_files, total_lines, total_tokens

def start_service(answer_dir):
    """Find and run start.sh."""
    start_script = find_file_recursive(answer_dir, "start.sh")
    if start_script:
        print(f"Starting service with {start_script}...")
        try:
            process = subprocess.Popen(
                ["bash", start_script],
                cwd=os.path.dirname(start_script),
                preexec_fn=os.setsid,
                stdin=subprocess.DEVNULL
            )
            return process
        except Exception as e:
            print(f"Failed to start service: {e}")
    return None

def kill_process_group(process):
    if process:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

def fix_test_structure(answer_dir):
    """
    Fixes the test structure if tests are in a 'tests' directory
    but Maven expects them in 'src/test/java'.
    """
    src_test_java = os.path.join(answer_dir, "src", "test", "java")
    tests_dir = os.path.join(answer_dir, "tests")
    
    # If src/test/java doesn't exist but tests/ does
    if not os.path.exists(src_test_java) and os.path.exists(tests_dir):
        print(f"Detected 'tests' directory but no 'src/test/java'. Moving tests...")
        os.makedirs(src_test_java, exist_ok=True)
        
        # Copy all files from tests/ to src/test/java/
        # We use cp -r to handle potential subdirectories if any
        subprocess.run(["cp", "-R", f"{tests_dir}/.", src_test_java], check=True)
        print(f"Moved tests from {tests_dir} to {src_test_java}")

def fix_pom_java_version(answer_dir):
    """
    Updates pom.xml to use Java 17 if it's set to lower version.
    """
    pom_path = os.path.join(answer_dir, "pom.xml")
    if os.path.exists(pom_path):
        with open(pom_path, 'r') as f:
            content = f.read()
        
        # Simple string replacement for common patterns
        # <maven.compiler.source>11</maven.compiler.source> -> 17
        # <source>11</source> -> 17
        
        new_content = content.replace("<maven.compiler.source>11</maven.compiler.source>", "<maven.compiler.source>17</maven.compiler.source>")
        new_content = new_content.replace("<maven.compiler.target>11</maven.compiler.target>", "<maven.compiler.target>17</maven.compiler.target>")
        new_content = new_content.replace("<source>11</source>", "<source>17</source>")
        new_content = new_content.replace("<target>11</target>", "<target>17</target>")
        
        if content != new_content:
            print("Upgraded pom.xml to Java 17")
            with open(pom_path, 'w') as f:
                f.write(new_content)

def evaluate_repo(repo_name, answer_repo_path, test_repo_path):
    print(f"=== Evaluating {repo_name} ===")
    
    # 1. Start Service (if any)
    service_process = start_service(answer_repo_path)
    if service_process:
        print("Waiting 15 seconds for service to start...")
        time.sleep(15)
        
    # 2. Run Tests
    # We run tests in the answer_repo_path because that's where the code is.
    # Wait, usually we want to run the *test suite* from test_repo_path against the *code* in answer_repo_path.
    # But for Java/Maven, tests are usually inside `src/test/java`.
    # If the user provided a separate test_repo_path (golden oracle), we might need to copy tests from there to answer_repo_path?
    # Or just run the tests in answer_repo_path if they were generated/copied there.
    # The `evaluate_repos.py` for Python runs pytest on `test_repo_path` with coverage on `answer_repo_path`.
    # For Java, we can't easily "point" maven at a different dir for source.
    # Assumption: The answer repo *contains* the tests (either generated or copied).
    # OR: We need to copy tests from test_repo_path to answer_repo_path before running.
    # The user's `gen_and_eval.py` seems to "Restore tests from backup commit" or similar.
    # Let's assume for now we run what's in answer_repo_path.
    # BUT, if we are evaluating a generated repo against a golden test suite, we MUST ensure the golden tests are present.
    # Let's copy tests from test_repo_path/src/test to answer_repo_path/src/test if possible?
    
    # Let's add a step to copy tests if test_repo_path is different from answer_repo_path
    if os.path.abspath(answer_repo_path) != os.path.abspath(test_repo_path):
        print(f"Copying tests from {test_repo_path} to {answer_repo_path}...")
        # Assuming standard maven structure: src/test
        src_test = os.path.join(test_repo_path, "src", "test")
        # Also check for 'tests' folder as seen in golden oracle
        tests_dir = os.path.join(test_repo_path, "tests")
        
        if os.path.exists(src_test):
            # We use rsync or cp to overwrite
            subprocess.run(["cp", "-R", src_test, os.path.join(answer_repo_path, "src")], check=False)
        elif os.path.exists(tests_dir):
            subprocess.run(["cp", "-R", tests_dir, answer_repo_path], check=False)
            
    # Fix test structure if needed (e.g. tests/ vs src/test/java)
    fix_test_structure(answer_repo_path)
    
    # Fix pom.xml Java version if needed
    fix_pom_java_version(answer_repo_path)
            
    test_output, return_code = run_java_tests(test_repo_path, answer_repo_path)
    # print("Test output length:", len(test_output))
    
    # 3. Kill Service
    kill_process_group(service_process)
    
    # 4. Collect Metrics
    passed, failed_xml, skipped = parse_java_test_output(answer_repo_path, test_output)
    
    # Count total tests using AST from the *source of truth* (the tests we just ran)
    # If we copied tests, we should count in answer_repo_path/src/test
    # If not, answer_repo_path/src/test
    test_src_dir = os.path.join(answer_repo_path, "src", "test")
    if not os.path.exists(test_src_dir):
        test_src_dir = answer_repo_path # Fallback search whole dir
        
    total_tests_ast = count_tests_java(test_src_dir)
    
    # Reconcile counts
    # If XML parsing found tests, use that.
    # If AST found more, maybe some didn't run?
    # Ideally: total = max(AST, passed + failed + skipped)
    # failed = total - passed - skipped
    
    reported_total = passed + failed_xml + skipped
    
    if total_tests_ast > reported_total:
        print(f"Warning: AST counted {total_tests_ast} tests, but execution reported {reported_total}.")
        total_tests = total_tests_ast
        # If they didn't run, they are effectively failed or skipped. Let's count as failed for strictness?
        # Or just trust reported_total if we want "pass rate of executed tests".
        # But usually "pass rate" implies "of all intended tests".
        # Let's stick to the Python logic: max of both.
        failed = total_tests - passed - skipped
    else:
        total_tests = reported_total
        failed = failed_xml
        
    pass_rate = (passed / total_tests) if total_tests > 0 else 0.0
    
    files, loc, tokens = count_lines_and_tokens_java(answer_repo_path)
    
    return {
        "repo": repo_name,
        "pass_rate": pass_rate,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "files": files,
        "loc": loc,
        "tokens": tokens
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate Java repositories.")
    parser.add_argument("--answer_dir", required=True)
    parser.add_argument("--test_dir", required=True)
    parser.add_argument("--output", default="evaluation_results_java.json")
    parser.add_argument("--filter", help="Filter repos by name")
    
    args = parser.parse_args()
    
    results = []
    
    if not os.path.exists(args.answer_dir):
        print(f"Answer directory {args.answer_dir} does not exist.")
        return

    # Check if answer_dir is a single repo or a collection
    # If it contains 'pom.xml' or 'src', it's likely a single repo.
    # Otherwise treat as collection.
    is_single_repo = os.path.exists(os.path.join(args.answer_dir, "pom.xml")) or \
                     os.path.exists(os.path.join(args.answer_dir, "src"))
                     
    if is_single_repo:
        repos = [os.path.basename(args.answer_dir)]
        base_answer_dir = os.path.dirname(args.answer_dir)
        base_test_dir = os.path.dirname(args.test_dir)
    else:
        repos = [d for d in os.listdir(args.answer_dir) if os.path.isdir(os.path.join(args.answer_dir, d))]
        repos.sort()
        base_answer_dir = args.answer_dir
        base_test_dir = args.test_dir
    
    # print(f"DEBUG: Found {len(repos)} repos to evaluate.")
    
    for repo in repos:
        # print(f"DEBUG: Processing {repo}")
        if args.filter and args.filter not in repo:
            continue
            
        if is_single_repo:
             answer_repo_path = args.answer_dir
             test_repo_path = args.test_dir
        else:
            answer_repo_path = os.path.join(base_answer_dir, repo)
            test_repo_path = os.path.join(base_test_dir, repo)
        
        if not os.path.exists(test_repo_path):
            print(f"Test repo for {repo} not found at {test_repo_path}. Skipping.")
            continue
            
        try:
            metrics = evaluate_repo(repo, answer_repo_path, test_repo_path)
            results.append(metrics)
            print(f"Result for {repo}: {metrics}")
        except Exception as e:
            print(f"Error evaluating {repo}: {e}")
            import traceback
            traceback.print_exc()
    output_file = os.path.join("exps/evaluation_results", args.output)     
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
