# build_associations_csv.py
"""
Reads a raw associations CSV, geocodes missing latitude/longitude,
and writes an enriched CSV for ingestion.
"""
import argparse  # For parsing CLI arguments
import logging  # For logging progress and warnings
import sqlite3  # Lightweight local cache database
from pathlib import Path  # Filesystem paths

import pandas as pd  # Data handling
import requests  # HTTP requests for geocoding
from dotenv import load_dotenv  # Load environment variables

# Constants for default paths and geocoder
load_dotenv()
DEFAULT_INPUT = Path("data") / "associations_raw.csv"
DEFAULT_OUTPUT = Path("data") / "associations_goteborg_with_coords.csv"
DEFAULT_CACHE_DB = Path(".geo_cache.sqlite3")
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"


def init_logging():
    """Configure logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )


def open_cache(db_path: Path) -> sqlite3.Connection:
    """Open or create a SQLite cache for geocode results."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS geocode_cache (
            address TEXT PRIMARY KEY,
            latitude REAL,
            longitude REAL
        )
    """)
    conn.commit()
    return conn


def geocode(address: str, conn: sqlite3.Connection, api_key: str = None):
    """
    Return (lat, lon) for an address, using cache if available,
    otherwise querying the external geocoding service.
    """
    # Check cache first
    row = conn.execute(
        "SELECT latitude, longitude FROM geocode_cache WHERE address = ?",
        (address,)
    ).fetchone()
    if row:
        return row

    # Make external request if not cached
    try:
        params = {"q": address, "format": "json", "limit": 1}
        if api_key:
            params["key"] = api_key
        resp = requests.get(GEOCODER_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"No results for '{address}'")
        lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logging.warning(f"Geocoding failed for '{address}': {e}")
        return None, None

    # Cache the successful result
    try:
        conn.execute(
            "INSERT OR REPLACE INTO geocode_cache(address, latitude, longitude) VALUES (?, ?, ?)",
            (address, lat, lon)
        )
        conn.commit()
    except Exception as e:
        logging.warning(f"Failed to cache geocode for '{address}': {e}")

    return lat, lon


def main():
    """Main entry point: parse arguments, geocode missing entries, and write output."""
    init_logging()
    parser = argparse.ArgumentParser(description="Build associations CSV with geocoding")
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT, help="Path to raw CSV")
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT, help="Path to enriched CSV")
    parser.add_argument("--cache-db", type=Path, default=DEFAULT_CACHE_DB, help="SQLite cache DB path")
    parser.add_argument("--api-key", type=str, default=None, help="Geocoding API key")
    args = parser.parse_args()

    # Load raw data
    if not args.input_csv.exists():
        logging.error(f"Input CSV not found: {args.input_csv}")
        return
    df = pd.read_csv(args.input_csv)
    logging.info(f"Loaded {len(df)} rows from {args.input_csv}")

    # Identify or create lat/lon columns
    lat_col = next((c for c in df.columns if c.lower() in ("latitude","lat")), None)
    lon_col = next((c for c in df.columns if c.lower() in ("longitude","lon")), None)
    if not lat_col or not lon_col:
        lat_col, lon_col = "latitude","longitude"
        df[lat_col] = pd.NA
        df[lon_col] = pd.NA
    logging.info(f"Using columns: lat={lat_col}, lon={lon_col}")

    # Prepare cache connection
    cache_conn = open_cache(args.cache_db)

    # Geocode entries missing coordinates
    for idx, row in df.iterrows():
        if pd.isna(row[lat_col]) or pd.isna(row[lon_col]):
            address = row.get("address") or row.get("club_name") or ""
            if not address:
                logging.warning(f"No address for row {idx}; skipping")
                continue
            lat, lon = geocode(address, cache_conn, args.api_key)
            if lat is not None:
                df.at[idx, lat_col] = lat
                df.at[idx, lon_col] = lon

    # Write the enriched CSV
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    logging.info(f"Wrote enriched CSV to {args.output_csv}")


if __name__ == "__main__":
    main()
