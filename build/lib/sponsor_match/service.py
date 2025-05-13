# sponsor_match/service.py
import joblib, pandas as pd, numpy as np, pathlib
from sklearn.metrics import pairwise_distances
from sponsor_match.db import get_engine

MODELS = {b: joblib.load(f"models/kmeans_{b}.joblib")
          for b in ["small","medium","large"]
          if pathlib.Path(f"models/kmeans_{b}.joblib").exists()}

def recommend(lat: float, lon: float, bucket: str, top_n=15) -> pd.DataFrame:
    eng = get_engine()
    firms = pd.read_sql(
        "select * from companies where size_bucket=%s", eng, params=[bucket]
    )
    if bucket in MODELS:
        label = MODELS[bucket].predict([[lat, lon]])[0]
        cand = firms[MODELS[bucket].labels_ == label]
    else:  # cold-start fallback
        cand = firms

    cand["dist_km"] = pairwise_distances(
        cand[["lat","lon"]], [[lat,lon]], metric="euclidean") * 111  # deg→km rough
    out = (cand.sort_values(["dist_km","rev_per_emp"]).head(top_n)
              .loc[:,["company_name","revenue_ksek","employees","dist_km","lat","lon"]])
    return out.reset_index(drop=True)
