#!/usr/bin/env python3
"""
scripts/build_associations_csv.py
---------------------------------
Read a CSV of club associations, geocode addresses to lat/lon, and write out a new CSV.

Retry logic:
    1. original address
    2. address + ", Sweden"
    3. replace suburb "Västra Frölunda" → "Göteborg"
    4. postal-code only (if comma present)
If all attempts fail, lat/lon remain NaN so you can inspect later.
"""
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
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
    Attempt to geocode `address` using successive fallback strategies.
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
        except Exception as e:
            logger.debug("Geocoding error for '%s': %s", query, e)
            continue
        if loc:
            return loc.latitude, loc.longitude
    return None, None


def main(input_csv: Path, output_csv: Path) -> None:
    """
    Read associations from `input_csv`, geocode missing coordinates,
    recompute size_bucket, and write to `output_csv`.
    """
    if not input_csv.exists():
        logger.error("Input CSV not found: %s", input_csv)
        raise SystemExit(1)

    logger.info("Loading %s", input_csv)
    df = pd.read_csv(input_csv)

    # ————— Column-normalization shim —————
    # Ensure we have 'lat' and 'lon' columns, renaming common alternates
    if "lat" not in df.columns or "lon" not in df.columns:
        for (alt_lat, alt_lon) in [("latitude", "longitude"), ("Latitude", "Longitude")]:
            if alt_lat in df.columns and alt_lon in df.columns:
                df = df.rename(columns={alt_lat: "lat", alt_lon: "lon"})
                break
    # Final sanity check
    if "lat" not in df.columns or "lon" not in df.columns:
        raise RuntimeError(
            "build_associations_csv.py error: input CSV must have 'lat' & 'lon' columns; "
            f"found {df.columns.tolist()}"
        )
    # ————————————————————————————————

    # Prepare geocoder (1 req/sec, 10s timeout)
    geo = Nominatim(user_agent="sponsor_match_geo", timeout=10, scheme="https")
    geocode = RateLimiter(geo.geocode, min_delay_seconds=1.1)

    # Identify rows needing geocoding
    missing_mask = df["lat"].isna() | df["lon"].isna()
    n_missing = missing_mask.sum()
    logger.info("Found %d/%d rows without coordinates", n_missing, len(df))

    # Geocode missing addresses
    failures = []
    for idx, row in df.loc[missing_mask].iterrows():
        lat, lon = try_geocode(row["address"], geocode)
        if lat is None:
            failures.append(row["address"])
        df.at[idx, "lat"] = lat
        df.at[idx, "lon"] = lon

    if failures:
        logger.warning("Still missing coordinates for %d addresses", len(failures))
        logger.debug("Failures: %s", failures)

    # Recompute size_bucket based on member_count
    bins = [0, 100, 500, float("inf")]
    labels = ["small", "medium", "large"]
    df["size_bucket"] = pd.cut(df["member_count"], bins=bins, labels=labels)

    # Write out
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info("Wrote %d rows → %s", len(df), output_csv)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Geocode club associations and enrich with coordinates"
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to input associations CSV (e.g. data/associations_goteborg.csv)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output CSV path (default: same directory, suffix '_with_coords.csv')"
    )
    args = parser.parse_args()
    out_path = args.output or args.input_csv.with_name(f"{args.input_csv.stem}_with_coords.csv")
    main(args.input_csv, out_path)
