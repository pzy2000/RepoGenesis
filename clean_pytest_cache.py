#!/usr/bin/env python3
"""
Clean all pytest cache directories recursively from a starting directory (default: current working directory).

Removes all directories named ".pytest_cache" under the specified path.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import time
from typing import List


def _handle_remove_readonly(func, path, exc_info):
    """Fallback handler to remove read-only files on Windows/Unix.

    Changes file permissions to writeable and retries the operation.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        # If still failing, propagate the original exception after best-effort
        raise


def find_pytest_caches(start_dir: str) -> List[str]:
    """Find all ".pytest_cache" directories under start_dir recursively."""
    caches: List[str] = []
    for root, dirnames, _ in os.walk(start_dir):
        # Fast check to avoid joining when unnecessary
        if ".pytest_cache" in dirnames:
            caches.append(os.path.join(root, ".pytest_cache"))
    return caches


def remove_directories(directories: List[str]) -> int:
    """Remove the given directories. Returns the number successfully removed."""
    removed = 0
    for directory in directories:
        if not os.path.exists(directory):
            continue
        try:
            shutil.rmtree(directory, onerror=_handle_remove_readonly)
            removed += 1
        except Exception as exc:
            print(f"Failed to remove: {directory}\n  Reason: {exc}", file=sys.stderr)
    return removed


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively delete all '.pytest_cache' directories under the given path."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=os.getcwd(),
        help="Starting directory (default: current working directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list caches that would be removed without deleting them.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    start_time = time.time()
    start_dir = os.path.abspath(args.path)

    if not os.path.isdir(start_dir):
        print(f"Error: '{start_dir}' is not a directory", file=sys.stderr)
        return 2

    caches = find_pytest_caches(start_dir)

    if args.dry_run:
        print("[DRY-RUN] .pytest_cache directories found:")
        for c in caches:
            print(c)
        print(f"[DRY-RUN] Total: {len(caches)}")
        return 0

    removed = remove_directories(caches)
    elapsed = time.time() - start_time

    print(f"Found: {len(caches)} .pytest_cache directories")
    print(f"Removed: {removed}")
    print(f"Elapsed: {elapsed:.2f}s")
    return 0 if removed == len(caches) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


