# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
sponsor_match/data/ingest_companies.py
-----------------------------------------
Read data/bolag_1_500_with_coords.csv (already geocoded) and load into companies table.
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from sponsor_match.core.db import get_engine

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    # Use the already geocoded file
    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "data" / "bolag_1_500_with_coords.csv"

    # Read the geocoded file
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        logger.info("Loaded %d rows from %s", len(df), csv_path)
    except FileNotFoundError:
        logger.error("CSV not found at %s", csv_path)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected read error: %s", e)
        sys.exit(1)

    # Rename columns to match database schema
    df = df.rename(columns={
        "Företagsnamn": "name",
        "Postadress": "address",
        "Omsättning (tkr)": "revenue_ksek",
        "Anställda": "employees",
        "År": "year",
    })

    # Calculate size bucket based on revenue
    def calculate_size_bucket(revenue_ksek):
        if pd.isna(revenue_ksek):
            return "medium"
        revenue_sek = revenue_ksek * 1000
        if revenue_sek < 5_000_000:
            return "small"
        elif revenue_sek < 50_000_000:
            return "medium"
        else:
            return "large"

    df["size_bucket"] = df["revenue_ksek"].apply(calculate_size_bucket)

    # Add default industry and orgnr to match database schema
    df["industry"] = "Other"
    df["orgnr"] = None  # No organization numbers in our data

    # Select final columns matching database schema
    final_columns = ["orgnr", "name", "revenue_ksek", "employees", "year", "size_bucket", "industry", "lat", "lon"]
    df = df[final_columns]

    # Drop rows with missing coordinates
    before_count = len(df)
    df = df.dropna(subset=["lat", "lon"])
    after_count = len(df)
    if before_count > after_count:
        logger.warning("Dropped %d rows with missing coordinates", before_count - after_count)

    # Write to database
    engine = get_engine()

    try:
        with engine.begin() as conn:
            # Clear existing data and insert new
            conn.execute(text("DELETE FROM companies"))
            df.to_sql("companies", conn, if_exists="append", index=False)

            new_count = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar() or 0
            logger.info("✅ Companies ingestion complete. Total rows: %d", new_count)

    except Exception as e:
        logger.exception("DB error during ingest: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()