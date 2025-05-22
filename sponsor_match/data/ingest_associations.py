#!/usr/bin/env python3
"""
sponsor_match/data/ingest_associations.py

Reads an enriched associations CSV and ingests it into the MySQL database.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sponsor_match.core.db import get_engine
from dotenv import load_dotenv

def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

def ingest(csv_path: Path):
    """
    Load the CSV at csv_path into the `associations` table.
    Replaces any existing data in `associations`.
    """
    if not csv_path.exists():
        logging.error(f"CSV file not found: {csv_path}")
        return

    try:
        df = pd.read_csv(csv_path)
        logging.info(f"Loaded {len(df)} rows from {csv_path}")
    except Exception as e:
        logging.error(f"Failed to read CSV {csv_path}: {e}")
        return

    engine = get_engine()
    try:
        with engine.begin() as conn:
            df.to_sql(
                name="associations",
                con=conn,
                if_exists="replace",
                index=False,
                method="multi",      # batch inserts if available
            )
        logging.info(f"Successfully wrote {len(df)} rows to `associations` table.")
    except SQLAlchemyError as e:
        logging.error(f"Database error during ingest: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during ingest: {e}")

def main():
    load_dotenv()    # ensure .env credentials are loaded
    init_logging()

    parser = argparse.ArgumentParser(
        description="Ingest enriched associations CSV into MySQL `associations` table"
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path("data") / "associations_goteborg_with_coords.csv",
        help="Path to the enriched associations CSV file",
    )
    args = parser.parse_args()
    ingest(args.csv_path)

if __name__ == "__main__":
    main()
