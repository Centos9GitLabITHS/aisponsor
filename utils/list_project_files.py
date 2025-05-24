#!/usr/bin/env python3
"""
utils/list_project_files.py
----------------------
Recursively scans the entire project root (one level up from this script), skips
directories .venv and .venv312 as well as __pycache__ and .git, and writes
out both filenames and entire contents for file types:
.py, .csv, .json, .toml, .md and .yml

Now creates four separate dump files to split the content evenly.

Usage:
    cd /home/user/SponsorMatchAI
    python utils/list_project_files.py [--output-prefix CUSTOM_PREFIX]

Output:
    utils_output/project_dump_part1.txt through utils_output/project_dump_part4.txt (default)
"""

import argparse
import logging
import os
from pathlib import Path
from typing import List, Set

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

EXCLUDE_DIRS = {'.venv', '.venv312', '__pycache__', '.git'}
EXCLUDE_FILES = {
    'data/bolag_1_500_sorted_with_year.csv',
    'data/associations_goteborg.csv',
    'data/associations_goteborg_with_coords.csv',
    'data/gothenburg_companies_addresses.csv',
    'data/associations_geocoded.csv',
    'data/companies_geocoded.csv',
    'data/gothenburg_associations.csv',
    'data/municipality_of_goteborg.csv'
}
EXCLUDE_FILENAMES = {'bolag_1_500_with_coords.csv'}


def collect_files(root: Path, exts: List[str], exclude_files: Set[str], exclude_filenames: Set[str]) -> List[Path]:
    """
    Go through root and all subdirectories, collect files with suffixes in exts,
    skip EXCLUDE_DIRS, exclude_files, and exclude_filenames, and return a list of file paths.
    """
    collected_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude unwanted directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in sorted(filenames):
            # Skip files with excluded filenames
            if fn in exclude_filenames:
                logger.info(f"Excluding file by name: {fn} in {dirpath}")
                continue

            if any(fn.lower().endswith(ext) for ext in exts):
                file_path = Path(dirpath) / fn
                rel_path = str(file_path.relative_to(root))

                # Skip excluded files by path
                if rel_path in exclude_files:
                    logger.info(f"Excluding file by path: {rel_path}")
                    continue

                collected_files.append(file_path)
    return collected_files


def write_files_to_dump(files: List[Path], root: Path, out_path: Path) -> None:
    """
    Write the given files to the output dump file.
    """
    with out_path.open("w", encoding="utf-8") as f:
        for file_path in files:
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


def split_into_four_parts(files: List[Path]) -> List[List[Path]]:
    """
    Split the list of files into four approximately equal parts.
    """
    file_count = len(files)
    quarter = file_count // 4

    # Handle case where file count doesn't divide evenly by 4
    # by distributing remainder to first parts
    remainder = file_count % 4

    # Calculate lengths for each part
    lengths = [quarter + (1 if i < remainder else 0) for i in range(4)]

    # Create the parts
    result = []
    start_idx = 0
    for length in lengths:
        end_idx = start_idx + length
        result.append(files[start_idx:end_idx])
        start_idx = end_idx

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create four dump files of important project files with full content."
    )
    parser.add_argument(
        "--output-prefix", "-o",
        type=str,
        default=None,
        help="Output file prefix (default: utils_output/project_dump)"
    )
    args = parser.parse_args()

    # Since we're now in utils/ directory, need to get the project root (one level up)
    project_root = Path(__file__).parent.parent

    # Create utils_output directory if it doesn't exist
    outputs_dir = project_root / "utils_output"
    outputs_dir.mkdir(exist_ok=True)

    # Set default output prefix if not specified
    output_prefix = args.output_prefix if args.output_prefix else outputs_dir / "project_dump"

    extensions = [".py", ".csv", ".json", ".toml", ".md", ".yml"]
    logger.info("Scanning %s for %s files...", project_root, extensions)

    # Collect all relevant files, excluding specific files
    all_files = collect_files(project_root, extensions, EXCLUDE_FILES, EXCLUDE_FILENAMES)
    logger.info("Found %d files to include in dumps", len(all_files))

    # Split files into four groups
    file_parts = split_into_four_parts(all_files)

    # Write each group to a separate dump file
    for i, files_part in enumerate(file_parts, 1):
        output_path = Path(f"{output_prefix}_part{i}.txt")
        write_files_to_dump(files_part, project_root, output_path)
        logger.info("Part %d contains %d files", i, len(files_part))

    logger.info("Created four dump files with prefix: %s", output_prefix)


if __name__ == "__main__":
    main()
