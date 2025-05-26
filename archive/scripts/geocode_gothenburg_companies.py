# geocode_gothenburg_companies.py
"""
Geocode Gothenburg company addresses with:
 - normalisation for cache keys,
 - disk-cached results using pickle,
 - periodic checkpointing for large datasets,
 - thread-based parallelism with geopy RateLimiter.
"""
import logging  # Progress and debug logs
import os  # For environment variables
import pickle  # For caching address mappings
import re  # Regex for address normalisation
import time  # For retries
from argparse import ArgumentParser  # CLI parsing
from concurrent.futures import ThreadPoolExecutor, as_completed  # Parallelism
from pathlib import Path  # Filesystem paths
from typing import Dict, Tuple, Optional  # Type hints

import pandas as pd  # Data handling
from geopy.extra.rate_limiter import RateLimiter  # Rate-limiting for API
from geopy.geocoders import Nominatim  # Geocoding service
from tqdm import tqdm  # Progress bars

# Configuration constants
CACHE_FILE = Path("data/geocode_cache.pkl")
CHECKPOINT_INTERVAL = 1000
NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
USER_AGENT = "golden_goal_geo"

# Initialise logger
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_address(addr: str) -> str:
    """Standardise addresses for cache keys: lowercase, remove punctuation, collapse spaces."""
    s = addr.strip().lower()
    s = re.sub(r"[,.]", "", s)
    s = re.sub(r"\bgatan\b", "g", s)
    s = re.sub(r"\s+", " ", s)
    return s


def load_cache() -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """Load existing address-to-(lat,lon) cache from disk, or start fresh."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "rb") as f:
            cache = pickle.load(f)
        logger.info("Loaded %d cached addresses", len(cache))
    else:
        cache = {}
        logger.info("No existing cache; starting fresh")
    return cache


def save_cache(cache: Dict[str, Tuple[Optional[float], Optional[float]]]):
    """Persist the cache dictionary to disk."""
    CACHE_FILE.parent.mkdir(exist_ok=True, parents=True)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)
    logger.info("Checkpoint: saved cache (%d entries)", len(cache))


def geocode_worker_init():
    """Initialise a per-thread geocoder and rate-limiter for parallel requests."""
    geocoder = Nominatim(
        user_agent=USER_AGENT,
        timeout=10,
        domain=NOMINATIM_URL.replace("https://", "").replace("http://", ""),
        scheme=NOMINATIM_URL.split("://")[0]
    )
    limiter = RateLimiter(geocoder.geocode, min_delay_seconds=1.1)
    globals()["_limiter"] = limiter


def geocode_one(addr_norm: str) -> Tuple[str, Optional[float], Optional[float]]:
    """
    Attempt to geocode the normalised address, optionally appending ', sweden'.
    Returns (address_norm, lat, lon).
    Retries on errors up to two variants.
    """
    for query in (addr_norm, f"{addr_norm}, sweden"):
        try:
            loc = globals()["_limiter"](query, country_codes="se", exactly_one=True)
        except Exception as e:
            logger.debug("Error geocoding %r: %s", query, e)
            time.sleep(2)
            continue
        if loc:
            return addr_norm, loc.latitude, loc.longitude
    # Return None if both attempts fail
    return addr_norm, None, None


def parse_args():
    """Define and parse command-line arguments."""
    p = ArgumentParser(description="Geocode Göteborg addresses with caching & threads")
    p.add_argument("-L", "--log-level", choices=["DEBUG","INFO","WARN","ERROR"], default="INFO")
    p.add_argument("-w", "--workers", type=int, default=4)
    p.add_argument("--no-progress", action="store_true", help="Hide tqdm bar")
    p.add_argument("in_csv", type=Path, help="Input CSV with 'address' or 'registered_address'")
    p.add_argument("out_csv", type=Path, help="Output CSV with 'lat' and 'lon' appended")
    return p.parse_args()


def main():
    """Load data, normalise, parallel-geocode, checkpoint, and write final CSV."""
    args = parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # 1) Load input CSV
    df = pd.read_csv(args.in_csv, dtype=str)
    if "address" not in df.columns:
        if "registered_address" in df.columns:
            df["address"] = df["registered_address"]
        else:
            logger.error("Need column 'address' or 'registered_address'")
            return

    # 2) Normalise addresses for caching
    df["address_norm"] = df["address"].map(normalize_address)

    # 3) Load or initialise cache
    cache = load_cache()
    unique_norm = df["address_norm"].dropna().unique().tolist()
    to_geo = [a for a in unique_norm if a not in cache]
    logger.info("Need to geocode %d/%d unique addresses", len(to_geo), len(unique_norm))

    # 4) Parallel geocoding with checkpointing
    if to_geo:
        with ThreadPoolExecutor(max_workers=args.workers, initializer=geocode_worker_init) as exe:
            futures = {exe.submit(geocode_one, addr): addr for addr in to_geo}
            it = tqdm(as_completed(futures), total=len(futures), desc="Geocoding", disable=args.no_progress)
            for i, fut in enumerate(it, start=1):
                addr = futures[fut]
                try:
                    _, lat, lon = fut.result()
                except Exception as e:
                    logger.debug("Late error for %r: %s", addr, e)
                    lat, lon = None, None
                cache[addr] = (lat, lon)

                # Save cache and partial CSV at intervals
                if i % CHECKPOINT_INTERVAL == 0:
                    save_cache(cache)
                    partial = args.out_csv.with_suffix(".partial.csv")
                    df_partial = df[df["address_norm"].isin(cache)]
                    df_partial["lat"] = df_partial["address_norm"].map(lambda x: cache[x][0])
                    df_partial["lon"] = df_partial["address_norm"].map(lambda x: cache[x][1])
                    df_partial.to_csv(partial, index=False)
                    logger.info("Partial CSV (%d rows) → %s", len(df_partial), partial)
        save_cache(cache)

    # 5) Map coordinates back into full DataFrame
    df["lat"] = df["address_norm"].map(lambda x: cache.get(x, (None, None))[0])
    df["lon"] = df["address_norm"].map(lambda x: cache.get(x, (None, None))[1])

    # 6) Write the final output CSV
    args.out_csv.parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(args.out_csv, index=False)
    logger.info("Wrote %d rows to %s", len(df), args.out_csv)


if __name__ == "__main__":
    main()
