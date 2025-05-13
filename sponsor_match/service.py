# sponsor_match/service.py
from sponsor_match.db import get_engine
from sponsor_match.clustering import load_model, FEATURES
import pandas as pd
from geopy.distance import distance

_kmeans = load_model()
_eng    = get_engine()

def recommend(assoc_lat, assoc_lon, size_bucket, top_n: int = 10) -> pd.DataFrame:
    """Return the nearest/top-cluster companies for one sports association."""
    # ── 1. pull all companies w/ same size bucket
    q = "SELECT * FROM companies WHERE size_bucket = %s"
    df = pd.read_sql(q, _eng, params=[size_bucket])

    if df.empty:
        return pd.DataFrame()

    # ── 2. compute cluster distance ← cheap filter
    df["cluster"] = _kmeans.predict(df[FEATURES])
    target_cluster = _kmeans.predict([[assoc_lat, assoc_lon,
                                       df["rev_per_emp"].median()]])[0]
    df = df[df.cluster == target_cluster]

    # ── 3. true Haversine distance
    df["km"] = df.apply(
        lambda r: distance((assoc_lat, assoc_lon), (r.lat, r.lon)).km,
        axis=1,
    )
    return (
        df.sort_values("km")
          .loc[:, ["name", "address", "km", "size_bucket"]]
          .head(top_n)
          .reset_index(drop=True)
    )
