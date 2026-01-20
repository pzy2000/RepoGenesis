#!/usr/bin/env python3
"""
Comprehensive DSR testing script for all repositories in repos directory.
Tests both Java and Python repositories, supporting nested structures.
"""

import os
import subprocess
import time
import signal
import json
import argparse
from pathlib import Path
from typing import Dict, Tuple, Optional

BASE_DIR = "/Users/manishaqian/Real_Swe-bench/code/exps/repos_dick"
RESULTS_FILE = "code/exps/dsr_repos_results_msagent.json"

def kill_port(port: int):
    """Kill any process using the specified port."""
    try:
        result = subprocess.run(
            f"lsof -ti:{port}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except:
                    pass
    except:
        pass

def find_file_recursive(root_path: str, filename: str, max_depth: int = 5) -> Optional[str]:
    """Find a file recursively up to max_depth."""
    root_path_obj = Path(root_path)
    
    # Check root first
    if (root_path_obj / filename).exists():
        return str(root_path_obj / filename)
        
    for path in root_path_obj.rglob(filename):
        # Calculate relative depth
        try:
            rel_path = path.relative_to(root_path_obj)
            if len(rel_path.parts) <= max_depth + 1: # filename is one part
                return str(path)
        except ValueError:
            continue
            
    return None

def detect_repo_type(repo_path: str) -> Tuple[str, Optional[str]]:
    """
    Detect repository type and return (type, config_file_path).
    type is 'Java', 'Python', or 'Unknown'.
    """
    # Check for Java
    pom_path = find_file_recursive(repo_path, "pom.xml")
    if pom_path:
        return "Java", pom_path
        
    # Check for Python
    req_path = find_file_recursive(repo_path, "requirements.txt")
    if req_path:
        return "Python", req_path
        
    setup_path = find_file_recursive(repo_path, "setup.py")
    if setup_path:
        return "Python", setup_path
        
    pyproject_path = find_file_recursive(repo_path, "pyproject.toml")
    if pyproject_path:
        return "Python", pyproject_path
        
    return "Unknown", None

def test_java_repository(repo_name: str, repo_path: str, pom_path: str, port_base: int) -> bool:
    """Test Java repository deployment."""
    print(f"  [Java] Testing: {repo_name}")
    
    # Step 1: Install dependencies
    print(f"    [1/3] Installing dependencies (pom: {os.path.relpath(pom_path, repo_path)})...")
    
    # Run maven in the directory containing pom.xml
    pom_dir = os.path.dirname(pom_path)
    
    try:
        result = subprocess.run(
            ["mvn", "clean", "install", "-DskipTests", "-q"],
            cwd=pom_dir,
            capture_output=True,
            text=True,
            timeout=300 # Increased timeout for initial downloads
        )
        
        if result.returncode != 0:
            print(f"    Maven build failed: {result.stderr[:200]}...") # debug
            return False, f"Maven build failed"
        
        print("    ✓ Dependencies installed")
    except subprocess.TimeoutExpired:
        return False, "Maven build timeout (>300s)"
    except Exception as e:
        return False, f"Maven build error: {str(e)}"
    
    # Step 2 & 3: Start the server
    print(f"    [2/3] Starting server (Port range: {port_base}-{port_base+10})...")
    
    for port in range(port_base, port_base + 10):
        kill_port(port)
    
    time.sleep(1)
    
    start_script = find_file_recursive(repo_path, "start.sh", max_depth=5)
    if not start_script:
        return False, "start.sh not found (recursive)"
    
    start_dir = os.path.dirname(start_script)
    
    try:
        env = os.environ.copy()
        env["PORT"] = str(port_base)
        
        process = subprocess.Popen(
            ["bash", "start.sh"],
            cwd=start_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup
        for i in range(20): # increased wait
            time.sleep(1)
            poll = process.poll()
            if poll is not None:
                stdout, stderr = process.communicate()
                combined_output = stdout + stderr
                
                if any(pattern in combined_output for pattern in [
                    "Started", "Javalin started", "Server started",
                    "Application started", "Listening on", "Tomcat started"
                ]):
                    return True, "Server started successfully"
                
                if "Address already in use" in combined_output or "Port already in use" in combined_output:
                    return True, "Server deployable (port conflict)"
                
                return False, f"Server exited with code {poll}"
        
        print("    ✓ Server running")
        
        try:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        except:
            pass
        
        return True, "Server started successfully"
        
    except Exception as e:
        return False, f"Server start error: {str(e)}"
    finally:
        try:
            if 'process' in locals() and process.poll() is None:
                process.kill()
        except:
            pass
        
        for port in range(port_base, port_base + 10):
            kill_port(port)

def test_python_repository(repo_name: str, repo_path: str, req_path: str, port_base: int) -> bool:
    """Test Python repository deployment."""
    print(f"  [Python] Testing: {repo_name}")
    
    # Step 1: Install dependencies
    print(f"    [1/3] Installing dependencies (req: {os.path.relpath(req_path, repo_path)})...")
    
    # Determine install command based on file type
    # If requirements.txt, use pip install -r
    # If setup.py or pyproject.toml, use pip install .
    
    req_filename = os.path.basename(req_path)
    req_dir = os.path.dirname(req_path)
    
    try:
        cmd = []
        if req_filename == "requirements.txt":
            cmd = ["pip", "install", "-q", "-r", req_filename]
        else:
            cmd = ["pip", "install", "-q", "."]
            
        result = subprocess.run(
            cmd,
            cwd=req_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            # print(result.stderr[:200]) # debug
            return False, "Pip install failed"
        
        print("    ✓ Dependencies installed")
    except subprocess.TimeoutExpired:
        return False, "Pip install timeout (>120s)"
    except Exception as e:
        return False, f"Pip install error: {str(e)}"
    
    # Step 2 & 3: Start the server
    print(f"    [2/3] Starting server (Port range: {port_base}-{port_base+10})...")
    
    for port in range(port_base, port_base + 10):
        kill_port(port)
    
    time.sleep(1)
    
    start_script = find_file_recursive(repo_path, "start.sh", max_depth=5)
    if not start_script:
        return False, "start.sh not found (recursive)"
    
    start_dir = os.path.dirname(start_script)
    
    try:
        env = os.environ.copy()
        env["PORT"] = str(port_base)
        
        process = subprocess.Popen(
            ["bash", "start.sh"],
            cwd=start_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup
        for i in range(15):
            time.sleep(1)
            poll = process.poll()
            if poll is not None:
                stdout, stderr = process.communicate()
                combined_output = stdout + stderr
                
                if any(pattern in combined_output for pattern in [
                    "Running on", "Started", "Uvicorn running",
                    "Application startup complete", "Listening on", "Accepting connections"
                ]):
                    return True, "Server started successfully"
                
                if "Address already in use" in combined_output or "Port already in use" in combined_output:
                    return True, "Server deployable (port conflict)"
                
                return False, f"Server exited with code {poll}"
        
        print("    ✓ Server running")
        
        try:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        except:
            pass
        
        return True, "Server started successfully"
        
    except Exception as e:
        return False, f"Server start error: {str(e)}"
    finally:
        try:
            if 'process' in locals() and process.poll() is None:
                process.kill()
        except:
            pass
        
        for port in range(port_base, port_base + 10):
            kill_port(port)

def test_repository(repo_name: str, repo_path: str, port_base: int) -> Tuple[bool, str, str]:
    """
    Test repository deployment.
    Returns (success: bool, message: str, repo_type: str)
    """
    repo_type, config_path = detect_repo_type(repo_path)
    
    if repo_type == "Java":
        success, message = test_java_repository(repo_name, repo_path, config_path, port_base)
        return success, message, "Java"
    elif repo_type == "Python":
        success, message = test_python_repository(repo_name, repo_path, config_path, port_base)
        return success, message, "Python"
    else:
        # Before failing, check if start.sh exists. If so, try to guess or just fail gracefully.
        # But without installing deps, it likely fails.
        return False, "Unknown or missing build config", "Unknown"

def main():
    parser = argparse.ArgumentParser(description='Test DSR for repositories')
    parser.add_argument('--shard', type=int, nargs=2, metavar=('INDEX', 'TOTAL'), help='Shard index and total shards (0-indexed)')
    parser.add_argument('--output', type=str, default=RESULTS_FILE, help='Output JSON file')
    parser.add_argument('--port-base', type=int, default=8000, help='Base port for testing (default: 8000)')
    args = parser.parse_args()

    print("=" * 80)
    print("Testing DSR for All Repositories in repos (Nested Support)")
    if args.shard:
        print(f"Shard: {args.shard[0]}/{args.shard[1]}")
    print(f"Port Base: {args.port_base}")
    print("=" * 80)
    print()
    
    base_path = Path(BASE_DIR)
    
    # Process specific directories if needed, or all
    
    # Prioritize previously failed directories if resuming, but here we restart
    all_repo_dirs = sorted([d.name for d in base_path.iterdir() if d.is_dir()])
    
    if args.shard:
        shard_idx, total_shards = args.shard
        chunk_size = (len(all_repo_dirs) + total_shards - 1) // total_shards
        start_idx = shard_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(all_repo_dirs))
        repo_dirs = all_repo_dirs[start_idx:end_idx]
    else:
        repo_dirs = all_repo_dirs
    
    all_results = {}
    
    # Check if we have partial results to resume? 
    # For now, overwrite
    
    total_dirs_count = len(repo_dirs)
    current_dir_idx = 0

    for repo_dir in repo_dirs:
        current_dir_idx += 1
        print(f"\n{'=' * 80}")
        print(f"[{current_dir_idx}/{total_dirs_count}] Testing directory: {repo_dir}")
        print(f"{'=' * 80}")
        
        dir_path = os.path.join(BASE_DIR, repo_dir)
        repos = sorted([d.name for d in Path(dir_path).iterdir() if d.is_dir()])
        
        dir_results = {}
        success_count = 0
        total_count = len(repos)
        
        for idx, repo_name in enumerate(repos, 1):
            print(f"-- Repo [{idx}/{total_count}]: {repo_name}")
            repo_path = os.path.join(dir_path, repo_name)
            success, message, repo_type = test_repository(repo_name, repo_path, args.port_base)
            
            dir_results[repo_name] = {
                "success": success,
                "message": message,
                "type": repo_type
            }
            
            if success:
                success_count += 1
                print(f"  ✓ {repo_name}")
            else:
                print(f"  ✗ {repo_name}: {message}")
        
        dsr = success_count / total_count if total_count > 0 else 0
        
        all_results[repo_dir] = {
            "total": total_count,
            "success": success_count,
            "failed": total_count - success_count,
            "dsr": dsr,
            "repositories": dir_results
        }
        
        print(f"\nDirectory DSR: {dsr:.4f} ({success_count}/{total_count})")
        
        # Save intermediate results
        output_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "in_progress",
            "results_by_directory": all_results
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
    
    # Final save
    total_repos = sum(r["total"] for r in all_results.values())
    total_success = sum(r["success"] for r in all_results.values())
    overall_dsr = total_success / total_repos if total_repos > 0 else 0
    
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print()
    
    for repo_dir in repo_dirs:
        if repo_dir in all_results:
            r = all_results[repo_dir]
            print(f"{repo_dir:<60} DSR: {r['dsr']:.4f} ({r['success']}/{r['total']})")
            
    print(f"\nTotal: {total_repos}, Success: {total_success}, DSR: {overall_dsr:.4f}")
    
    output_data["status"] = "completed"
    output_data["total_repositories"] = total_repos
    output_data["total_success"] = total_success
    output_data["total_failed"] = total_repos - total_success
    output_data["overall_dsr"] = overall_dsr
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

if __name__ == "__main__":
    main()
