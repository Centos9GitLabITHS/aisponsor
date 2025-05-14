#!/usr/bin/env python3
"""
tools/convert_all_xlsx_to_csv.py
--------------------------------
Convert all Excel files (.xlsx, .xls) in a directory tree to CSV format.

Features:
  - Handles multiple sheets by creating separate CSV per sheet.
  - Optionally deletes original Excel files after conversion.
Usage:
  python tools/convert_all_xlsx_to_csv.py [directory]
      [--exclude DIR [DIR ...]] [--delete-original] [--yes] [--encoding ENCODING]
"""

import argparse
import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

class ExcelToCSVConverter:
    def __init__(
        self,
        exclude_dirs: Optional[List[str]] = None,
        delete_original: bool = False,
        encoding: str = 'utf-8'
    ) -> None:
        """
        Args:
            exclude_dirs: directories to skip (e.g. ['.git', '__pycache__'])
            delete_original: delete Excel files after conversion
            encoding: encoding for output CSV files
        """
        self.exclude_dirs = exclude_dirs or [
            '.git', '.venv', '.venv312', '__pycache__',
            'node_modules', 'dist', 'build', '.idea'
        ]
        self.delete_original = delete_original
        self.encoding = encoding

        # Statistics
        self.files_found = 0
        self.files_converted = 0
        self.errors: List[str] = []
        self.total_size_before = 0
        self.total_size_after = 0

    def should_skip_directory(self, path: Path) -> bool:
        """Return True if any part of `path` matches an excluded directory."""
        return any(part in self.exclude_dirs for part in path.parts)

    def find_excel_files(self, root: Path) -> List[Path]:
        """Recursively find all .xlsx and .xls files under `root`."""
        excel_files: List[Path] = []
        logger.info("Scanning %s for Excel files…", root)
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            if self.should_skip_directory(current):
                dirnames.clear()  # don't recurse into excluded dirs
                continue
            for fn in filenames:
                if fn.lower().endswith(('.xlsx', '.xls')):
                    file_path = current / fn
                    excel_files.append(file_path)
                    self.total_size_before += file_path.stat().st_size
                    logger.debug("Found Excel: %s", file_path.relative_to(root))
        self.files_found = len(excel_files)
        logger.info("Total Excel files found: %d", self.files_found)
        return excel_files

    def convert_single_file(self, excel_path: Path) -> bool:
        """
        Convert one Excel file to CSV. Returns True on success.
        Creates one CSV if single sheet, otherwise one per sheet.
        """
        try:
            logger.info("Converting %s", excel_path)
            if not excel_path.exists():
                raise FileNotFoundError(f"{excel_path} not found")

            xls = pd.ExcelFile(excel_path)
            sheets = xls.sheet_names

            if len(sheets) == 1:
                df = pd.read_excel(xls, sheets[0])
                csv_path = excel_path.with_suffix('.csv')
                df.to_csv(csv_path, index=False, encoding=self.encoding)
                self.total_size_after += csv_path.stat().st_size
                logger.info("  → %s (%d rows × %d cols)", csv_path.name, len(df), len(df.columns))
            else:
                logger.info("  Multiple sheets: %s", sheets)
                for sheet in sheets:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    csv_name = f"{excel_path.stem}_{sheet}.csv"
                    csv_path = excel_path.parent / csv_name
                    df.to_csv(csv_path, index=False, encoding=self.encoding)
                    self.total_size_after += csv_path.stat().st_size
                    logger.info("    → %s (%d rows × %d cols)", csv_name, len(df), len(df.columns))

            if self.delete_original:
                excel_path.unlink()
                logger.info("  Deleted original: %s", excel_path.name)

            self.files_converted += 1
            return True

        except Exception as e:
            err = f"Failed to convert {excel_path}: {e}"
            self.errors.append(err)
            logger.error(err)
            return False

    def convert_all(self, root: Path, confirm: bool = True) -> None:
        """
        Orchestrate find → convert → summary.
        If `confirm` is True, prompts the user before proceeding.
        """
        excel_files = self.find_excel_files(root)
        if not excel_files:
            logger.warning("No Excel files to convert under %s", root)
            return

        logger.info("About to convert %d file(s)", len(excel_files))
        if self.delete_original:
            logger.warning("Original Excel files will be deleted after conversion")
        if confirm:
            resp = input("Proceed with conversion? (y/n): ").strip().lower()
            if resp != 'y':
                logger.info("Conversion cancelled by user")
                return

        for f in excel_files:
            self.convert_single_file(f)

        self.print_summary()

    def print_summary(self) -> None:
        """Log conversion statistics and space savings."""
        logger.info("Conversion complete: %d/%d files succeeded, %d errors",
                    self.files_converted, self.files_found, len(self.errors))
        if self.total_size_before:
            saved = self.total_size_before - self.total_size_after
            pct = saved / self.total_size_before * 100
            logger.info("Space before: %s, after: %s (%.1f%% saved)",
                        self.format_bytes(self.total_size_before),
                        self.format_bytes(self.total_size_after),
                        pct)
        if self.errors:
            logger.error("Errors encountered:")
            for e in self.errors:
                logger.error("  - %s", e)

    @staticmethod
    def format_bytes(size: int) -> str:
        """Convert `size` in bytes to human-readable string."""
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

def main() -> None:
    """Parse arguments and run the converter."""
    parser = argparse.ArgumentParser(
        description="Convert all Excel files in a directory tree to CSV."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Additional directories to skip"
    )
    parser.add_argument(
        "--delete-original",
        action="store_true",
        help="Delete Excel files after successful conversion"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Do not prompt for confirmation"
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding for output CSV files (default: utf-8)"
    )

    args = parser.parse_args()
    converter = ExcelToCSVConverter(
        exclude_dirs=args.exclude,
        delete_original=args.delete_original,
        encoding=args.encoding
    )
    root_path = Path(args.directory)
    converter.convert_all(root_path, confirm=not args.yes)


if __name__ == "__main__":
    main()
