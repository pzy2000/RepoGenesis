#!/usr/bin/env python3
"""
Blog CMS API 测试运行脚本

提供便捷的测试运行方式
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_pattern=None, verbose=False, coverage=False, parallel=False):
    """运行测试"""
    
    # 构建pytest命令
    cmd = ["python", "-m", "pytest"]
    
    # 添加测试文件或模式
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append("test_blog_api.py")
    
    # 添加选项
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # 添加其他有用选项
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
        "--color=yes",
        "--durations=10"
    ])
    
    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 50)
    
    # 运行测试
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1


def check_dependencies():
    """检查依赖是否安装"""
    required_packages = ["pytest", "requests"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Blog CMS API 测试运行器")
    parser.add_argument("--pattern", "-p", help="测试模式 (e.g., test_01_*)")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--coverage", "-c", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--parallel", "-n", action="store_true", help="并行运行测试")
    parser.add_argument("--check-deps", action="store_true", help="检查依赖")
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("所有依赖已安装")
            return 0
        else:
            return 1
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 运行测试
    return run_tests(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel
    )


if __name__ == "__main__":
    sys.exit(main())