# scripts/build_associations_csv.py
"""
Read associations_goteborg.csv  → add lat / lon  → write *_with_coords.csv
Retry logic:
    1. full address as-is
    2. append ", Göteborg, Sweden"
    3. replace suburb with "Göteborg"
    4. fall back to postal-code only
If all fail → keep NaNs so you notice the problem.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

SRC  = pathlib.Path(sys.argv[1])
DEST = SRC.with_name(SRC.stem + "_with_coords.csv")

# 1 ─── read
df = pd.read_csv(SRC)

# 2 ─── geocoder (1 req / sec, 10 s timeout, Sweden only)
geo = Nominatim(
    user_agent="sponsor_match_geo",
    timeout=10,
    scheme="https",
)
geocode = RateLimiter(geo.geocode, min_delay_seconds=1.1)

def try_geocode(addr: str) -> tuple[float | None, float | None]:
    """Return (lat, lon) or (None, None)."""
    variants = [
        addr,                                          # original
        f"{addr}, Sweden",                             # add country
        addr.replace("Västra Frölunda", "Göteborg"),   # use city
        addr.split(",")[1].strip() if "," in addr else addr,  # postcode only
    ]
    for query in variants:
        if not query:
            continue
        loc = geocode(query, country_codes="se", exactly_one=True)
        if loc:
            return loc.latitude, loc.longitude
    return None, None

# 3 ─── look-up missing coords
missing = df["lat"].isna() | df["lon"].isna()
print(f"→ need to geocode {missing.sum()}/{len(df)} rows")
fails = []
for idx, row in df[missing].iterrows():
    lat, lon = try_geocode(row["address"])
    if lat is None:
        fails.append(row["address"])
    df.at[idx, "lat"], df.at[idx, "lon"] = lat, lon

if fails:
    print("⚠ still missing:", ", ".join(fails))

# 4 ─── add / refresh size_bucket
bins   = [0, 100, 500, float("inf")]
labels = ["small", "medium", "large"]
df["size_bucket"] = pd.cut(df["member_count"], bins=bins, labels=labels)

# 5 ─── save
df.to_csv(DEST, index=False)
print(f"✅ wrote {len(df)} rows → {DEST}")
