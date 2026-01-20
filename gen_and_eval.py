#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Optional, Tuple


def read_readme(repo_root: Path) -> str:
    readme_files = [
        repo_root / "README.md",
        repo_root / "readme.md",
        repo_root / "README",
        repo_root / "Readme.md",
    ]
    for f in readme_files:
        if f.exists():
            return f.read_text(encoding="utf-8", errors="ignore")
    raise FileNotFoundError(f"README not found under {repo_root}")


def read_requirements(repo_root: Path) -> str:
    req_file = repo_root / "requirements.txt"
    if req_file.exists():
        return req_file.read_text(encoding="utf-8", errors="ignore")
    return ""


def ensure_conda_available() -> str:
    conda_exe = shutil.which("conda")
    if not conda_exe:
        raise RuntimeError("conda is required but was not found on PATH")
    return conda_exe


def ensure_event_loop() -> None:
    """Ensure there is a current asyncio event loop in this thread.
    Some libraries call asyncio.get_event_loop() during construction
    and expect a loop to be set.
    """
    try:
        asyncio.get_running_loop()
        return
    except RuntimeError:
        pass
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

def create_pytest_env(env_name: str, requirements_file: Optional[Path]) -> None:
    conda_exe = ensure_conda_available()
    # Create env with a reasonable Python version compatible with most repos
    subprocess.run(
        [conda_exe, "create", "-y", "-n", env_name, "python=3.10"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Ensure pip + pytest
    subprocess.run(
        [conda_exe, "run", "-n", env_name, "python", "-m", "pip", "install", "--upgrade", "pip", "pytest"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if requirements_file and requirements_file.exists():
        subprocess.run(
            [conda_exe, "run", "-n", env_name, "python", "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )


def parse_pytest_summary(output: str) -> Tuple[int, int, int]:
    """
    Returns (passed, failed, errors) based on pytest short summary lines.
    """
    passed = failed = errors = 0
    # Common summary line examples:
    # "== 10 passed in 0.12s =="
    # "== 8 passed, 2 failed in 0.34s =="
    # "== 7 passed, 1 error in 0.22s =="
    m = re.search(r"=+\s*(.+?)\s*=+", output)
    if m:
        segment = m.group(1)
        m_pass = re.search(r"(\d+)\s+passed", segment)
        m_fail = re.search(r"(\d+)\s+failed", segment)
        m_err = re.search(r"(\d+)\s+error", segment)
        if m_pass:
            passed = int(m_pass.group(1))
        if m_fail:
            failed = int(m_fail.group(1))
        if m_err:
            errors = int(m_err.group(1))
    return passed, failed, errors


def metagpt_generate(repo_root: Path, readme_text: str, requirements_text: str) -> None:
    # Ensure local MetaGPT source is importable when not installed via pip
    import sys
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_meta_path = os.path.join(workspace_root, "agent", "MetaGPT")
    if agent_meta_path not in sys.path and os.path.isdir(agent_meta_path):
        sys.path.insert(0, agent_meta_path)
    from metagpt.software_company import generate_repo

    # Ensure an event loop exists before MetaGPT constructs roles
    ensure_event_loop()
    # Use official API to generate directly into repo_root
    idea = textwrap.dedent(
        f"""
        You are a senior software engineer tasked with implementing a complete software project.

        Project Requirements:
        README:
        {readme_text}

        requirements.txt (reference):
        {requirements_text}

        Your task:
        1. Analyze the README and referenced requirements to understand the project requirements.
        2. Design the complete project structure and architecture.
        3. Implement ALL necessary files including:
           - Main application files
           - Configuration files
           - Dependencies/requirements files (requirements.txt is required)
           - Documentation files
           - Any additional files needed for the project to run
        4. Ensure the project can be started via a single shell command writen in a file named start.sh.
        5. The generated start.sh MUST:
            * Listen on 0.0.0.0
            * Use a common port (e.g., 8000) or the one specified in the README
            * Use ONLY the correct command for the detected framework
        6. If a web service is expected, bind to 0.0.0.0 and use the port.
        7. Write production-ready, well-documented code.

        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.
        """
    ).strip()

    # generate_repo is sync; it respects project_path
    generate_repo(
        idea=idea,
        project_name=repo_root.name,
        inc=False,
        project_path=str(repo_root),
        implement=True,
        run_tests=False,
        code_review=True,
        n_round=5,
        investment=3.0,
    )


def deepcode_generate(repo_root: Path, readme_text: str, requirements_text: str) -> None:
    """Use DeepCode workflows to synthesize code based on README into repo_root.
    Strategy:
    - Create an implementation plan file from the README in repo_root.
    - Invoke DeepCode CodeImplementationWorkflow in pure code mode targeting repo_root.
    - Move generated files from generate_code/ up to repo_root.
    """
    # Ensure DeepCode is importable
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_deep_path = os.path.join(workspace_root, "agent", "DeepCode")
    if agent_deep_path not in sys.path and os.path.isdir(agent_deep_path):
        sys.path.insert(0, agent_deep_path)

    from workflows.code_implementation_workflow import CodeImplementationWorkflow

    repo_root.mkdir(parents=True, exist_ok=True)

    # Prepare plan file derived from README
    plan_path = repo_root / "initial_plan.txt"
    plan_content = textwrap.dedent(
        f"""
        You are a senior software engineer tasked with implementing a complete software project.

        Project Requirements:
        README:
        {readme_text}

        requirements.txt (reference):
        {requirements_text}

        Your task:
        1. Analyze the README and referenced requirements to understand the project requirements.
        2. Design the complete project structure and architecture.
        3. Implement ALL necessary files including:
           - Main application files
           - Configuration files
           - Dependencies/requirements files (requirements.txt is required)
           - Documentation files
           - Any additional files needed for the project to run
        4. Ensure the project can be started via a single shell command writen in a file named start.sh.
        5. The generated start.sh MUST:
            * Listen on 0.0.0.0
            * Use a common port (e.g., 8000) or the one specified in the README
            * Use ONLY the correct command for the detected framework
        6. If a web service is expected, bind to 0.0.0.0 and use the port.
        7. Write production-ready, well-documented code.

        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.
        """
    ).strip()
    plan_path.write_text(plan_content, encoding="utf-8")

    # Preflight: ensure config and API keys
    secrets_path = os.path.join(agent_deep_path, "mcp_agent.secrets.yaml")
    config_path = os.path.join(agent_deep_path, "mcp_agent.config.yaml")
    if not os.path.isfile(config_path):
        print("[deepcode] WARNING: mcp_agent.config.yaml not found; DeepCode may use defaults")
    if not os.path.isfile(secrets_path):
        print("[deepcode] WARNING: mcp_agent.secrets.yaml not found; ensure LLM keys via env")
    if not os.environ.get("OPENAI_API_KEY"):
        print("[deepcode] WARNING: OPENAI_API_KEY not set; DeepCode may fail to call LLM")

    # Ensure expected code workspace exists to satisfy DeepCode's existence checks
    gen_dir = repo_root / "generate_code"
    gen_dir.mkdir(parents=True, exist_ok=True)

    # Run DeepCode workflow asynchronously (pure code mode). This will create generate_code/ under repo_root
    workflow = CodeImplementationWorkflow(config_path=secrets_path if os.path.isfile(secrets_path) else "mcp_agent.secrets.yaml")
    cwd = os.getcwd()
    try:
        # Run inside DeepCode directory so relative configs resolve
        os.chdir(agent_deep_path)
        asyncio.run(
            workflow.run_workflow(
                plan_file_path=str(plan_path),
                target_directory=str(repo_root),
                pure_code_mode=True,
                enable_read_tools=False,
            )
        )
    finally:
        os.chdir(cwd)

    # Move generated code from generate_code into repo_root (flatten one level)
    if gen_dir.exists() and gen_dir.is_dir():
        for root, dirs, files in os.walk(gen_dir):
            rel = os.path.relpath(root, str(gen_dir))
            dest_dir = repo_root / rel if rel != "." else repo_root
            dest_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                src = Path(root) / f
                dst = dest_dir / f
                # Overwrite existing files to reflect latest generation
                shutil.copy2(src, dst)


def qwen_agent_generate(repo_root: Path, readme_text: str, requirements_text: str, args) -> None:
    """Use Qwen-Agent to synthesize code based on README into repo_root.
    Strategy:
    - Import Qwen-Agent from agent/Qwen-Agent.
    - Create an Assistant agent with code_interpreter tool.
    - Send a comprehensive prompt to implement the entire project per README.
    - Files will be generated in the current working directory (repo_root).
    """
    # Ensure Qwen-Agent is importable
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_qwen_path = os.path.join(workspace_root, "agent", "Qwen-Agent")
    if agent_qwen_path not in sys.path and os.path.isdir(agent_qwen_path):
        sys.path.insert(0, agent_qwen_path)

    try:
        from qwen_agent.agents import Assistant
        from qwen_agent.utils.output_beautify import typewriter_print
    except ImportError as e:
        print(f"[qwen-agent] Failed to import Qwen-Agent: {e}")
        print("[qwen-agent] Creating placeholder files...")
        repo_root.mkdir(parents=True, exist_ok=True)
        marker = repo_root / "AGENT.txt"
        marker.write_text("Generated by Qwen-Agent adapter (import failed)\n", encoding="utf-8")
        return

    repo_root.mkdir(parents=True, exist_ok=True)

    # Configure LLM - try multiple options
    llm_cfg = None
    # if os.environ.get("DASHSCOPE_API_KEY"):
    #     llm_cfg = {
    #         'model': 'qwen-max-latest',
    #         'model_type': 'qwen_dashscope',
    #     }
    if args.llm_api_key:
        llm_cfg = {
            'model': args.llm,
            'model_server': args.llm_base_url,
            'api_key': args.llm_api_key,
        }
    else:
        print("[qwen-agent] No API key found (DASHSCOPE_API_KEY or OPENAI_API_KEY)")
        print("[qwen-agent] Creating placeholder files...")
        marker = repo_root / "AGENT.txt"
        marker.write_text("Generated by Qwen-Agent adapter (no API key)\n", encoding="utf-8")
        return

    # Create system instruction for comprehensive project implementation
    system_instruction = textwrap.dedent(f"""
        You are a senior software engineer tasked with implementing a complete software project.
        
        Project Requirements:
        README:
        {readme_text}
        
        requirements.txt (reference):
        {requirements_text}
        
        Your task:
        1. Analyze the README and referenced requirements to understand the project requirements.
        2. Design the complete project structure and architecture.
        3. Implement ALL necessary files including:
           - Main application files
           - Configuration files
           - Dependencies/requirements files (requirements.txt is required)
           - Documentation files
           - Any additional files needed for the project to run
        4. Ensure the project can be started via a single shell command writen in a file named start.sh.
        5. The generated start.sh MUST:
            * Listen on 0.0.0.0
            * Use a common port (e.g., 8000) or the one specified in the README
            * Use ONLY the correct command for the detected framework
        6. If a web service is expected, bind to 0.0.0.0 and use the port.
        7. Write production-ready, well-documented code.
        
        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.
        """).strip()

    # Create Assistant agent with code interpreter
    tools = ['code_interpreter']
    bot = Assistant(
        llm=llm_cfg,
        system_message=system_instruction,
        function_list=tools
    )

    # Prepare comprehensive implementation prompt
    implementation_prompt = textwrap.dedent(f"""
        Please implement the complete software project based on the README and requirements.
        
        Current working directory: {repo_root}
        
        Steps to follow:
        1. First, analyze the requirements and create a project structure plan
        2. Create all necessary directories using os.makedirs()
        3. Implement all source code files with proper imports and dependencies
        4. Create configuration files including requirements.txt
        5. Create a main entry point that can start the application
        6. Test that the basic structure is correct
        
        Make sure to:
        - Use proper file paths relative to current directory
        - Include error handling and logging where appropriate
        - Follow best practices for the technology stack
        - Create a README.md with usage instructions
        
        Start implementing now!
        """).strip()

    # Run the agent in the target directory
    cwd = os.getcwd()
    try:
        os.chdir(str(repo_root))
        
        messages = [{'role': 'user', 'content': implementation_prompt}]
        response_text = ""
        
        print("[qwen-agent] Starting project implementation...")
        for response in bot.run(messages=messages):
            # Stream output and collect final response
            if isinstance(response, list) and response:
                for msg in response:
                    if msg.get('role') == 'assistant' and msg.get('content'):
                        content = msg['content']
                        response_text += content
                        print(content, end='', flush=True)
        
        print(f"\n[qwen-agent] Implementation completed in {repo_root}")
        
    except Exception as e:
        print(f"[qwen-agent] Error during implementation: {e}")
        # Create fallback marker
        marker = repo_root / "AGENT.txt"
        marker.write_text(f"Generated by Qwen-Agent adapter (error: {e})\n", encoding="utf-8")
    finally:
        os.chdir(cwd)


def ms_agent_generate(repo_root: Path, readme_text: str, requirements_text: str, args) -> None:
    """Use MS-Agent to synthesize code based on README into repo_root.
    Strategy:
    - Import MS-Agent from agent/ms-agent.
    - Create an LLMAgent with code generation capabilities.
    - Send a comprehensive prompt to implement the entire project per README.
    - Files will be generated in the current working directory (repo_root).
    """
    # Ensure MS-Agent is importable
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_ms_path = os.path.join(workspace_root, "agent", "ms-agent")
    if agent_ms_path not in sys.path and os.path.isdir(agent_ms_path):
        sys.path.insert(0, agent_ms_path)

    try:
        from ms_agent import LLMAgent
    except ImportError as e:
        print(f"[ms-agent] Failed to import MS-Agent: {e}")
        print("[ms-agent] Creating placeholder files...")
        repo_root.mkdir(parents=True, exist_ok=True)
        marker = repo_root / "AGENT.txt"
        marker.write_text("Generated by MS-Agent adapter (import failed)\n", encoding="utf-8")
        return

    repo_root.mkdir(parents=True, exist_ok=True)

    # Configure API key - MS-Agent supports ModelScope API and OpenAI
    # if not os.environ.get("MODELSCOPE_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
    #     print("[ms-agent] No API key found (MODELSCOPE_API_KEY or OPENAI_API_KEY)")
    #     print("[ms-agent] Creating placeholder files...")
    #     marker = repo_root / "AGENT.txt"
    #     marker.write_text("Generated by MS-Agent adapter (no API key)\n", encoding="utf-8")
    #     return

    # Prepare comprehensive implementation prompt based on README
    implementation_prompt = textwrap.dedent(f"""
        You are a senior software engineer. Please implement a complete software project based on the following requirements.

        Project Requirements:
        README:
        {readme_text}

        requirements.txt (reference):
        {requirements_text}

        Your task:
        1. Analyze the README and referenced requirements to understand the project requirements.
        2. Design the complete project structure and architecture.
        3. Implement ALL necessary files including:
           - Main application files
           - Configuration files
           - Dependencies/requirements files (requirements.txt is required)
           - Documentation files
           - Any additional files needed for the project to run
        4. Ensure the project can be started via a single shell command writen in a file named start.sh.
        5. The generated start.sh MUST:
            * Listen on 0.0.0.0
            * Use a common port (e.g., 8000) or the one specified in the README
            * Use ONLY the correct command for the detected framework
        6. If a web service is expected, bind to 0.0.0.0 and use the port.
        7. Write production-ready, well-documented code.

        Important: Generate ALL files in the current working directory. Do not reference or peek at any tests directory.
        """).strip()

    # Run the agent in the target directory
    cwd = os.getcwd()
    try:
        os.chdir(str(repo_root))
        
        async def run_ms_agent():
            # Save original sys.argv and clear it to avoid MS-Agent parsing conflicts
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]]  # Keep only script name
            
            try:
                # Create config with API key
                from omegaconf import OmegaConf
                
                config_dict = {
                    'llm': {
                        'service': 'openai',
                        'model': args.llm_model.strip(),
                    },
                    'generation_config': {
                        'temperature': 1,
                        'stream': True
                    },
                    'max_chat_round': 100,
                    'callbacks': []
                }
                
                # Add API key based on what's available
                # if args.modelscope_api_key:
                #     config_dict['llm']['service'] = 'modelscope'
                #     config_dict['llm']['modelscope_api_key'] = args.modelscope_api_key.strip()
                if args.llm_api_key:
                    config_dict['llm']['openai_api_key'] = args.llm_api_key.strip()
                    # Add base_url if it looks like a custom endpoint
                    api_key = args.llm_api_key
                    config_dict['llm']['openai_base_url'] = args.llm_base_url.strip()
                else:
                    raise RuntimeError("args.llm_api_key not provided")
                
                config = OmegaConf.create(config_dict)
                
                # Initialize the agent with config
                llm_agent = LLMAgent(config=config)
                # Run the implementation task
                print("[ms-agent] Starting project implementation...")
                result = await llm_agent.run(implementation_prompt)
                return result
            finally:
                # Restore original sys.argv
                sys.argv = original_argv
        
        # Run the async agent
        result = asyncio.run(run_ms_agent())
        
        print(f"\n[ms-agent] Implementation completed in {repo_root}")
        if result:
            print(f"[ms-agent] Result summary: {str(result)[:200]}...")
        
    except Exception as e:
        print(f"[ms-agent] Error during implementation: {e}")
        import traceback
        traceback.print_exc()
        # Create fallback marker
        marker = repo_root / "AGENT.txt"
        marker.write_text(f"Generated by MS-Agent adapter (error: {e})\n", encoding="utf-8")
    finally:
        os.chdir(cwd)


async def metagpt_start_command(repo_root: Path) -> str:
    # Ensure local MetaGPT source is importable when not installed via pip
    root_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = root_dir
    agent_meta_path = os.path.join(workspace_root, "agent", "MetaGPT")
    if agent_meta_path not in sys.path and os.path.isdir(agent_meta_path):
        sys.path.insert(0, agent_meta_path)
    from metagpt.roles.di.data_interpreter import DataInterpreter

    prompt = textwrap.dedent(
        """
        Analyze the project in {repo_root} and output a single shell command to start the app.
        - Only output the command prefixed with START_COMMAND: and nothing else.
        - Avoid backgrounding with &; emit the foreground command. Example format:
          START_COMMAND: FLASK_APP=web_app flask run --host=0.0.0.0 --port=8000
        """
    ).strip()

    di = DataInterpreter()
    cwd = os.getcwd()
    result = None
    try:
        os.chdir(str(repo_root))
        # Retry up to 5 times to mitigate transient WAF/501 issues
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                result = await di.run(prompt)
                break
            except Exception as e:
                err_text = str(e)
                if "openai.InternalServerError" in err_text or "501page" in err_text:
                    # Transient upstream issue, retry after a short delay
                    try:
                        await asyncio.sleep(min(2 * attempt, 10))
                    except Exception:
                        pass
                    continue
                # Non-WAF errors: break to fallback handling
                result = None
                break

        # If still no result after retries, try a simplified prompt once
        if result is None:
            simple_prompt = "START_COMMAND:"
            try:
                result = await di.run(simple_prompt)
            except Exception:
                # Swallow and allow downstream fallback
                result = None
    finally:
        os.chdir(cwd)

    # DataInterpreter may return None or complex objects; capture from its logs/return as string
    if result is None:
        result = ""
    if not isinstance(result, str):
        try:
            result = json.dumps(result)
        except Exception:
            result = str(result)
    m = re.search(r"START_COMMAND:\s*(.+)", result)
    if not m:
        # Fallback: try to detect common frameworks
        if (repo_root / "app.py").exists():
            return "python app.py"
        if (repo_root / "manage.py").exists():
            return "python manage.py runserver 0.0.0.0:8000"
        return "python -m http.server 8000"
    return m.group(1).strip()


def start_service(command: str, repo_root: Path) -> subprocess.Popen:
    env = os.environ.copy()
    # Ensure unbuffered python output for logs
    env.setdefault("PYTHONUNBUFFERED", "1")
    # Start the service
    proc = subprocess.Popen(
        command,
        cwd=str(repo_root),
        env=env,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc


def run_pytest_in_env(env_name: str, repo_root: Path) -> Tuple[int, str]:
    conda_exe = ensure_conda_available()
    cmd = [conda_exe, "run", "-n", env_name, "pytest", "-q"]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.returncode, proc.stdout


def terminate_process(proc: Optional[subprocess.Popen]) -> None:
    if not proc:
        return
    if proc.poll() is None:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            try:
                os.kill(proc.pid, signal.SIGKILL)
            except Exception:
                pass


def write_temp_metagpt_config(model: str, base_url: str, api_key: str) -> Path:
    """Write a minimal MetaGPT config2.yaml to a temp file and return its path."""
    content = textwrap.dedent(
        f"""
        llm:
          api_type: "openai"
          model: "{model}"
          base_url: "{base_url}"
          api_key: "{api_key}"
        """
    ).strip() + "\n"
    tmpdir = Path(tempfile.mkdtemp(prefix="metagpt_cfg_"))
    cfg = tmpdir / "config2.yaml"
    cfg.write_text(content, encoding="utf-8")
    return cfg


def git_backup_repo(workspace: Path, repo_root: Path, message: str) -> str:
    """Create a git commit backing up the repo_root subtree. Return commit id (HEAD).
    If there is nothing to commit, still return current HEAD.
    """
    rel = os.path.relpath(str(repo_root), str(workspace))
    # Stage only the target subtree
    subprocess.run(["git", "add", "-A", "--", rel], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    commit = subprocess.run(
        ["git", "commit", "-m", message, "--no-gpg-sign"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Always capture HEAD after attempting commit
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(workspace), text=True).strip()
    return head


def git_reset_to(workspace: Path, commit_id: str) -> None:
    result = subprocess.run(["git", "reset", "--hard", commit_id], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to reset to commit {commit_id}: {result.stderr}")
    else:
        print("git reset result:", result.stdout)


def git_restore_path(workspace: Path, commit_id: str, rel_path: str) -> None:
    """Restore a specific path from a given commit into working tree.
    Prefer `git restore`, fallback to `git checkout` for older Git.
    """
    # Try git restore
    proc = subprocess.run([
        "git", "restore", "--source", commit_id, "--", rel_path
    ], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        # Fallback to checkout syntax
        subprocess.run(["git", "checkout", commit_id, "--", rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def git_clean_path(workspace: Path, rel_path: str) -> None:
    """Remove untracked files/dirs only within a specific path.
    Keeps ignored files (does not use -x) to avoid deleting cache/artifacts elsewhere.
    """
    subprocess.run(["git", "clean", "-fd", "--", rel_path], cwd=str(workspace), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def copy_repo_to_results(workspace: Path, repo_root: Path) -> Path:
    """Copy the entire repo subtree to <workspace>/results/<repo_root_basename> for later review."""
    results_dir = workspace / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    dest_dir = results_dir / repo_root.name
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(repo_root, dest_dir)
    return dest_dir


def process_single_repo(args: argparse.Namespace, workspace: Path, repo_name: str) -> None:
    repo_root = workspace / args.repo_root / repo_name
    if not repo_root.exists():
        raise FileNotFoundError(f"Target directory not found: {repo_root}")

    # Read README as the sole source of spec
    readme_text = read_readme(repo_root)
    # Read requirements.txt as optional context
    requirements_text = read_requirements(repo_root)

    service_proc: Optional[subprocess.Popen] = None
    env_name: Optional[str] = None
    backup_commit = git_backup_repo(workspace, repo_root, message=f"backup before metagpt for {repo_name}")
    # Remove tests before generation
    tests_dir = repo_root / "tests"
    if tests_dir.exists():
        shutil.rmtree(tests_dir)

    try:
        if args.agent.lower() == "metagpt":
            # Optionally set MetaGPT config via env var if provided
            if args.metagpt_config:
                os.environ.setdefault("METAGPT_CONFIG", str(Path(args.metagpt_config).resolve()))
            else:
                # Allow CLI overrides or OPENAI_API_KEY fallback to avoid NotFoundError
                llm_model = args.llm_model.strip()
                llm_base_url = args.llm_base_url.strip()
                llm_api_key = args.llm_api_key.strip() or os.environ.get("OPENAI_API_KEY", "")
                # If any override provided or OPENAI_API_KEY exists, create a temp config
                if llm_model or llm_base_url or llm_api_key:
                    if not llm_model:
                        llm_model = "gpt-4o-mini"
                    if not llm_base_url:
                        llm_base_url = "https://api.openai.com/v1"
                    if not llm_api_key:
                        raise RuntimeError("OPENAI_API_KEY is not set and --llm_api_key not provided")
                    cfg_path = write_temp_metagpt_config(llm_model, llm_base_url, llm_api_key)
                    os.environ["METAGPT_CONFIG"] = str(cfg_path)
            # Generate project contents with MetaGPT (synchronous API)
            metagpt_generate(repo_root, readme_text, requirements_text)
            print("metagpt_generate done")
            # Ask for start command and start service
            # start_cmd = asyncio.run(metagpt_start_command(repo_root))
            # print("metagpt_start_command done")
            # Restore tests from backup commit to run pytest
            rel_repo = os.path.relpath(str(repo_root), str(workspace))
            tests_rel_path = os.path.join(rel_repo, "tests")
            git_restore_path(workspace, backup_commit, tests_rel_path)
        elif args.agent.lower() == "deepcode":
            # Provide OPENAI_API_KEY to DeepCode if passed
            if args.deepcode_openai_key and not os.environ.get("OPENAI_API_KEY"):
                os.environ["OPENAI_API_KEY"] = args.deepcode_openai_key
            # Simple adapter: place a marker and proceed to startup/test flow
            deepcode_generate(repo_root, readme_text, requirements_text)
            # Heuristic start command for DeepCode projects if any
            start_cmd = "python -m streamlit run app.py" if (repo_root / "app.py").exists() else "python -m http.server 8000"
        elif args.agent.lower() == "qwen-agent":
            # Generate code using Qwen-Agent
            qwen_agent_generate(repo_root, readme_text, requirements_text, args)
            # Heuristic start command for Qwen-Agent projects
            if (repo_root / "app.py").exists():
                start_cmd = "python app.py"
            elif (repo_root / "main.py").exists():
                start_cmd = "python main.py"
            elif (repo_root / "manage.py").exists():
                start_cmd = "python manage.py runserver 0.0.0.0:8000"
            else:
                start_cmd = "python -m http.server 8000"
        elif args.agent.lower() == "ms-agent":
            # Generate code using MS-Agent
            # ms_agent_generate(repo_root, readme_text, requirements_text, args)
            # # Heuristic start command for MS-Agent projects
            # if (repo_root / "app.py").exists():
            #     start_cmd = "python app.py"
            # elif (repo_root / "main.py").exists():
            #     start_cmd = "python main.py"
            # elif (repo_root / "server.py").exists():
            #     start_cmd = "python server.py"
            # elif (repo_root / "manage.py").exists():
            #     start_cmd = "python manage.py runserver 0.0.0.0:8000"
            # else:
            #     start_cmd = "python -m http.server 8000"
            raise NotImplementedError("USE PYTHONPATH=. openai_api_key=xxx openai_base_url=xxxx python ms_agent/cli/cli.py run --config projects/service --trust_remote_code true --repo /Volumes/T7/Real_Swe-bench/code/repo_readme_repeat to run ms-agent")
        else:
            raise NotImplementedError(f"Agent '{args.agent}' is not supported yet")

        # print(f"[agent] start command: {start_cmd}")
        # service_proc = start_service(start_cmd, repo_root)
        # print("start_service done")
        # # Give the service some time to boot up
        # try:
        #     boot_output = service_proc.stdout.readline().strip()
        #     if boot_output:
        #         print(f"[service] {boot_output}")
        # except Exception:
        #     pass
        # print("boot_output done")
        # # Prepare pytest environment (requirements file may have been deleted with tests)
        # tests_req = repo_root / "tests" / "requirements.txt"
        # env_name = f"pytest-{repo_name}-{os.getpid()}"
        # create_pytest_env(env_name, tests_req if tests_req.exists() else None)
        # print("create_pytest_env done")
        # # Run pytest
        # rc, out = run_pytest_in_env(env_name, repo_root)
        # print(out)
        # passed, failed, errors = parse_pytest_summary(out)
        # total = passed + failed + errors
        # pass_at_1 = 1.0 if rc == 0 else 0.0

        # print(json.dumps({
        #     "repo": repo_name,
        #     "passed": passed,
        #     "failed": failed,
        #     "errors": errors,
        #     "total": total,
        #     "pass_at_1": pass_at_1,
        # }, ensure_ascii=False))

    finally:
        terminate_process(service_proc)
        # Clean up env
        if env_name:
            try:
                conda_exe = ensure_conda_available()
                subprocess.run([conda_exe, "env", "remove", "-y", "-n", env_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            except Exception:
                pass
        # Save generated repo for later review before reset
        try:
            copy_repo_to_results(workspace, repo_root)
        except Exception:
            pass
        # Restore only the target repo subtree to backup snapshot and clean untracked within it
        # try:
            # rel_repo = os.path.relpath(str(repo_root), str(workspace))
            # git_restore_path(workspace, backup_commit, rel_repo)
            # git_clean_path(workspace, rel_repo)
        # except Exception:
            # pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and evaluate repos with agents")
    parser.add_argument("--agent", required=True, help="Agent name under agent folder (e.g., metagpt)")
    parser.add_argument("--repo_root", required=True, help="Repo root directory")
    parser.add_argument("--repo", required=True, help="Target repo name under repo_scratch (e.g., Blog)")
    parser.add_argument("--workspace", default="/Volumes/T7/Real_Swe-bench/code", help="Workspace root path")
    parser.add_argument("--metagpt_config", default="", help="Optional MetaGPT config yaml path")
    parser.add_argument("--llm_model", default="", help="Override LLM model (e.g., gpt-4o-mini)")
    parser.add_argument("--llm_base_url", default="", help="Override LLM base URL (e.g., https://api.openai.com/v1)")
    parser.add_argument("--llm_api_key", default="", help="Override LLM API key (or rely on OPENAI_API_KEY)")
    parser.add_argument("--llm", help="Override LLM (e.g., gpt-5-mini)")
    parser.add_argument("--deepcode_openai_key", default="", help="OPENAI_API_KEY for DeepCode if not set in env")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if args.repo.lower() == "all":
        base_dir = workspace / args.repo_root
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory not found: {base_dir}")
        # Iterate through all direct subdirectories as repos
        for entry in sorted(p.name for p in base_dir.iterdir() if p.is_dir()):
            process_single_repo(args, workspace, entry)
    else:
        process_single_repo(args, workspace, args.repo)


if __name__ == "__main__":
    main()


