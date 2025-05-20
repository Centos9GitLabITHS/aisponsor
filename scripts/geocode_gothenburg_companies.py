#!/usr/bin/env python3
"""
scripts/geocode_goteborg.py
----------------------------
Geocode all Gothenburg‐municipality company addresses.

Usage:
    python scripts/geocode_goteborg.py \
      data/goteborg_companies_addresses.csv \
      data/goteborg_with_coords.csv
"""
import logging
from argparse import ArgumentParser
from pathlib import Path
import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeopyError

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def try_geocode(address: str, geocode: RateLimiter):
    """Return (lat, lon) or (None, None)."""
    variants = [address, f"{address}, Sweden"]
    for q in variants:
        try:
            loc = geocode(q, country_codes="se", exactly_one=True)
        except (GeocoderServiceError, GeopyError):
            continue
        if loc:
            return loc.latitude, loc.longitude
    return None, None

def main(in_csv: Path, out_csv: Path):
    if not in_csv.exists():
        logger.error("Input not found: %s", in_csv)
        raise SystemExit(1)
    df = pd.read_csv(in_csv)
    # ensure columns
    if "address" not in df:
        logger.error("No ‘address’ column in %s", in_csv)
        raise SystemExit(1)

    # inject lat/lon
    df["lat"] = pd.NA
    df["lon"] = pd.NA

    geo = Nominatim(user_agent="sponsor_match_geo", timeout=10)
    geocode = RateLimiter(geo.geocode, min_delay_seconds=1.1)

    to_geo = df["lat"].isna() | df["lon"].isna()
    logger.info("Geocoding %d/%d addresses", to_geo.sum(), len(df))
    for idx, row in df[to_geo].iterrows():
        lat, lon = try_geocode(row["address"], geocode)
        df.at[idx, "lat"] = lat
        df.at[idx, "lon"] = lon

    fails = df["lat"].isna().sum()
    if fails:
        logger.warning("%d addresses failed to geocode", fails)

    out_csv.parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(out_csv, index=False)
    logger.info("Wrote %d rows → %s", len(df), out_csv)

if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("in_csv", type=Path)
    p.add_argument("out_csv", type=Path)
    args = p.parse_args()
    main(args.in_csv, args.out_csv)
