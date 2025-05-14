#!/usr/bin/env python3
"""
tools/create_simple_dump.py
---------------------------
Generate a simple project dump listing and embedding all Python source files
from specified directories.

Usage:
    python tools/create_simple_dump.py [--targets DIR [DIR ...]] [--output OUTPUT]

Defaults:
    targets: sponsor_match, scripts, app, .
    output : project_dump_simple.txt
"""

import argparse
import logging
import os
from pathlib import Path
from typing import List

# Configure structured logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def collect_python_files(directories: List[Path]) -> List[Path]:
    """
    Walk each directory in `directories`, skipping __pycache__,
    and return a list of all .py file paths.
    """
    py_files: List[Path] = []
    for d in directories:
        if not d.exists():
            logger.warning("Skipping missing target directory: %s", d)
            continue

        if d.is_file() and d.suffix == ".py":
            py_files.append(d)
            continue

        for root, dirs, files in os.walk(d):
            # Skip __pycache__ directories
            dirs[:] = [dn for dn in dirs if dn != "__pycache__"]
            for fn in files:
                if fn.endswith(".py"):
                    py_files.append(Path(root) / fn)

    logger.info("Collected %d Python files", len(py_files))
    return py_files

def write_dump(files: List[Path], out_path: Path) -> None:
    """
    Write the header, file listing, and file contents to `out_path`.
    """
    header = "SPONSORMATCHAI PROJECT DUMP\n" + "="*50 + "\n\n"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(header)

        # File listing
        f.write("FILES INCLUDED:\n" + "-"*40 + "\n")
        for p in files:
            f.write(f"{p}\n")
        f.write("\n")

        # File contents
        for p in files:
            f.write("="*40 + "\n")
            f.write(f"FILE: {p}\n")
            f.write("="*40 + "\n\n")
            try:
                content = p.read_text(encoding="utf-8")
                f.write(content)
            except Exception as e:
                f.write(f"<Error reading file: {e}>\n")
            f.write("\n\n")

    size_kb = out_path.stat().st_size / 1024
    logger.info("Created %s (%.1f KB)", out_path, size_kb)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a simple dump of Python source files."
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        type=Path,
        default=[Path(p) for p in ("sponsor_match", "scripts", "app", ".")],
        help="Directories (or files) to include"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("project_dump_simple.txt"),
        help="Output dump filename"
    )
    args = parser.parse_args()

    python_files = collect_python_files(args.targets)
    write_dump(python_files, args.output)

if __name__ == "__main__":
    main()
