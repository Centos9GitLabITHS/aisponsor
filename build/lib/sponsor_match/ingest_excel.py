"""
sponsor_match/ingest_excel.py
─────────────────────────────
Loads the Excel file  data/bolag_1_500_sorted_with_year.xlsx
into the MariaDB table  sponsor_registry.companies.

Usage:
    $ python -m sponsor_match.ingest_excel
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from sponsor_match.db import get_engine

# ───────────────────────────────────────────────
# 1. Locate Excel file (relative to project root)
# ───────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]          # …/SponsorMatchAI
EXCEL    = ROOT_DIR / "data" / "bolag_1_500_sorted_with_year.xlsx"

# ───────────────────────────────────────────────
# 2. Read + tidy DataFrame
# ───────────────────────────────────────────────
df = pd.read_excel(EXCEL)

df = df.rename(
    columns={
        "Företagsnamn":     "name",
        "Postadress":       "address",
        "Omsättning (tkr)": "revenue_ksek",
        "Anställda":        "employees",
        "År":               "year",
    }
)

df["rev_per_emp"] = (df["revenue_ksek"] * 1000) / df["employees"].clip(lower=1)

# size bucket by total revenue (adjust thresholds freely)
bins   = [0, 5_000_000, 50_000_000, float("inf")]
labels = ["small", "medium", "large"]
df["size_bucket"] = pd.cut(df["revenue_ksek"] * 1000, bins=bins, labels=labels)

# keep only the columns we’ll insert
df = df[
    ["name", "address", "revenue_ksek",
     "employees", "year", "rev_per_emp", "size_bucket"]
]

# ───────────────────────────────────────────────
# 3. Write to MariaDB
# ───────────────────────────────────────────────
engine = get_engine()

DDL = """
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
)  CHARACTER SET utf8mb4;
"""

with engine.begin() as con:
    con.execute(text(DDL))
    df.to_sql("companies", con, if_exists="append", index=False)

print(f"✅ Imported {len(df):,} rows into sponsor_registry.companies")
