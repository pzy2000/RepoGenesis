User: 如果我想模仿swe-bench的harness evaluation脚本，做一个RepoGenesis的eval脚本，要求端到端方便复现，应该使用docker还是local environment？如果你有问题，可以问我

Workspace: Collecting workspace informationFiltering to most relevant information我有几个问题帮助我给出更好的建议：

1. **目标用户**：是希望外部研究者复现结果，还是主要是内部使用？
2. **当前评估流程**：我看到 evaluate_repos.py 用的是 conda 隔离，evaluate_repos_java.py 用 Maven。现有的隔离机制够用吗，还是经常出现环境冲突？
3. **服务依赖**：各个 repo 的微服务除了自身代码，还有外部依赖吗（比如 Redis、PostgreSQL、消息队列等）？
4. **测试类型**：测试全是 HTTP 黑盒测试，还是也有单元测试需要访问内部模块？
5. **规模**：一次评估通常跑多少个 repo？并发还是串行？
6. **平台要求**：需要支持 Windows 吗，还是 Linux/macOS 即可？

这些答案会直接影响 Docker vs Local 的选择。

User: 1. 希望外部研究者复现结果
2. conda够用，maven不确定
3. 没有
4. HTTP 黑盒测试
5. 串行，不然端口可能冲突
6. 能支持windows更好

GitHub Copilot: 基于你的回答，建议使用 **Docker**。理由如下：

## 为什么选 Docker

| 需求 | Local (conda) | Docker |
|------|--------------|--------|
| 外部研究者复现 | ❌ 需要手动装 conda/JDK/Maven | ✅ 一条命令 |
| Windows 支持 | ❌ conda 在 Windows 行为不一致 | ✅ Docker Desktop 统一 |
| Maven 隔离 | ❌ 不确定够不够用 | ✅ 容器内完全隔离 |
| HTTP 黑盒测试 | ✅ 够用 | ✅ 同样支持 |
| 串行无端口冲突 | ✅ 够用 | ✅ 容器网络更干净 |

---

## 推荐架构

核心思路：**一个 repo 一个容器，eval harness 在宿主机协调**，类似 SWE-bench 的做法。

```
eval_harness (宿主机 Python)
    │
    ├── 读取 generated repo
    ├── docker build → 镜像
    ├── docker run → 容器内启动服务 + 跑测试
    ├── 收集 stdout/stderr 结果
    └── 写入 JSON
```

---

## 建议的文件结构

```
eval_harness/
├── run_eval.py              # 主入口，替代现有 evaluate_repos.py
├── Dockerfile.python        # Python repo 基础镜像
├── Dockerfile.java          # Java repo 基础镜像
├── docker_entrypoint.sh     # 容器内：启动服务 + 运行测试
├── requirements.txt
└── README.md
```

---

## 镜像设计

**Python 基础镜像**（每个 repo build 一次）：

````dockerfile
FROM python:3.10-slim

# 系统依赖
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /repo

# 先复制 generated repo
COPY ./generated_repo /repo

# 安装 repo 依赖
RUN pip install -r requirements.txt

# 复制 golden oracle 测试（覆盖 agent 生成的 tests/）
COPY ./golden_tests /repo/tests

# 安装测试依赖
RUN pip install pytest httpx requests

COPY docker_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
````

**Java 基础镜像**：

````dockerfile
FROM maven:3.9-eclipse-temurin-17

WORKDIR /repo
COPY ./generated_repo /repo

# 预下载依赖（加速后续 build）
RUN mvn dependency:go-offline -q || true

# 覆盖测试
COPY ./golden_tests/src/test /repo/src/test

COPY docker_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
````

---

## Entrypoint 脚本

````bash
#!/bin/bash
set -e

LANG=${REPO_LANG:-python}  # python or java
SERVICE_PORT=${SERVICE_PORT:-8000}
STARTUP_TIMEOUT=${STARTUP_TIMEOUT:-30}

echo "=== Starting service ==="

if [ "$LANG" = "python" ]; then
    bash start.sh &
    SERVICE_PID=$!
elif [ "$LANG" = "java" ]; then
    mvn spring-boot:run -q &
    SERVICE_PID=$!
fi

# 等待服务就绪
echo "=== Waiting for service on port $SERVICE_PORT ==="
for i in $(seq 1 $STARTUP_TIMEOUT); do
    if curl -sf "http://localhost:$SERVICE_PORT" > /dev/null 2>&1 || \
       curl -sf "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
        echo "Service ready after ${i}s"
        break
    fi
    if [ $i -eq $STARTUP_TIMEOUT ]; then
        echo "SERVICE_START_FAILED"
        exit 1
    fi
    sleep 1
done

echo "=== Running tests ==="

if [ "$LANG" = "python" ]; then
    pytest tests/ -v --tb=short --json-report \
        --json-report-file=/results/pytest_report.json 2>&1
    EXIT_CODE=$?
elif [ "$LANG" = "java" ]; then
    mvn test 2>&1
    EXIT_CODE=$?
fi

kill $SERVICE_PID 2>/dev/null || true
exit $EXIT_CODE
````

---

## 主 Harness 脚本

````python
"""
RepoGenesis Evaluation Harness (Docker-based)
Usage:
    python run_eval.py \
        --generated_dir ./generated_repos \
        --golden_dir ./repo_golden_oracle \
        --output results.json \
        --lang python
"""

import argparse
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Tuple, Optional


def build_image(repo_name: str, generated_repo: Path, golden_tests: Path,
                lang: str, dockerfile: Path) -> Tuple[bool, str]:
    """Build a Docker image for a single repo."""
    image_tag = f"repogenesis-eval-{repo_name}:latest".lower()

    with tempfile.TemporaryDirectory() as ctx:
        ctx_path = Path(ctx)
        shutil.copytree(generated_repo, ctx_path / "generated_repo")
        shutil.copytree(golden_tests, ctx_path / "golden_tests")
        shutil.copy(dockerfile, ctx_path / "Dockerfile")
        shutil.copy(Path(__file__).parent / "docker_entrypoint.sh",
                    ctx_path / "docker_entrypoint.sh")

        cmd = ["docker", "build", "-t", image_tag, str(ctx_path)]
        try:
            result = subprocess.run(
                cmd, timeout=300, capture_output=True, text=True, check=True
            )
            return True, image_tag
        except subprocess.CalledProcessError as e:
            return False, f"Build failed: {e.stderr[-2000:]}"
        except subprocess.TimeoutExpired:
            return False, "Build timed out (300s)"


def run_container(image_tag: str, lang: str,
                  timeout: int = 120) -> Tuple[int, str]:
    """Run the eval container and return (exit_code, logs)."""
    with tempfile.TemporaryDirectory() as results_dir:
        cmd = [
            "docker", "run", "--rm",
            "--network", "bridge",          # 隔离网络
            "--memory", "1g",               # 内存限制
            "-e", f"REPO_LANG={lang}",
            "-v", f"{results_dir}:/results",
            image_tag
        ]
        try:
            result = subprocess.run(
                cmd, timeout=timeout, capture_output=True, text=True
            )
            logs = result.stdout + result.stderr
            return result.returncode, logs
        except subprocess.TimeoutExpired:
            return -1, "Container timed out"


def parse_results(logs: str, lang: str) -> Dict:
    """Parse test results from container logs."""
    passed, failed, errors = 0, 0, 0

    if lang == "python":
        for line in logs.splitlines():
            # pytest summary: "5 passed, 2 failed, 1 error"
            if "passed" in line or "failed" in line:
                import re
                m = re.search(r'(\d+) passed', line)
                if m:
                    passed = int(m.group(1))
                m = re.search(r'(\d+) failed', line)
                if m:
                    failed = int(m.group(1))
                m = re.search(r'(\d+) error', line)
                if m:
                    errors = int(m.group(1))
    elif lang == "java":
        for line in logs.splitlines():
            # Maven: "Tests run: 5, Failures: 0, Errors: 0"
            import re
            m = re.search(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+)', line)
            if m:
                total = int(m.group(1))
                failed = int(m.group(2)) + int(m.group(3))
                passed = total - failed

    total = passed + failed + errors
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": total,
        "pass_at_1": passed / total if total > 0 else 0.0
    }


def evaluate_repo(repo_name: str, generated_dir: Path, golden_dir: Path,
                  lang: str) -> Dict:
    generated_repo = generated_dir / repo_name
    golden_repo = golden_dir / repo_name

    if not generated_repo.exists():
        return {"repo": repo_name, "status": "missing_generated", "pass_at_1": 0.0}
    if not golden_repo.exists():
        return {"repo": repo_name, "status": "missing_golden", "pass_at_1": 0.0}

    dockerfile = Path(__file__).parent / f"Dockerfile.{lang}"
    golden_tests = golden_repo / ("tests" if lang == "python" else "src/test")

    print(f"[{repo_name}] Building image...")
    build_ok, image_or_err = build_image(
        repo_name, generated_repo, golden_tests, lang, dockerfile
    )
    if not build_ok:
        print(f"[{repo_name}] Build failed: {image_or_err}")
        return {"repo": repo_name, "status": "build_failed",
                "error": image_or_err, "pass_at_1": 0.0}

    print(f"[{repo_name}] Running tests...")
    exit_code, logs = run_container(image_or_err, lang)

    metrics = parse_results(logs, lang)
    metrics["repo"] = repo_name
    metrics["status"] = "success" if exit_code == 0 else "test_failed"
    metrics["exit_code"] = exit_code

    # 清理镜像
    subprocess.run(["docker", "rmi", image_or_err], capture_output=True)

    print(f"[{repo_name}] Pass@1: {metrics['pass_at_1']:.2f} "
          f"({metrics['passed']}/{metrics['total']})")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="RepoGenesis Docker Eval Harness")
    parser.add_argument("--generated_dir", type=Path, required=True,
                        help="Directory of generated repos")
    parser.add_argument("--golden_dir", type=Path, required=True,
                        help="Golden oracle directory (repo_golden_oracle)")
    parser.add_argument("--output", type=Path, default=Path("results.json"))
    parser.add_argument("--lang", choices=["python", "java"], default="python")
    parser.add_argument("--repos", nargs="*",
                        help="Specific repo names to eval (default: all)")
    args = parser.parse_args()

    repo_names = (
        args.repos
        if args.repos
        else [d.name for d in args.generated_dir.iterdir() if d.is_dir()]
    )

    all_results = []
    for repo_name in sorted(repo_names):
        result = evaluate_repo(repo_name, args.generated_dir,
                               args.golden_dir, args.lang)
        all_results.append(result)

    # 汇总
    total_repos = len(all_results)
    successful = [r for r in all_results if r.get("total", 0) > 0]
    avg_pass_at_1 = (
        sum(r["pass_at_1"] for r in successful) / len(successful)
        if successful else 0.0
    )

    output = {
        "summary": {
            "total_repos": total_repos,
            "evaluated": len(successful),
            "avg_pass_at_1": avg_pass_at_1,
            "lang": args.lang,
        },
        "results": all_results,
    }

    args.output.write_text(json.dumps(output, indent=2))
    print(f"\n=== Summary ===")
    print(f"Evaluated: {len(successful)}/{total_repos} repos")
    print(f"Avg Pass@1: {avg_pass_at_1:.3f}")
    print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()
````

---

## 用法（一条命令复现）

```bash
# 外部研究者只需要：
git clone <repogenesis_repo>
cd repogenesis

# Python repos
python eval_harness/run_eval.py \
    --generated_dir ./my_generated_repos \
    --golden_dir ./repo_golden_oracle \
    --output results.json \
    --lang python

# Java repos
python eval_harness/run_eval.py \
    --generated_dir ./my_generated_repos_java \
    --golden_dir ./repo_golden_oracle_java \
    --output results_java.json \
    --lang java
```

**唯一前提：装了 Docker**。不需要 conda、JDK、Maven、任何 Python 包。

---

## 与现有代码的关系

- `evaluate_repos.py` / `evaluate_repos_java.py` → **保留**，作为 local 快速调试用
- `run_eval.py` → 新增，作为对外发布的**官方复现入口**
- `Dockerfile.*` → 新增，固定环境快照

这样内部开发继续用 local 脚本快速迭代，外部复现走 Docker，两者并存。