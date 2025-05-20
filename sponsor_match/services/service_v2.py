#!/usr/bin/env python3
"""
SponsorMatchService (service_v2.py)
----------------------------------
Take a RecommendationRequest and return a RecommendationResult.
"""

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
from geopy.distance import geodesic

from sponsor_match.models.features import FeatureEngineer

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)


@dataclass
class RecommendationRequest:
    club_id: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    size_bucket: str = "medium"
    top_n: int = 15
    filters: Dict[str, Any] = None


@dataclass
class RecommendationResult:
    companies: pd.DataFrame
    scores: Dict[int, float]
    metadata: Dict[str, Any]


class SponsorMatchService:
    def __init__(self, db_engine, cluster_models: Dict[str, Any]):
        """
        Args:
            db_engine: SQLAlchemy Engine or connection.
            cluster_models: mapping size_bucket → trained MiniBatchKMeans.
        """
        self.db = db_engine
        self.cluster_models = cluster_models or {}

        # Try to load the ML model if it exists
        self.ml_model = None
        model_path = Path(__file__).parent.parent / "models" / "match_gb.joblib"
        if model_path.exists():
            try:
                self.ml_model = joblib.load(model_path)
                logger.info(f"Loaded ML model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load ML model: {e}")

        # Create feature engineer
        self.feature_engineer = FeatureEngineer()

    def _get_club_by_id(self, club_id: int) -> pd.Series:
        """Fetch a single club row from the DB."""
        df = pd.read_sql(
            "SELECT * FROM clubs WHERE id = %s",
            self.db,
            params=(club_id,)
        )
        if df.empty:
            raise ValueError(f"No club found with id={club_id}")
        return df.iloc[0]

    def _find_matching_companies(
            self, request: RecommendationRequest
    ) -> pd.DataFrame:
        """
        Pull all companies in the same size bucket, apply any filters,
        and optionally filter to the nearest cluster.

        Supported filters:
        - industries: list of industry names to include
        - max_distance: maximum distance in kilometers
        """
        # First, get all companies in the same size bucket
        firms = pd.read_sql(
            "SELECT * FROM companies WHERE size_bucket = %s",
            self.db,
            params=(request.size_bucket,)
        ).reset_index(drop=True)

        if firms.empty:
            logger.warning(f"No companies found with size_bucket={request.size_bucket}")
            return firms

        # Safely compute distance: missing coords → inf
        def safe_dist(row):
            try:
                return geodesic((row["lat"], row["lon"]), (request.lat, request.lon)).km
            except Exception:
                return float("inf")

        firms["dist_km"] = firms.apply(safe_dist, axis=1)

        # Apply maximum distance filter if specified
        if request.filters and request.filters.get("max_distance"):
            max_distance = request.filters["max_distance"]
            firms = firms[firms["dist_km"] <= max_distance]

            if firms.empty:
                logger.info(f"No companies found within {max_distance} km")
                return firms

        # Apply industry filter if specified
        if request.filters and request.filters.get("industries"):
            industries = request.filters["industries"]
            if industries:  # Only filter if the list is not empty
                firms = firms[firms["industry"].isin(industries)]

                if firms.empty:
                    logger.info(f"No companies found in industries: {industries}")
                    return firms

        # Apply geographical clustering if model exists
        model = self.cluster_models.get(request.size_bucket)
        if model is not None and not firms.empty:
            # Predict club's cluster
            club_cluster = int(model.predict([[request.lat, request.lon]])[0])
            logger.info(f"Club is in cluster {club_cluster}")

            # Predict clusters for all companies (using only those with valid coords)
            coords = firms[["lat", "lon"]].values
            company_clusters = model.predict(coords)

            firms = firms[company_clusters == club_cluster].reset_index(drop=True)
            logger.info(f"After cluster filtering, {len(firms)} companies remain")

            if firms.empty:
                logger.warning(f"No companies in the same cluster {club_cluster}")
                return firms

        return firms

    def _calculate_scores(
            self,
            firms: pd.DataFrame,
            request: RecommendationRequest
    ) -> Tuple[pd.Series, Dict[str, pd.Series]]:
        """
        Compute scores for each company based on multiple factors:
        - Geographical proximity (distance decay)
        - Size matching
        - Revenue per employee
        - ML model prediction (if available)
        """
        features = {}
        # 1) Distance score (using dist_km from _find_matching_companies)
        features["distance_km"] = firms["dist_km"]
        features["distance_score"] = np.exp(-features["distance_km"] / 50)

        # 2) Size match
        features["size_match"] = self.feature_engineer.calculate_size_match(
            pd.Series([request.size_bucket] * len(firms)), firms["size_bucket"]
        )

        # 3) Revenue per employee
        rev_per_emp = firms["revenue_ksek"] * 1000 / firms["employees"].clip(lower=1)
        features["rev_per_emp"] = rev_per_emp
        if rev_per_emp.std() > 0:
            features["rev_per_emp_normalized"] = (
                rev_per_emp - rev_per_emp.min()
            ) / (rev_per_emp.max() - rev_per_emp.min())

        # 4) ML model prediction
        if self.ml_model is not None:
            X = pd.DataFrame(features)
            try:
                features["ml_score"] = pd.Series(
                    self.ml_model.predict_proba(X)[:, 1],
                    index=X.index
                )
            except Exception as e:
                logger.warning(f"ML model scoring failed: {e}")

        # Combine scores: you can adjust weighting here
        # For simplicity, final score = distance_score * size_match
        distance = features.get("distance_score", pd.Series(1.0, index=firms.index))
        size    = features.get("size_match", pd.Series(1.0, index=firms.index))
        final_score = distance * size

        return final_score, features

    def recommend(
            self,
            request: RecommendationRequest
    ) -> RecommendationResult:
        """Main entry point."""
        if request.club_id:
            club = self._get_club_by_id(request.club_id)
            request.lat = club["lat"]
            request.lon = club["lon"]
            request.size_bucket = club["size_bucket"]

        firms = self._find_matching_companies(request)
        if firms.empty:
            return RecommendationResult(companies=firms, scores={}, metadata={})

        scores, feats = self._calculate_scores(firms, request)
        # Build result DataFrame
        result_df = pd.DataFrame({"score": scores}).join(firms).join(pd.DataFrame(feats))
        # Sort and take top N
        result_df = result_df.sort_values("score", ascending=False).head(request.top_n)

        # Convert to dict mapping company_id→score
        score_dict = dict(zip(result_df["id"], result_df["score"]))

        return RecommendationResult(
            companies=result_df.reset_index(drop=True),
            scores=score_dict,
            metadata={"request_id": str(uuid.uuid4())}
        )
