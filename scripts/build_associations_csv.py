# scripts/build_associations_csv.py
"""
Re-build data/associations_goteborg_with_coords.csv

    $ python -m scripts.build_associations_csv
"""
from pathlib import Path
import sqlite3, time
import pandas as pd
from geopy.geocoders import Nominatim, Photon
from geopy.extra.rate_limiter import RateLimiter

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "data" / "associations_goteborg.csv"
OUT  = ROOT / "data" / "associations_goteborg_with_coords.csv"
CACHE = ROOT / "geocode_cache.db"

# ──────────────────────────────────────────────────────────────
# 1)  helper – 2-step geocoder   (Nominatim → Photon fallback)
# ──────────────────────────────────────────────────────────────
nominatim = Nominatim(user_agent="sponsormatch_bulk")
photon    = Photon(user_agent="sponsormatch_bulk")

g1 = RateLimiter(nominatim.geocode, min_delay_seconds=1)
g2 = RateLimiter(photon.geocode,    min_delay_seconds=1)

# tiny sqlite cache so we never spam the API
con = sqlite3.connect(CACHE)
con.execute("""CREATE TABLE IF NOT EXISTS cache (
                 address TEXT PRIMARY KEY,
                 lat     REAL,
                 lon     REAL,
                 ts      REAL
               )""")
con.commit()


def geo_lookup(addr: str) -> tuple[float | None, float | None]:
    """Return (lat,lon) or (None,None)"""
    cur = con.execute("SELECT lat,lon FROM cache WHERE address=?", (addr,))
    hit = cur.fetchone()
    if hit:
        return hit

    # 1️⃣ raw address
    loc = g1(addr)
    # 2️⃣ add “Göteborg, Sweden” if not found
    if loc is None and "Göteborg" not in addr:
        loc = g1(f"{addr}, Göteborg, Sweden")
    # 3️⃣ Photon fallback
    if loc is None:
        loc = g2(addr)

    if loc:
        con.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?)",
                    (addr, loc.latitude, loc.longitude, time.time()))
        con.commit()
        return loc.latitude, loc.longitude

    print("⚠️  could not geocode:", addr)
    con.execute("INSERT OR IGNORE INTO cache VALUES (?,?,?,?)",
                (addr, None, None, time.time()))
    con.commit()
    return None, None


# ──────────────────────────────────────────────────────────────
# 2)  load → geocode where missing
# ──────────────────────────────────────────────────────────────
df = pd.read_csv(SRC)

if {"lat", "lon"}.issubset(df.columns) is False:
    df["lat"] = pd.NA
    df["lon"] = pd.NA

for ix, row in df[df["lat"].isna() | df["lon"].isna()].iterrows():
    lat, lon = geo_lookup(row["address"])
    if lat is not None:
        df.at[ix, "lat"] = lat
        df.at[ix, "lon"] = lon

# ──────────────────────────────────────────────────────────────
# 3)  (re)compute size_bucket
# ──────────────────────────────────────────────────────────────
bins   = [0, 100, 500, float("inf")]
labels = ["small", "medium", "large"]
df["size_bucket"] = pd.cut(df["member_count"], bins=bins, labels=labels)

# ──────────────────────────────────────────────────────────────
# 4)  save
# ──────────────────────────────────────────────────────────────
df.to_csv(OUT, index=False)
print(f"✅  wrote {len(df)} rows → {OUT.relative_to(ROOT)}")
