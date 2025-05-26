# ingest_associations.py
"""
Read an enriched associations CSV and ingest it into the MySQL `associations` table,
replacing any existing data.
"""
import argparse  # CLI parsing
import logging  # Progress logging
from pathlib import Path  # Filesystem paths

import pandas as pd  # Data loading
from dotenv import load_dotenv  # Load environment credentials
from sqlalchemy.exc import SQLAlchemyError  # Database error handling

from sponsor_match.core.db import get_engine  # Obtain SQLAlchemy engine


def init_logging():
    """Configure basic logging settings."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )


def ingest(csv_path: Path):
    """
    Load the CSV at `csv_path` into the `associations` table.
    Uses SQLAlchemy's `to_sql` with `if_exists='replace'`.
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
        # Begin transaction; drop and recreate table content atomically
        with engine.begin() as conn:
            df.to_sql(
                name="associations",
                con=conn,
                if_exists="replace",
                index=False,
                method="multi"  # Batch inserts where supported
            )
        logging.info(f"Successfully wrote {len(df)} rows to `associations` table.")
    except SQLAlchemyError as e:
        logging.error(f"Database error during ingest: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during ingest: {e}")


def main():
    """Entry point: load .env, parse args, and call ingest()."""
    load_dotenv()
    init_logging()
    parser = argparse.ArgumentParser(description="Ingest associations CSV into MySQL")
    parser.add_argument("--csv-path", type=Path, default=Path("data/associations_goteborg_with_coords.csv"))
    args = parser.parse_args()
    ingest(args.csv_path)


if __name__ == "__main__":
    main()
