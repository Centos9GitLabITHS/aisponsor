#!/usr/bin/env python3
"""
scripts/build_associations_csv.py
---------------------------------
Read a CSV of club associations (with no lat/lon), geocode addresses to lat/lon,
and write out a new CSV with columns ['id','name','member_count','address','lat','lon','size_bucket'].
"""
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
from geopy.exc import GeocoderServiceError, GeopyError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def try_geocode(address: str, geocode: RateLimiter) -> Tuple[Optional[float], Optional[float]]:
    """
    Attempt to geocode `address` (Göteborg, Sweden) with fallbacks.
    Returns (lat, lon) or (None, None).
    """
    variants = [
        address,
        f"{address}, Sweden",
        address.replace("Västra Frölunda", "Göteborg"),
        (address.split(",", 1)[1].strip() if "," in address else ""),
    ]
    for query in variants:
        if not query:
            continue
        try:
            loc = geocode(query, country_codes="se", exactly_one=True)
        except (GeocoderServiceError, GeopyError) as e:
            logger.debug("Geocoding failed for %r: %s", query, e)
            continue
        if loc:
            return loc.latitude, loc.longitude
    return None, None

def main(input_csv: Path, output_csv: Path) -> None:
    if not input_csv.exists():
        logger.error("Input CSV not found: %s", input_csv)
        raise SystemExit(1)

    # If we've already built it, skip
    if output_csv.exists():
        logger.info("Found existing %s – skipping geocoding", output_csv)
        return

    logger.info("Loading %s", input_csv)
    df = pd.read_csv(input_csv)

    # Inject lat/lon columns if missing
    if "lat" not in df.columns:
        df["lat"] = pd.NA
    if "lon" not in df.columns:
        df["lon"] = pd.NA

    # Prepare geocoder
    geo = Nominatim(user_agent="sponsor_match_geo", timeout=10, scheme="https")
    geocode = RateLimiter(geo.geocode, min_delay_seconds=1.1)

    # Geocode every row that has missing lat or lon
    missing = df["lat"].isna() | df["lon"].isna()
    logger.info("Need geocoding for %d/%d rows", missing.sum(), len(df))
    failures = []
    for idx, row in df[missing].iterrows():
        lat, lon = try_geocode(row["address"], geocode)
        if lat is None:
            failures.append(row["address"])
        df.at[idx, "lat"] = lat
        df.at[idx, "lon"] = lon

    if failures:
        logger.warning("Failed geocoding %d addresses; leaving NaN", len(failures))

    # Recompute size_bucket
    bins = [0, 100, 500, float("inf")]
    labels = ["small", "medium", "large"]
    df["size_bucket"] = pd.cut(df["member_count"], bins=bins, labels=labels)

    # Write out
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info("Wrote %d rows → %s", len(df), output_csv)

if __name__ == "__main__":
    p = ArgumentParser(description="Geocode club associations")
    p.add_argument("input_csv", type=Path, help="Raw CSV (no lat/lon)")
    p.add_argument(
        "-o", "--output", type=Path,
        help="Out CSV (default: same dir, suffix '_with_coords.csv')"
    )
    args = p.parse_args()
    out = args.output or args.input_csv.with_name(f"{args.input_csv.stem}_with_coords.csv")
    main(args.input_csv, out)
