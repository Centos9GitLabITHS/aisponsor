#!/usr/bin/env python3
"""
sponsor_match/data/ingest_associations.py
-----------------------------------------
Read a geocoded associations CSV and load it idempotently into the `clubs` table.
"""

import logging
from argparse import ArgumentParser
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import text
from sponsor_match.core.db import get_engine

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main(csv_path: Path, db_url: str | None) -> None:
    """
    Load the associations CSV into the `clubs` table.
    If the table already has data, it will be truncated first.
    """
    # Build or fall back to config URL
    engine = get_engine(db_url) if db_url else get_engine()

    # Read CSV
    if not csv_path.exists():
        logger.error("CSV file not found at %s", csv_path)
        sys.exit(1)

    logger.info("Reading %s", csv_path)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.exception("Error reading CSV: %s", e)
        sys.exit(1)

    logger.info("Read %d rows from %s", len(df), csv_path)

    # Drop 'id' column if present, since clubs table has its own PK
    if "id" in df.columns:
        logger.info("Dropping 'id' column before insert")
        df = df.drop(columns=["id"])

    # Idempotent load: truncate then append
    try:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE clubs"))
            df.to_sql("clubs", conn, if_exists="append", index=False)
            new_count = conn.execute(text("SELECT COUNT(*) FROM clubs")).scalar() or 0
            logger.info("✅ Associations ingestion complete. Total clubs now: %d", new_count)
    except Exception as e:
        logger.exception("Database error during ingest: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    parser = ArgumentParser(description="Ingest geocoded associations into the clubs table")
    parser.add_argument(
        "--db-url", "-d",
        default=None,
        help="SQLAlchemy URL for your MySQL database (overrides env/config)"
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to geocoded associations CSV"
    )
    args = parser.parse_args()
    main(args.csv_path, args.db_url)
