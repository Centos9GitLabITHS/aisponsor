#!/usr/bin/env python3
"""
sponsor_match/data/ingest_csv.py
--------------------------------
Read data/bolag_1_500_sorted_with_year.csv, geocode each company,
and load it idempotently into sponsor_registry.companies.

Usage:
    python -m sponsor_match.data.ingest_csv
"""

import sys
import logging
from pathlib import Path

import pandas as pd
from geopy.exc import GeocoderServiceError, GeopyError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from sqlalchemy import text

from sponsor_match.core.db import get_engine

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def try_geocode(address: str, geocode: RateLimiter) -> tuple[float|None, float|None]:
    """Geocode with a few fallbacks; return (lat, lon) or (None, None)."""
    variants = [
        address,
        f"{address}, Sweden",
        address.replace("Västra Frölunda", "Göteborg"),
    ]
    for q in variants:
        if not q:
            continue
        try:
            loc = geocode(q, country_codes="se", exactly_one=True)
        except (GeocoderServiceError, GeopyError):
            continue
        if loc:
            return loc.latitude, loc.longitude
    return None, None

def main() -> None:
    # 1) locate CSV
    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "data" / "bolag_1_500_sorted_with_year.csv"

    # 2) read
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        logger.info("Loaded %d rows from %s", len(df), csv_path)
    except FileNotFoundError:
        logger.error("CSV not found at %s", csv_path)
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logger.error("CSV at %s is empty", csv_path)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected read error: %s", e)
        sys.exit(1)

    # 3) validate columns
    expected = {"Företagsnamn","Postadress","Omsättning (tkr)","Anställda","År"}
    missing = expected - set(df.columns)
    if missing:
        logger.error("Missing columns %s; found %s", missing, df.columns.tolist())
        sys.exit(1)

    # 4) rename & compute bucket
    df = df.rename(columns={
        "Företagsnamn":"name",
        "Postadress":"address",
        "Omsättning (tkr)":"revenue_ksek",
        "Anställda":"employees",
        "År":"year",
    })
    bins = [0,5_000_000,50_000_000,float("inf")]
    labels = ["small","medium","large"]
    df["size_bucket"] = pd.cut(df["revenue_ksek"]*1000, bins=bins, labels=labels)

    # 5) geocode
    geo = Nominatim(user_agent="sponsor_match_geo", timeout=10)
    geocode = RateLimiter(geo.geocode, min_delay_seconds=1.0)
    df["lat"], df["lon"] = zip(*df["address"].apply(lambda a: try_geocode(a, geocode)))  # :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
    failed = df["lat"].isna().sum()
    if failed:
        logger.warning("Geocoding failed for %d/%d companies; distances will be ∞", failed, len(df))

    # 6) select final columns
    df = df[["name","address","revenue_ksek","employees","year","size_bucket","lat","lon"]]

    # 7) write to DB (idempotent)
    engine = get_engine()
    ddl = """
    CREATE TABLE IF NOT EXISTS companies (
      id            BIGINT AUTO_INCREMENT PRIMARY KEY,
      name          TEXT,
      address       TEXT,
      revenue_ksek  DOUBLE,
      employees     INT,
      year          INT,
      size_bucket   ENUM('small','medium','large'),
      industry      TEXT,
      lat           DOUBLE,
      lon           DOUBLE
    ) CHARACTER SET utf8mb4;
    """

    try:
        with engine.begin() as conn:
            # force the correct schema (drops any old table & recreates with lat/lon)
            conn.execute(text("DROP TABLE IF EXISTS companies"))
            conn.execute(text(ddl))
            # load all rows in one go
            df.to_sql("companies", conn, if_exists="append", index=False)
            new_count = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar() or 0
            logger.info("✅ Ingestion complete. Total rows now: %d", new_count)
    except Exception as e:
        logger.exception("DB error during ingest: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
