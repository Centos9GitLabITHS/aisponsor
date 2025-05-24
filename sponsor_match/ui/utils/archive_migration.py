#!/usr/bin/env python3
"""
utils/archive_migration.py

Complete script for identifying and archiving obsolete files from the SponsorMatch AI project.
This script safely moves outdated files to the archive folder while maintaining a detailed
audit trail and allowing for rollback if needed.
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = PROJECT_ROOT / "archive"

# Archive configuration
ARCHIVE_CONFIG = {
    "version": "2.0",
    "date_format": "%Y%m%d_%H%M%S",
    "manifest_filename": "archive_manifest.json",
    "rollback_filename": "rollback_manifest.json",
    "dry_run_by_default": True
}


class FileArchiver:
    """
    Manages the archiving of obsolete project files with safety checks and rollback capability.
    """

    def __init__(self, dry_run: bool = True):
        """
        Initialize the archiver.

        Args:
            dry_run: If True, only simulate the archiving without moving files
        """
        self.dry_run = dry_run
        self.timestamp = datetime.now().strftime(ARCHIVE_CONFIG["date_format"])
        self.archive_dir = ARCHIVE_ROOT / f"archive_{self.timestamp}"
        self.manifest_path = self.archive_dir / ARCHIVE_CONFIG["manifest_filename"]
        self.rollback_path = self.archive_dir / ARCHIVE_CONFIG["rollback_filename"]

        # Track operations
        self.operations = []
        self.errors = []

    def get_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file for integrity verification."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def identify_obsolete_files(self) -> List[Dict[str, any]]:
        """
        Identify files that should be archived based on various criteria.

        Returns:
            List of dictionaries containing file information and archiving reason
        """
        obsolete_files = []

        # Pattern-based identification
        patterns_to_archive = [
            # Old data ingestion scripts (replaced by geocoded CSV pipeline)
            {
                "pattern": "**/ingest_*.py",
                "exclude": ["ingest_associations_fixed.py", "ingest_companies.py"],  # Keep these
                "reason": "Replaced by geocoded CSV pipeline"
            },
            {
                "pattern": "**/manual_geocoding*.py",
                "reason": "Geocoding now handled by pre-processed CSVs"
            },
            {
                "pattern": "**/*_old.py",
                "reason": "Explicitly marked as old"
            },
            {
                "pattern": "**/*_backup.py",
                "reason": "Backup file"
            },
            {
                "pattern": "**/*_test.py",
                "exclude": ["test_*.py"],  # Keep proper test files
                "reason": "Temporary test file"
            },
            {
                "pattern": "**/*_v1.py",
                "reason": "Version 1 file superseded"
            },
            {
                "pattern": "**/temp_*.py",
                "reason": "Temporary file"
            },
            {
                "pattern": "**/examine.py",
                "reason": "Ad-hoc examination script"
            }
        ]

        # Check each pattern
        for pattern_config in patterns_to_archive:
            pattern = pattern_config["pattern"]
            exclude = pattern_config.get("exclude", [])
            reason = pattern_config["reason"]

            for filepath in PROJECT_ROOT.glob(pattern):
                # Skip if already in archive
                if "archive" in filepath.parts:
                    continue

                # Skip if in exclude list
                if any(exc in filepath.name for exc in exclude):
                    continue

                # Skip __pycache__ directories
                if "__pycache__" in filepath.parts:
                    continue

                obsolete_files.append({
                    "path": filepath,
                    "relative_path": filepath.relative_to(PROJECT_ROOT),
                    "reason": reason,
                    "size": filepath.stat().st_size,
                    "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                    "hash": self.get_file_hash(filepath) if filepath.is_file() else None
                })

        # Content-based identification
        obsolete_files.extend(self._identify_by_content())

        # Deduplicate
        seen = set()
        unique_files = []
        for file_info in obsolete_files:
            path_str = str(file_info["path"])
            if path_str not in seen:
                seen.add(path_str)
                unique_files.append(file_info)

        return unique_files

    def _identify_by_content(self) -> List[Dict[str, any]]:
        """
        Identify obsolete files by examining their content.

        Looks for deprecated imports, hardcoded paths, and other indicators.
        """
        content_based_obsolete = []

        # Patterns that indicate obsolescence
        obsolete_indicators = [
            ("from sklearn.cross_validation import", "Uses deprecated sklearn API"),
            ("import MySQLdb", "Uses deprecated MySQL driver"),
            ("/old_data/", "References old data directory"),
            ("/home/user/old_project/", "Contains hardcoded old project paths"),
            ("# DEPRECATED", "Marked as deprecated in comments"),
            ("# TODO: Remove this file", "Marked for removal in comments")
        ]

        # Check Python files
        for py_file in PROJECT_ROOT.glob("**/*.py"):
            # Skip if already in archive or __pycache__
            if "archive" in py_file.parts or "__pycache__" in py_file.parts:
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern, reason in obsolete_indicators:
                    if pattern in content:
                        content_based_obsolete.append({
                            "path": py_file,
                            "relative_path": py_file.relative_to(PROJECT_ROOT),
                            "reason": reason,
                            "size": py_file.stat().st_size,
                            "modified": datetime.fromtimestamp(py_file.stat().st_mtime).isoformat(),
                            "hash": self.get_file_hash(py_file)
                        })
                        break  # One reason is enough

            except Exception as e:
                logger.warning(f"Could not examine {py_file}: {e}")

        return content_based_obsolete

    def create_archive_structure(self):
        """Create the archive directory structure."""
        if not self.dry_run:
            self.archive_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories to maintain organization
            subdirs = ["data", "models", "scripts", "ui", "misc"]
            for subdir in subdirs:
                (self.archive_dir / subdir).mkdir(exist_ok=True)

    def categorize_file(self, relative_path: Path) -> str:
        """Determine which archive subdirectory a file belongs to."""
        path_str = str(relative_path).lower()

        if "data" in path_str or "ingest" in path_str or "csv" in path_str:
            return "data"
        elif "model" in path_str or "clustering" in path_str or "ml" in path_str:
            return "models"
        elif "ui" in path_str or "page" in path_str or "app" in path_str:
            return "ui"
        elif any(script in path_str for script in ["train", "test", "check", "build"]):
            return "scripts"
        else:
            return "misc"

    def archive_file(self, file_info: Dict[str, any]) -> Optional[Dict[str, any]]:
        """
        Archive a single file.

        Args:
            file_info: Dictionary with file information

        Returns:
            Operation record or None if failed
        """
        source_path = file_info["path"]
        relative_path = file_info["relative_path"]

        # Determine archive location
        category = self.categorize_file(relative_path)
        archive_path = self.archive_dir / category / relative_path.name

        # Ensure unique filename if collision
        if archive_path.exists():
            stem = archive_path.stem
            suffix = archive_path.suffix
            counter = 1
            while archive_path.exists():
                archive_path = archive_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1

        operation = {
            "timestamp": datetime.now().isoformat(),
            "source": str(source_path),
            "destination": str(archive_path),
            "relative_path": str(relative_path),
            "category": category,
            "reason": file_info["reason"],
            "file_size": file_info["size"],
            "file_hash": file_info["hash"],
            "dry_run": self.dry_run
        }

        try:
            if not self.dry_run:
                # Create parent directory
                archive_path.parent.mkdir(parents=True, exist_ok=True)

                # Move the file
                shutil.move(str(source_path), str(archive_path))

                # Verify the move
                if archive_path.exists() and not source_path.exists():
                    # Verify integrity
                    if file_info["hash"] and self.get_file_hash(archive_path) == file_info["hash"]:
                        operation["status"] = "success"
                        operation["verified"] = True
                    else:
                        operation["status"] = "success_unverified"
                        operation["verified"] = False
                else:
                    operation["status"] = "failed"
                    operation["error"] = "File not properly moved"
            else:
                operation["status"] = "simulated"

            self.operations.append(operation)
            return operation

        except Exception as e:
            operation["status"] = "error"
            operation["error"] = str(e)
            self.errors.append(operation)
            logger.error(f"Failed to archive {source_path}: {e}")
            return None

    def generate_manifest(self) -> Dict[str, any]:
        """Generate a comprehensive manifest of the archiving operation."""
        manifest = {
            "version": ARCHIVE_CONFIG["version"],
            "timestamp": self.timestamp,
            "dry_run": self.dry_run,
            "summary": {
                "total_files": len(self.operations),
                "successful": len([op for op in self.operations if op.get("status") == "success"]),
                "failed": len([op for op in self.operations if op.get("status") == "failed"]),
                "errors": len(self.errors),
                "total_size": sum(op.get("file_size", 0) for op in self.operations)
            },
            "operations": self.operations,
            "errors": self.errors,
            "categories": {}
        }

        # Group by category
        for op in self.operations:
            category = op.get("category", "misc")
            if category not in manifest["categories"]:
                manifest["categories"][category] = []
            manifest["categories"][category].append(op["relative_path"])

        return manifest

    def save_manifest(self, manifest: Dict[str, any]):
        """Save the manifest to disk."""
        if not self.dry_run:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Manifest saved to {self.manifest_path}")

    def generate_rollback_script(self):
        """Generate a script to reverse the archiving operation."""
        rollback_script = f"""#!/usr/bin/env python3
# Auto-generated rollback script for archive_{self.timestamp}
# Generated on {datetime.now().isoformat()}

import shutil
import json
from pathlib import Path

def rollback():
    manifest_path = Path("{self.manifest_path}")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    successful_rollbacks = 0
    failed_rollbacks = 0

    for operation in manifest["operations"]:
        if operation["status"] == "success":
            source = Path(operation["destination"])
            destination = Path(operation["source"])

            try:
                if source.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(destination))
                    print(f"Restored: {{destination}}")
                    successful_rollbacks += 1
                else:
                    print(f"Warning: {{source}} not found")
            except Exception as e:
                print(f"Failed to restore {{destination}}: {{e}}")
                failed_rollbacks += 1

    print(f"\\nRollback complete: {{successful_rollbacks}} restored, {{failed_rollbacks}} failed")

if __name__ == "__main__":
    rollback()
"""

        if not self.dry_run:
            with open(self.rollback_path, 'w') as f:
                f.write(rollback_script)

            # Make executable
            os.chmod(self.rollback_path, 0o755)
            logger.info(f"Rollback script saved to {self.rollback_path}")

    def print_summary(self, obsolete_files: List[Dict[str, any]]):
        """Print a summary of files to be archived."""
        print("\n" + "=" * 60)
        print("ARCHIVE MIGRATION SUMMARY")
        print("=" * 60)

        # Group by reason
        by_reason = {}
        for file_info in obsolete_files:
            reason = file_info["reason"]
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(file_info)

        # Print each group
        for reason, files in by_reason.items():
            print(f"\n{reason}:")
            print("-" * len(reason))

            for file_info in sorted(files, key=lambda x: x["relative_path"]):
                size_kb = file_info["size"] / 1024
                print(f"  • {file_info['relative_path']} ({size_kb:.1f} KB)")

        # Total statistics
        total_size = sum(f["size"] for f in obsolete_files)
        print(f"\nTotal files to archive: {len(obsolete_files)}")
        print(f"Total size: {total_size / 1024 / 1024:.2f} MB")

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No files will be moved")
        else:
            print("\n⚠️  FILES WILL BE MOVED - Make sure you have backups!")

        print("=" * 60 + "\n")

    def run(self) -> bool:
        """
        Execute the archiving process.

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting archive migration (dry_run={self.dry_run})")

        # Identify obsolete files
        obsolete_files = self.identify_obsolete_files()

        if not obsolete_files:
            logger.info("No obsolete files found")
            return True

        # Print summary
        self.print_summary(obsolete_files)

        # Ask for confirmation if not dry run
        if not self.dry_run:
            response = input("\nProceed with archiving? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Archiving cancelled by user")
                return False

        # Create archive structure
        self.create_archive_structure()

        # Archive each file
        logger.info(f"Archiving {len(obsolete_files)} files...")

        for i, file_info in enumerate(obsolete_files, 1):
            logger.info(f"[{i}/{len(obsolete_files)}] Archiving {file_info['relative_path']}")
            self.archive_file(file_info)

        # Generate and save manifest
        manifest = self.generate_manifest()
        self.save_manifest(manifest)

        # Generate rollback script
        self.generate_rollback_script()

        # Print final summary
        print("\n" + "=" * 60)
        print("ARCHIVE MIGRATION COMPLETE")
        print("=" * 60)

        if self.dry_run:
            print("\nDRY RUN SUMMARY:")
            print(f"  • Would archive {len(self.operations)} files")
            print(f"  • Total size: {manifest['summary']['total_size'] / 1024 / 1024:.2f} MB")
            print(f"  • Archive location: {self.archive_dir}")
        else:
            print(f"\nSUMMARY:")
            print(f"  • Archived {manifest['summary']['successful']} files successfully")
            print(f"  • Failed: {manifest['summary']['failed']}")
            print(f"  • Errors: {manifest['summary']['errors']}")
            print(f"  • Archive location: {self.archive_dir}")
            print(f"  • Manifest: {self.manifest_path}")
            print(f"  • Rollback script: {self.rollback_path}")

        return len(self.errors) == 0


def main():
    """Main entry point for the archive migration script."""
    parser = argparse.ArgumentParser(
        description="Archive obsolete files from the SponsorMatch AI project"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually move files (default is dry-run)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create archiver instance
    archiver = FileArchiver(dry_run=not args.execute)

    # Run the archiving process
    success = archiver.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import sys

    main()
