from pathlib import Path
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sqlalchemy import text
from sponsor_match.db import get_engine

CSV = Path(__file__).resolve().parents[1] / "data" / "associations_goteborg.csv"

def geocode(df: pd.DataFrame) -> pd.DataFrame:
    geo = Nominatim(user_agent="sponsor_match")
    rl  = RateLimiter(geo.geocode, min_delay_seconds=1)
    lats, lons = [], []
    for adr in df["address"]:
        loc = rl(f"{adr}, Sweden")
        lats.append(loc.latitude  if loc else None)
        lons.append(loc.longitude if loc else None)
    df["lat"] = lats
    df["lon"] = lons
    return df

def main():
    df = pd.read_csv(CSV)
    df = geocode(df)

    ddl = """
    CREATE TABLE IF NOT EXISTS associations (
      id           INT PRIMARY KEY,
      name         TEXT,
      member_count INT,
      address      TEXT,
      lat          DOUBLE,
      lon          DOUBLE
    ) CHARACTER SET utf8mb4;
    """

    eng = get_engine()
    with eng.begin() as con:
        con.execute(text(ddl))
        df.to_sql("associations", con, if_exists="replace", index=False)

    print(f"✅ Loaded {len(df)} associations.")

if __name__ == "__main__":
    main()
