#!/usr/bin/env python3
"""
sponsor_match/data/ingest_associations.py
-----------------------------------------
Loads a CSV file of club associations (with lat/lon) into the MySQL `clubs` table.

Usage:
    python -m sponsor_match.data.ingest_associations --csv-path data/associations_goteborg_with_coords.csv
"""

import sys
import logging
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sponsor_match.core.db import get_engine

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

def main(csv_path: Path) -> None:
    """
    Read club data from a CSV and load into the `clubs` table in the database.
    """
    # 1. Read CSV
    try:
        df = pd.read_csv(csv_path)
        logger.info("Loaded %d rows from %s", len(df), csv_path)
    except FileNotFoundError:
        logger.error("CSV file not found at %s", csv_path)
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logger.error("CSV file at %s is empty", csv_path)
        sys.exit(1)
    except Exception as e:
        logger.exception("Error reading CSV: %s", e)
        sys.exit(1)

    # 2. Define DDL for `clubs` table
    ddl = """
    CREATE TABLE IF NOT EXISTS clubs (
        id           INT PRIMARY KEY AUTO_INCREMENT,
        name         VARCHAR(200),
        member_count INT,
        address      TEXT,
        size_bucket  ENUM('small','medium','large'),
        lat          DOUBLE,
        lon          DOUBLE
    ) CHARACTER SET utf8mb4;
    """

    # 3. Write to database
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(text(ddl))
            # Overwrite the table with the new data
            df.to_sql("clubs", conn, if_exists="replace", index=False)
            logger.info("Wrote %d rows to `clubs` table", len(df))
    except Exception as e:
        logger.exception("Database error: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    parser = ArgumentParser(description="Load club CSV into the `clubs` table")
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "associations_goteborg_with_coords.csv",
        help="Path to the club associations CSV file"
    )
    args = parser.parse_args()
    main(args.csv_path)
