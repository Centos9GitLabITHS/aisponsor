#!/usr/bin/env python3
"""
sponsor_match/data/ingest_associations.py
-----------------------------------------
Load an associations CSV (with lat/lon) into the `companies` table.
"""

import logging
from argparse import ArgumentParser
from sqlalchemy import create_engine
import pandas as pd

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main(csv_path: str, db_url: str) -> None:
    logger.info("Reading %s", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("Read %d rows from %s", len(df), csv_path)

    engine = create_engine(db_url)
    # Inspect existing
    with engine.connect() as conn:
        existing = pd.read_sql("SELECT COUNT(*) AS cnt FROM companies", conn)
        total_before = int(existing["cnt"].iloc[0])
    logger.info("companies table contains %d rows before", total_before)

    # Append new rows
    df.to_sql("companies", engine, if_exists="append", index=False)

    # Count again
    with engine.connect() as conn:
        existing = pd.read_sql("SELECT COUNT(*) AS cnt FROM companies", conn)
        total_after = int(existing["cnt"].iloc[0])
    appended = total_after - total_before
    logger.info("Appended %d rows to companies (now %d total)", appended, total_after)


if __name__ == "__main__":
    p = ArgumentParser(description="Ingest associations CSV → companies table")
    # allow both --csv-path and positional csv_path
    p.add_argument(
        "--csv-path", "-c",
        dest="csv_path",
        help="Path to associations CSV (with lat/lon)",
    )
    p.add_argument(
        "csv_path_pos", nargs="?",
        help="(legacy) Path to associations CSV",
    )
    p.add_argument(
        "--db-url", "-d",
        dest="db_url",
        required=True,
        help="SQLAlchemy database URL",
    )
    args = p.parse_args()

    csv = args.csv_path or args.csv_path_pos
    if not csv:
        p.error("You must supply --csv-path or positional csv_path")
    main(csv, args.db_url)
