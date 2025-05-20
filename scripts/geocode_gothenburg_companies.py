#!/usr/bin/env python3
"""
scripts/geocode_gothenburg_companies.py
---------------------------------------
Geocode Gothenburg company addresses with:
 - normalization (cache-friendly),
 - disk-cached results,
 - periodic checkpointing,
 - custom Nominatim endpoint support,
 - thread-based parallelism + RateLimiter (1 req/sec).
"""

import logging
import os
import pickle
import re
import time
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Tuple, Optional

import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from tqdm import tqdm

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
CACHE_FILE = Path("data/geocode_cache.pkl")
CHECKPOINT_INTERVAL = 1000    # save cache & partial CSV every N addresses
NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
USER_AGENT   = "sponsor_match_geo"
# -----------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def normalize_address(addr: str) -> str:
    """Lowercase, strip punctuation, standardize spacing & common terms."""
    s = addr.strip().lower()
    s = re.sub(r"[,.]", "", s)               # remove commas, periods
    s = re.sub(r"\bgatan\b", "g", s)         # 'gatan' → 'g'
    s = re.sub(r"\s+", " ", s)               # collapse whitespace
    return s

def load_cache() -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "rb") as f:
            cache = pickle.load(f)
        logger.info("Loaded %d cached addresses", len(cache))
    else:
        cache = {}
        logger.info("No existing cache; starting fresh")
    return cache

def save_cache(cache: Dict[str, Tuple[Optional[float], Optional[float]]]):
    CACHE_FILE.parent.mkdir(exist_ok=True, parents=True)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)  # type: ignore
    logger.info("Checkpoint: saved cache (%d entries)", len(cache))

def geocode_worker_init():
    """Initialize one shared geocoder + rate limiter per thread."""
    geocoder = Nominatim(
        user_agent=USER_AGENT,
        timeout=10,
        domain=NOMINATIM_URL.replace("https://", "").replace("http://", ""),
        scheme=NOMINATIM_URL.split("://")[0]
    )
    limiter = RateLimiter(geocoder.geocode, min_delay_seconds=1.1)
    globals()["_limiter"] = limiter

def geocode_one(addr_norm: str) -> Tuple[str, Optional[float], Optional[float]]:
    """Try geocoding two variants; return (normalized_address, lat, lon)."""
    for query in (addr_norm, f"{addr_norm}, sweden"):
        try:
            loc = globals()["_limiter"](query, country_codes="se", exactly_one=True)
        except ExceptionGroup as eg:
            # Python 3.11+: multiple errors in one go
            for sub in eg.exceptions:
                logger.debug("Sub-error for %r: %s", query, sub)
            time.sleep(2)
            continue
        except Exception as e:
            # any other single error (timeout, network, etc.)
            logger.debug("Error for %r: %s", query, e)
            time.sleep(2)
            continue

        if loc:
            return addr_norm, loc.latitude, loc.longitude

    return addr_norm, None, None

def parse_args():
    p = ArgumentParser(description="Geocode Gothenburg addresses w/ caching & threads")
    p.add_argument("--log-level", "-L", choices=["DEBUG","INFO","WARN","ERROR"], default="INFO")
    p.add_argument("-w", "--workers", type=int, default=4, help="Thread count")
    p.add_argument("--no-progress", action="store_true", help="Hide tqdm bar")
    p.add_argument("in_csv",  type=Path, help="Input CSV with 'address' or 'registered_address'")
    p.add_argument("out_csv", type=Path, help="Output CSV with lat,lon appended")
    return p.parse_args()

def main():
    args = parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # 1) Load data
    df = pd.read_csv(args.in_csv, dtype=str)
    if "address" not in df.columns:
        if "registered_address" in df.columns:
            df["address"] = df["registered_address"]
        else:
            logger.error("Need column 'address' or 'registered_address'")
            return

    # 2) Normalize
    df["address_norm"] = df["address"].map(normalize_address)

    # 3) Load cache & build list
    cache = load_cache()
    unique_norm = df["address_norm"].dropna().unique().tolist()
    to_geo = [a for a in unique_norm if a not in cache]
    logger.info("Need to geocode %d/%d unique addresses", len(to_geo), len(unique_norm))

    # 4) Parallel geocode with checkpointing
    if to_geo:
        with ThreadPoolExecutor(max_workers=args.workers,
                                initializer=geocode_worker_init) as exe:
            futures = {exe.submit(geocode_one, addr): addr for addr in to_geo}
            it = tqdm(as_completed(futures), total=len(futures),
                      desc="Geocoding", disable=args.no_progress)
            for i, fut in enumerate(it, start=1):
                addr = futures[fut]
                try:
                    _, lat, lon = fut.result()
                except ExceptionGroup as eg:
                    # should never hit here—handled in geocode_one—but just in case:
                    for sub in eg.exceptions:
                        logger.debug("Late sub-error for %r: %s", addr, sub)
                    lat, lon = None, None
                except Exception as e:
                    logger.debug("Late error for %r: %s", addr, e)
                    lat, lon = None, None

                cache[addr] = (lat, lon)

                # checkpoint every N
                if i % CHECKPOINT_INTERVAL == 0:
                    save_cache(cache)
                    # write partial CSV
                    outp = args.out_csv.with_suffix(".partial.csv")
                    df_partial = df[df["address_norm"].isin(cache)]
                    df_partial["lat"] = df_partial["address_norm"].map(lambda x: cache[x][0])
                    df_partial["lon"] = df_partial["address_norm"].map(lambda x: cache[x][1])
                    df_partial.to_csv(outp, index=False)
                    logger.info("Partial CSV (%d rows) → %s", len(df_partial), outp)

        save_cache(cache)

    # 5) Map coords back to full DF
    df["lat"] = df["address_norm"].map(lambda x: cache.get(x, (None, None))[0])
    df["lon"] = df["address_norm"].map(lambda x: cache.get(x, (None, None))[1])

    # 6) Write final
    args.out_csv.parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(args.out_csv, index=False)
    logger.info("Wrote %d rows to %s", len(df), args.out_csv)

if __name__ == "__main__":
    main()
