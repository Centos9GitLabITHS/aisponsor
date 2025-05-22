#!/usr/bin/env python3
"""
scripts/build_associations_csv.py

Reads a raw associations CSV, geocodes missing latitude/longitude,
and writes an enriched CSV for ingestion.
"""

import argparse
import logging
import sqlite3
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Load .env early so we can pick up any GEOCODING_API_KEY or other vars
load_dotenv()

# Constants
DEFAULT_INPUT = Path("data") / "associations_raw.csv"
DEFAULT_OUTPUT = Path("data") / "associations_goteborg_with_coords.csv"
DEFAULT_CACHE_DB = Path(".geo_cache.sqlite3")

# Adjust this to your geocoding API if using another service
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"


def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )


def open_cache(db_path: Path) -> sqlite3.Connection:
    """Open or create the geocode cache database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS geocode_cache (
            address TEXT PRIMARY KEY,
            latitude REAL,
            longitude REAL
        )
        """
    )
    conn.commit()
    return conn


def geocode(address: str, conn: sqlite3.Connection, api_key: str = None):
    """Return (lat, lon) for address, using cache or external API."""
    # Check cache first
    row = conn.execute(
        "SELECT latitude, longitude FROM geocode_cache WHERE address = ?",
        (address,),
    ).fetchone()
    if row:
        return row

    # Not in cache: call external service
    try:
        params = {"q": address, "format": "json", "limit": 1}
        # If your service requires an API key, add it here
        if api_key:
            params["key"] = api_key
        resp = requests.get(GEOCODER_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"No results for '{address}'")
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
    except Exception as e:
        logging.warning(f"Geocoding failed for '{address}': {e}")
        return None, None

    # Cache the result
    try:
        conn.execute(
            "INSERT OR REPLACE INTO geocode_cache(address, latitude, longitude) VALUES (?, ?, ?)",
            (address, lat, lon),
        )
        conn.commit()
    except Exception as e:
        logging.warning(f"Failed to cache geocode for '{address}': {e}")

    return lat, lon


def main():
    init_logging()
    parser = argparse.ArgumentParser(
        description="Build associations CSV by adding lat/lon via geocoding"
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to raw associations CSV",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write enriched associations CSV",
    )
    parser.add_argument(
        "--cache-db",
        type=Path,
        default=DEFAULT_CACHE_DB,
        help="Path to SQLite cache DB for geocoding results",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Geocoding service API key (if required)",
    )
    args = parser.parse_args()

    # Read raw data
    if not args.input_csv.exists():
        logging.error(f"Input CSV not found: {args.input_csv}")
        return
    df = pd.read_csv(args.input_csv)
    logging.info(f"Loaded {len(df)} rows from {args.input_csv}")

    # Determine coordinate columns
    lat_col = next((c for c in df.columns if c.lower() in ("latitude", "lat")), None)
    lon_col = next((c for c in df.columns if c.lower() in ("longitude", "lon")), None)
    if not lat_col or not lon_col:
        lat_col, lon_col = "latitude", "longitude"
        df[lat_col] = pd.NA
        df[lon_col] = pd.NA
    logging.info(f"Using latitude column '{lat_col}', longitude column '{lon_col}'")

    # Prepare cache
    cache_conn = open_cache(args.cache_db)

    # Geocode missing entries
    for idx, row in df.iterrows():
        if pd.isna(row[lat_col]) or pd.isna(row[lon_col]):
            address = row.get("address") or row.get("club_name") or ""
            if not address:
                logging.warning(f"No address for row {idx}; skipping")
                continue
            lat, lon = geocode(address, cache_conn, api_key=args.api_key)
            if lat is not None and lon is not None:
                df.at[idx, lat_col] = lat
                df.at[idx, lon_col] = lon

    # Write enriched CSV
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    logging.info(f"Wrote enriched CSV to {args.output_csv}")


if __name__ == "__main__":
    main()
