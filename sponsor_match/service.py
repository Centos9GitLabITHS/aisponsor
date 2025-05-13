# sponsor_match/service.py
"""
Business-logic layer:
 • fetch companies of the same size bucket from MySQL
 • drop rows lacking coordinates
 • pick the *nearest cluster* of companies (MiniBatch-KMeans) to the club
 • rank by distance + revenue/employee
"""
from __future__ import annotations

import pathlib
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import pairwise_distances

from sponsor_match.db import get_engine

# ──────────────────────────────────────────────────────────────
# 1.  Load any K-means models that are present on disk
#     (they are trained by sponsor_match/clustering.py)
# ──────────────────────────────────────────────────────────────
MODELS: dict[str, MiniBatchKMeans] = {
    b: joblib.load(f"models/kmeans_{b}.joblib")          # type: ignore[override]
    for b in ("small", "medium", "large")
    if pathlib.Path(f"models/kmeans_{b}.joblib").exists()
}

# ──────────────────────────────────────────────────────────────
# 2.  Recommend sponsors
# ──────────────────────────────────────────────────────────────
def recommend(lat: float, lon: float, bucket: str, top_n: int = 15) -> pd.DataFrame:
    """
    Return *top_n* candidate companies for a club located at (*lat*, *lon*).

    Parameters
    ----------
    lat, lon : float
        Club’s latitude & longitude (WGS-84).
    bucket : {'small', 'medium', 'large'}
        Size segment of the club.  We only compare with companies
        in the **same** segment.
    top_n : int, default 15
        How many suggestions to return.

    Returns
    -------
    pd.DataFrame
        Columns: name, revenue_ksek, employees, dist_km, lat, lon
    """
    eng = get_engine()

    # --- pull companies of the same size bucket -------------
    firms = pd.read_sql(
        "SELECT * FROM companies WHERE size_bucket = :bucket",
        eng,
        params={"bucket": bucket},
    )

    # ignore rows without coordinates
    firms = firms.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    if firms.empty:
        return pd.DataFrame()

    # --- cluster-aware candidate set ------------------------
    if bucket in MODELS:
        model = MODELS[bucket]
        label = int(model.predict([[lat, lon]])[0])
        cand = firms.loc[model.labels_ == label].copy()
    else:                         # cold-start fallback
        cand = firms.copy()

    # --- distance (coarse: 1 deg ≈ 111 km) ------------------
    cand["dist_km"] = (
        pairwise_distances(cand[["lat", "lon"]], np.array([[lat, lon]]), metric="euclidean")
        * 111.0
    )

    # --- rank & trim ----------------------------------------
    cols_keep = [
        "name",          # change to 'company_name' if that’s the actual column
        "revenue_ksek",
        "employees",
        "dist_km",
        "lat",
        "lon",
    ]
    out = (
        cand.sort_values(["dist_km", "rev_per_emp"], ascending=[True, False])
        .head(top_n)
        .loc[:, cols_keep]
        .reset_index(drop=True)
    )
    return out
