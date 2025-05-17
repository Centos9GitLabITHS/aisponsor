#!/usr/bin/env python3
"""
utils/list_project_files.py
----------------------
Recursively scans the entire project root (one level up from this script), skips
directories .venv and .venv312 as well as __pycache__ and .git, and writes
out both filenames and entire contents for file types:
.py, .csv, .json, .toml, .md and .yml

Usage:
    cd /home/user/SponsorMatchAI
    python utils/list_project_files.py [--output CUSTOM_PATH]

Output:
    utils_output/project_dump.txt (default)
"""

import argparse
import logging
import os
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

EXCLUDE_DIRS = {'.venv', '.venv312', '__pycache__', '.git'}


def collect_and_dump(root: Path, exts: List[str], out_path: Path) -> None:
    """
    Go through root and all subdirectories, collect files with suffixes in exts,
    skip EXCLUDE_DIRS, and write filepath + content to out_path.
    """
    with out_path.open("w", encoding="utf-8") as f:
        for dirpath, dirnames, filenames in os.walk(root):
            # Exclude unwanted directories
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in sorted(filenames):
                if any(fn.lower().endswith(ext) for ext in exts):
                    file_path = Path(dirpath) / fn
                    f.write("=" * 80 + "\n")
                    f.write(f"FIL: {file_path.relative_to(root)}\n")
                    f.write("=" * 80 + "\n\n")
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        f.write(content)
                    except Exception as e:
                        f.write(f"<Could not read file: {e}>\n")
                    f.write("\n\n")
    size_kb = out_path.stat().st_size / 1024
    logger.info("Created dump file %s (%.1f KB)", out_path, size_kb)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create dump of important project files with full content."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file path (default: utils_output/project_dump.txt)"
    )
    args = parser.parse_args()

    # Since we're now in utils/ directory, need to get the project root (one level up)
    project_root = Path(__file__).parent.parent

    # Create utils_output directory if it doesn't exist
    outputs_dir = project_root / "utils_output"
    outputs_dir.mkdir(exist_ok=True)

    # Set default output path if not specified
    output_path = args.output if args.output else outputs_dir / "project_dump.txt"

    extensions = [".py", ".csv", ".json", ".toml", ".md", ".yml"]
    logger.info("Scanning %s for %s files...", project_root, extensions)
    collect_and_dump(project_root, extensions, output_path)


if __name__ == "__main__":
    main()
