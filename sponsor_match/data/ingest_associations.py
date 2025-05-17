#!/usr/bin/env python3
"""
sponsor_match/data/ingest_associations.py
-----------------------------------------
Read a geocoded associations CSV and append into the `clubs` table.
"""

import logging
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main(csv_path: Path, db_url: str | None) -> None:
    # Determine DB URL (fallback to env if not passed)
    url = db_url or None
    if not url:
        logger.error("No database URL provided. Use --db-url or set MYSQL_URL_OVERRIDE.")
        raise SystemExit(1)

    engine = create_engine(url)

    # Read CSV
    logger.info("Reading %s", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("Read %d rows from %s", len(df), csv_path)

    # We're inserting into `clubs`, not `companies`
    table_name = "clubs"

    # Drop `id` if present; the clubs table has its own AUTO_INCREMENT primary key
    if "id" in df.columns:
        logger.info("Dropping 'id' column before insert into %s", table_name)
        df = df.drop(columns=["id"])

    # Write to clubs
    logger.info("Writing %d rows into `%s`", len(df), table_name)
    df.to_sql(table_name, engine, if_exists="append", index=False)

if __name__ == "__main__":
    p = ArgumentParser(description="Ingest geocoded associations into DB")
    p.add_argument(
        "--db-url", "-d", default="",
        help="SQLAlchemy URL for your MySQL database"
    )
    p.add_argument(
        "csv_path",
        type=Path,
        help="Path to geocoded associations CSV"
    )
    args = p.parse_args()
    main(args.csv_path, args.db_url)
