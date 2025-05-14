#!/usr/bin/env python3
"""
tools/analyze_text_files.py
---------------------------
Generate a selective project dump including only code files,
and produce a list of excluded large files.

Usage:
    python tools/analyze_text_files.py [--dump-output DUMP_FILE] [--excluded-output EXCLUDED_FILE]
"""
import os
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Set, Tuple

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def create_selective_dump(
    output_file: Path,
    code_extensions: Tuple[str, ...],
    exclude_dirs: Set[str],
    max_file_size: int
) -> None:
    """
    Write a dump of project structure and contents limited to code files under max size.
    """
    included_count = 0
    excluded_count = 0

    with output_file.open("w", encoding="utf-8") as f:
        # 1. Project structure
        f.write("PROJECT STRUCTURE:\n")
        f.write("=" * 50 + "\n\n")
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            level = root.replace(".", "").count(os.sep)
            indent = "  " * level
            dir_name = os.path.basename(root) or Path(root).resolve().name
            f.write(f"{indent}{dir_name}/\n")
            sub_indent = "  " * (level + 1)
            for file in files:
                if file.endswith(code_extensions):
                    f.write(f"{sub_indent}{file}\n")

        # 2. File contents
        f.write("\n\nFILE CONTENTS:\n")
        f.write("=" * 50 + "\n\n")
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith(code_extensions):
                    path = Path(root) / file
                    rel = path.relative_to(Path("."))
                    try:
                        size = path.stat().st_size
                        if size > max_file_size:
                            excluded_count += 1
                            continue
                        f.write("=" * 30 + "\n")
                        f.write(f"FILE: {rel}\n")
                        f.write("=" * 30 + "\n\n")
                        f.write(path.read_text(encoding="utf-8"))
                        included_count += 1
                    except Exception as e:
                        f.write(f"Error reading {rel}: {e}\n")
                    f.write("\n")

    logger.info(
        "Created dump '%s' (included %d files, excluded %d files)",
        output_file, included_count, excluded_count
    )

def list_excluded_files(
    output_file: Path,
    exclude_dirs: Set[str],
    max_size: int,
    report_extensions: Tuple[str, ...]
) -> None:
    """
    Generate a list of non-code files exceeding max_size.
    """
    errors = []
    with output_file.open("w", encoding="utf-8") as f:
        f.write("Large files excluded from dump:\n\n")
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith(report_extensions):
                    path = Path(root) / file
                    try:
                        size = path.stat().st_size
                        if size > max_size:
                            rel = path.relative_to(Path("."))
                            f.write(f"{rel}: {size // 1024}KB\n")
                    except Exception as e:
                        errors.append(f"{path}: {e}")
        if errors:
            f.write("\nErrors:\n")
            for err in errors:
                f.write(f" - {err}\n")
    logger.info("Created excluded-files list '%s'", output_file)

def main() -> None:
    parser = ArgumentParser(
        description="Selective dump of code files and list of excluded large files"
    )
    parser.add_argument(
        "--dump-output", "-d",
        type=Path,
        default=Path("project_dump_selective.txt"),
        help="Filename for the selective dump"
    )
    parser.add_argument(
        "--excluded-output", "-e",
        type=Path,
        default=Path("excluded_files.txt"),
        help="Filename for the excluded-files list"
    )
    parser.add_argument(
        "--max-size", "-m",
        type=int,
        default=500 * 1024,
        help="Maximum file size in bytes to include in the dump"
    )

    args = parser.parse_args()

    code_exts = (".py", ".yml", ".yaml", ".toml", ".cfg", ".ini")
    exclude_dirs = {"venv", ".venv312", "__pycache__", ".git", ".idea", "build", "dist"}
    report_exts = (".json", ".csv", ".txt", ".md")

    create_selective_dump(args.dump_output, code_exts, exclude_dirs, args.max_size)
    list_excluded_files(args.excluded_output, exclude_dirs, args.max_size, report_exts)

if __name__ == "__main__":
    main()
