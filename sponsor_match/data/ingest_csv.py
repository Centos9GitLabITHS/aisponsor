#!/usr/bin/env python3
"""
sponsor_match/data/ingest_csv.py
--------------------------------
Loads the CSV file data/bolag_1_500_sorted_with_year.csv
into the MariaDB table sponsor_registry.companies.

Usage:
    python -m sponsor_match.data.ingest_csv
"""

import sys
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sponsor_match.core.db import get_engine

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

def main() -> None:
    """Read, transform, and load company data from CSV into MySQL."""
    # 1. Locate CSV file
    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "data" / "bolag_1_500_sorted_with_year.csv"

    # 2. Read CSV with error handling
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        logger.info("Loaded %d rows from %s", len(df), csv_path)
    except FileNotFoundError:
        logger.error("CSV file not found at %s", csv_path)
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logger.error("CSV file at %s is empty", csv_path)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error reading CSV: %s", e)
        sys.exit(1)

    # 3. Validate expected columns
    expected = {"Företagsnamn", "Postadress", "Omsättning (tkr)", "Anställda", "År"}
    missing = expected - set(df.columns)
    if missing:
        logger.error("Missing required columns: %s. Found: %s", missing, list(df.columns))
        sys.exit(1)

    # 4. Rename and compute fields
    df = df.rename(columns={
        "Företagsnamn":     "name",
        "Postadress":       "address",
        "Omsättning (tkr)": "revenue_ksek",
        "Anställda":        "employees",
        "År":               "year",
    })
    df["rev_per_emp"] = (df["revenue_ksek"] * 1000) / df["employees"].clip(lower=1)

    # 5. Bucket by revenue
    bins = [0, 5_000_000, 50_000_000, float("inf")]
    labels = ["small", "medium", "large"]
    df["size_bucket"] = pd.cut(df["revenue_ksek"] * 1000, bins=bins, labels=labels)

    # 6. Select only columns for insertion
    df = df[["name", "address", "revenue_ksek", "employees", "year", "rev_per_emp", "size_bucket"]]

    # 7. Write to MariaDB
    engine = get_engine()
    ddl = """
    CREATE TABLE IF NOT EXISTS companies (
      comp_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
      name         TEXT,
      address      TEXT,
      revenue_ksek DOUBLE,
      employees    INT,
      year         INT,
      rev_per_emp  DOUBLE,
      size_bucket  ENUM('small','medium','large'),
      industry     TEXT,
      lat          DOUBLE,
      lon          DOUBLE
    ) CHARACTER SET utf8mb4;
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(ddl))
            existing = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar() or 0
            logger.info("companies table contains %d rows", existing)

            df.to_sql("companies", conn, if_exists="append", index=False)
            logger.info("Appended %d rows to companies", len(df))
    except Exception as e:
        logger.exception("Database error during ingest: %s", e)
        sys.exit(1)

    logger.info("✅ Ingestion complete. Total rows now: %d", existing + len(df))


if __name__ == "__main__":
    main()
