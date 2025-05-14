#!/usr/bin/env python3
"""
tools/deep_analyze.py
---------------------
Analyze the project directory to report:
  1. File counts and total size by top-level directory
  2. File counts and total size by extension
  3. Suspicious “library” directories with many Python files

Usage:
    python tools/deep_analyze.py [--root DIR] [--top-n N]
"""

import os
import logging
from argparse import ArgumentParser
from pathlib import Path
from collections import defaultdict
from typing import DefaultDict, Tuple

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def analyze_project_structure(
    root_dir: Path,
    code_extensions: Tuple[str, ...],
    lib_indicators: Tuple[str, ...],
    top_n_dirs: int
) -> None:
    """
    Walk `root_dir` and compute:
      - Number and total size of code files per top-level subdirectory
      - Number and total size of code files per file extension
      - Directories indicating embedded libraries/modules
    """
    dir_counts: DefaultDict[str, int] = defaultdict(int)
    ext_counts: DefaultDict[str, int] = defaultdict(int)
    total_size_by_dir: DefaultDict[str, int] = defaultdict(int)
    total_size_by_ext: DefaultDict[str, int] = defaultdict(int)

    logger.info("Starting analysis in %s", root_dir)

    # Traverse and collect stats
    for current, dirs, files in os.walk(root_dir):
        # Determine the top-level directory relative to root_dir
        rel = Path(current).resolve().relative_to(root_dir.resolve())
        top_dir = rel.parts[0] if rel.parts else "."

        for fname in files:
            if not any(fname.endswith(ext) for ext in code_extensions):
                continue
            fpath = Path(current) / fname
            try:
                size = fpath.stat().st_size
            except OSError:
                logger.debug("Could not stat %s", fpath)
                continue

            ext = fpath.suffix
            dir_counts[top_dir] += 1
            ext_counts[ext] += 1
            total_size_by_dir[top_dir] += size
            total_size_by_ext[ext] += size

    # Report top-level directories
    logger.info("Files by top-level directory (showing top %d):", top_n_dirs)
    for dir_name, count in sorted(dir_counts.items(), key=lambda x: x[1], reverse=True)[:top_n_dirs]:
        size_mb = total_size_by_dir[dir_name] / (1024 * 1024)
        logger.info("  %-20s %6d files  %6.1f MB", dir_name, count, size_mb)

    # Report by extension
    logger.info("Files by extension:")
    for ext, count in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True):
        size_mb = total_size_by_ext[ext] / (1024 * 1024)
        logger.info("  %-6s %6d files  %6.1f MB", ext or "<none>", count, size_mb)

    # Identify “suspicious” directories
    logger.info("Suspicious directories (likely vendor/lib code):")
    for current, dirs, files in os.walk(root_dir):
        for indicator in lib_indicators:
            if indicator in current:
                py_files = sum(1 for f in files if f.endswith(".py"))
                if py_files > 10:
                    rel_path = Path(current).resolve().relative_to(root_dir.resolve())
                    logger.info("  %-30s %3d Python files", rel_path, py_files)
                break

def main() -> None:
    parser = ArgumentParser(
        description="Deep analysis of project structure and code distribution"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Project root directory to analyze (default: current directory)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=15,
        help="How many top directories to display by file count"
    )
    args = parser.parse_args()

    code_exts: Tuple[str, ...] = (
        ".py", ".yml", ".yaml", ".toml", ".cfg", ".ini"
    )
    lib_inds: Tuple[str, ...] = (
        "site-packages", "lib", "Lib", "include", "Include",
        "__pycache__", "dist-packages", "node_modules",
        ".eggs", "build", "dist"
    )

    analyze_project_structure(args.root, code_exts, lib_inds, args.top_n)

if __name__ == "__main__":
    main()
