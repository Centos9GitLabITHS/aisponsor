# Utility to list project files and dump their contents
# Detailed comments have been inserted in British English.

#!/usr/bin/env python3
"""
utils/list_project_files.py
----------------------
Recursively scans the entire project root (one level up from this script), skips
directories .venv, .venv312, __pycache__, .git, and archive/old_csv_files/,
and writes out both filenames and entire contents for file types:
.py, .csv, .json, .toml, .md and .yml

Now creates four separate dump files to split the content evenly.

Usage:
    cd /home/user/SponsorMatchAI
    python utils/list_project_files.py [--output-prefix CUSTOM_PREFIX] [--verbose]

Output:
    utils_output/project_dump_part1.txt through utils_output/project_dump_part4.txt (default)
"""

# Standard library or third-party import
import argparse
# Standard library or third-party import
import logging
# Standard library or third-party import
import os
# Standard library or third-party import
from pathlib import Path
# Standard library or third-party import
from typing import List, Set

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Directory names to exclude (checked against directory name only)
EXCLUDE_DIRS = {'.venv', '.venv312', '__pycache__', '.git'}

# Directory paths to exclude (checked against relative path from project root)
EXCLUDE_DIR_PATHS = {'archive/old_csv_files'}

# Specific files to exclude by their relative path
EXCLUDE_FILES = {
    'data/bolag_1_500_sorted_with_year.csv',
    'data/associations_goteborg.csv',
    'data/associations_goteborg_with_coords.csv',
    'data/gothenburg_companies_addresses.csv',
    'data/associations_geocoded.csv',
    'data/companies_geocoded.csv',
    'data/gothenburg_associations.csv',
    'data/municipality_of_goteborg.csv',
    'data/associations_geocoded_prepared.csv',
    'data/companies_geocoded.csv',
    'associations_prepared.csv',
    'data/companies_prepared.csv',
    'data/associations_prepared.csv',
}

# Filenames to exclude regardless of their location
EXCLUDE_FILENAMES = {'bolag_1_500_with_coords.csv'}


# Definition of function 'collect_files': explains purpose and parameters
def collect_files(root: Path, exts: List[str], exclude_files: Set[str], exclude_filenames: Set[str]) -> List[Path]:
    """
    Go through root and all subdirectories, collect files with suffixes in exts,
    skip EXCLUDE_DIRS (by directory name), EXCLUDE_DIR_PATHS (by relative path),
    exclude_files, and exclude_filenames, and return a list of file paths.
    """
    collected_files = []
    excluded_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Get relative path from root
        rel_dirpath = Path(dirpath).relative_to(root)

        # Skip if this directory is in an excluded path
        skip_dir = False
        for exclude_path in EXCLUDE_DIR_PATHS:
            if exclude_path in str(rel_dirpath):
                logger.debug(f"Skipping directory: {rel_dirpath}")
                skip_dir = True
                break

        if skip_dir:
            dirnames[:] = []  # Don't descend into subdirectories
            continue

        # Exclude unwanted directories by name
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for fn in sorted(filenames):
            # Skip files with excluded filenames
            if fn in exclude_filenames:
                logger.debug(f"Excluding file by name: {fn} in {dirpath}")
                excluded_count += 1
                continue

            if any(fn.lower().endswith(ext) for ext in exts):
                file_path = Path(dirpath) / fn
                rel_path = str(file_path.relative_to(root))

                # Skip excluded files by path
                if rel_path in exclude_files:
                    logger.debug(f"Excluding file by path: {rel_path}")
                    excluded_count += 1
                    continue

                collected_files.append(file_path)

    # Log summary of exclusions only
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} files based on exclusion rules")

    return collected_files


# Definition of function 'write_files_to_dump': explains purpose and parameters
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


# Definition of function 'split_into_four_parts': explains purpose and parameters
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


# Definition of function 'main': explains purpose and parameters
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
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed exclusion messages"
    )
    args = parser.parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        # Also set root logger to DEBUG for full verbosity
        logging.getLogger().setLevel(logging.DEBUG)

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


# Entry point check: script execution starts here when run directly
if __name__ == "__main__":
    main()