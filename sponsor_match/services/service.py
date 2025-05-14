#!/usr/bin/env python3
"""
sponsor_match/services/service.py
---------------------------------
Legacy business-logic layer for SponsorMatch (v1).
Fetches companies of the same size bucket, optionally filters by K-Means cluster,
and ranks them by distance + revenue/employee.
"""

import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import pairwise_distances
from sqlalchemy.engine import Engine

from sponsor_match.core.db import get_engine

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class LegacyRecommendationService:
    """
    Legacy v1 service: recommends sponsors given a club’s location.
    """

    def __init__(
        self,
        db_engine: Optional[Engine] = None,
        model_dir: Path = Path("models"),
        buckets: tuple[str, ...] = ("small", "medium", "large")
    ) -> None:
        """
        Args:
            db_engine: SQLAlchemy Engine (constructed via get_engine() if None)
            model_dir: directory where kmeans_{bucket}.joblib are stored
            buckets: size buckets to attempt loading models for
        """
        self.engine = db_engine or get_engine()
        self.cluster_models = self._load_cluster_models(model_dir, buckets)

    @staticmethod
    def _load_cluster_models(
        model_dir: Path,
        buckets: tuple[str, ...]
    ) -> Dict[str, MiniBatchKMeans]:
        """
        Load any MiniBatchKMeans models found in `model_dir` matching
        `kmeans_{bucket}.joblib`.
        """
        models: Dict[str, MiniBatchKMeans] = {}
        for b in buckets:
            path = model_dir / f"kmeans_{b}.joblib"
            if path.exists():
                try:
                    models[b] = joblib.load(path)
                    logger.info("Loaded cluster model for bucket '%s'", b)
                except Exception as e:
                    logger.warning("Failed to load %s: %s", path, e)
        return models

    def recommend(
        self,
        lat: float,
        lon: float,
        size_bucket: str,
        top_n: int = 15
    ) -> pd.DataFrame:
        """
        Return the top_n candidate companies for a club at (lat, lon)
        in the given size_bucket.
        """
        # 1) Query companies of same bucket
        df = pd.read_sql(
            "SELECT * FROM companies WHERE size_bucket = :bucket",
            self.engine,
            params={"bucket": size_bucket}
        )
        df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
        if df.empty:
            logger.info("No companies found in bucket '%s'", size_bucket)
            return pd.DataFrame()

        # 2) Optional cluster filtering
        model = self.cluster_models.get(size_bucket)
        if model:
            # assign cluster label for club's location
            label = int(model.predict([[lat, lon]])[0])
            df = df.loc[model.labels_ == label].reset_index(drop=True)
            logger.info("Filtered to %d companies in cluster %d", len(df), label)

        # 3) Compute distance (approx: 1° ≈ 111 km)
        coords = df[["lat", "lon"]].to_numpy()
        dist_km = pairwise_distances(coords, [[lat, lon]], metric="euclidean").flatten() * 111.0
        df["dist_km"] = dist_km

        # 4) Compute revenue per employee normalized to [0,1]
        rev_per_emp = df["revenue_ksek"] * 1000 / df["employees"].clip(lower=1)
        if rev_per_emp.std() > 0:
            rev_norm = (rev_per_emp - rev_per_emp.min()) / (rev_per_emp.max() - rev_per_emp.min())
        else:
            rev_norm = pd.Series(0.0, index=df.index)
        df["rev_per_emp_norm"] = rev_norm

        # 5) Composite score: closer & higher revenue favored equally
        df["score"] = (np.exp(-df["dist_km"] / 50) + rev_norm) / 2

        # 6) Select top N
        result = (
            df.sort_values("score", ascending=False)
              .head(top_n)
              .loc[:, ["name", "revenue_ksek", "employees", "dist_km", "lat", "lon", "score"]]
              .reset_index(drop=True)
        )
        logger.info("Returning %d top candidates", len(result))
        return result

def main() -> None:
    parser = ArgumentParser(
        description="Legacy: recommend sponsors by location and size bucket"
    )
    parser.add_argument("lat", type=float, help="Club latitude")
    parser.add_argument("lon", type=float, help="Club longitude")
    parser.add_argument(
        "--bucket",
        choices=["small", "medium", "large"],
        default="medium",
        help="Size bucket for filtering companies"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=15,
        help="Number of recommendations to return"
    )
    args = parser.parse_args()

    service = LegacyRecommendationService()
    df = service.recommend(args.lat, args.lon, args.bucket, args.top_n)
    if df.empty:
        print("No matches found.")
    else:
        print(df.to_string(index=False, float_format="%.1f"))

if __name__ == "__main__":
    main()
