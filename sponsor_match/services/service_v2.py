#!/usr/bin/env python3
"""
sponsor_match/services/service_v2.py
------------------------------------
Business‐logic layer (v2) for SponsorMatch AI.
This version includes:
- Corrected clustering logic for geographical matching
- Proper implementation of filters
- Integration with ML model for recommendation ranking (when available)

Takes a RecommendationRequest and returns a RecommendationResult.
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
        )

        # Drop companies without coordinates
        firms = firms.dropna(subset=["lat", "lon"]).reset_index(drop=True)

        if firms.empty:
            logger.warning(f"No companies found with size_bucket={request.size_bucket} and valid coordinates")
            return firms

        # Calculate distances for all remaining companies first (needed for both filtering and scoring)
        firms["dist_km"] = firms.apply(
            lambda r: geodesic((r.lat, r.lon), (request.lat, request.lon)).km,
            axis=1
        )

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
        if model is not None:
            # FIXED: Correctly predict cluster for the club's location
            club_cluster = int(model.predict([[request.lat, request.lon]])[0])
            logger.info(f"Club is in cluster {club_cluster}")

            # FIXED: Predict clusters for all companies
            company_coords = firms[["lat", "lon"]].values
            company_clusters = model.predict(company_coords)

            # Keep only companies in the same cluster as the club
            firms = firms[company_clusters == club_cluster].reset_index(drop=True)
            logger.info(f"After cluster filtering, {len(firms)} companies remain")

            if firms.empty:
                logger.warning(f"No companies found in the same cluster as the club (cluster {club_cluster})")
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

        Returns:
            - A Series of composite scores between 0 and 1
            - A dictionary of individual factor scores for explanation
        """
        # Create club DataFrame with the same number of rows as firms
        club_df = pd.DataFrame({
            'lat': [request.lat] * len(firms),
            'lon': [request.lon] * len(firms),
            'size_bucket': [request.size_bucket] * len(firms)
        })

        # Factor 1: Distance decay
        distances = firms["dist_km"]
        dist_score = np.exp(-distances / 50)  # Exponential decay with 50km scale

        # Factor 2: Size match
        size_match = self.feature_engineer.calculate_size_match(
            club_df["size_bucket"],
            firms["size_bucket"]
        )

        # Factor 3: Revenue per employee (normalized to 0-1)
        rev_per_emp = firms.revenue_ksek * 1000 / firms.employees.clip(lower=1)
        if rev_per_emp.std() > 0:
            rev_norm = (rev_per_emp - rev_per_emp.min()) / (rev_per_emp.max() - rev_per_emp.min())
        else:
            rev_norm = pd.Series(0.5, index=firms.index)

        # Collect all factor scores
        factor_scores = {
            "distance": dist_score,
            "size_match": size_match,
            "revenue": rev_norm
        }

        # Try to use ML model if available
        ml_score = None
        if self.ml_model is not None:
            try:
                # Generate features using FeatureEngineer
                features = self.feature_engineer.create_features(club_df, firms)

                # Use ML model to predict probability
                if hasattr(self.ml_model, 'predict_proba'):
                    ml_score = pd.Series(
                        self.ml_model.predict_proba(features)[:, 1],
                        index=firms.index
                    )
                else:
                    ml_score = pd.Series(
                        self.ml_model.predict(features),
                        index=firms.index
                    )

                factor_scores["ml_prediction"] = ml_score
                logger.info("Successfully applied ML model to score candidates")

            except Exception as e:
                logger.warning(f"Could not apply ML model: {e}")
                ml_score = None

        # Calculate composite score
        if ml_score is not None:
            # If ML model is available, give it higher weight
            composite = 0.3 * dist_score + 0.2 * size_match + 0.1 * rev_norm + 0.4 * ml_score
        else:
            # Otherwise use the default weights
            composite = 0.5 * dist_score + 0.3 * size_match + 0.2 * rev_norm

        return composite, factor_scores

    def recommend(
            self,
            request: RecommendationRequest
    ) -> RecommendationResult:
        """
        Generate sponsor recommendations.

        1. Resolve club coordinates if only club_id was given.
        2. Fetch & optionally cluster-filter companies.
        3. Score & pick the top_n.
        """
        # 1) ensure we have lat/lon
        if request.club_id is not None and (request.lat is None or request.lon is None):
            club = self._get_club_by_id(request.club_id)
            request.lat = float(club.lat)
            request.lon = float(club.lon)
            logger.info(f"Retrieved club coordinates: ({request.lat}, {request.lon})")

        if request.lat is None or request.lon is None:
            raise ValueError("Must provide either club_id or both lat and lon")

        # 2) get candidate firms
        firms = self._find_matching_companies(request)
        if firms.empty:
            logger.info("No candidate companies found for bucket '%s'", request.size_bucket)
            return RecommendationResult(companies=pd.DataFrame(), scores={}, metadata={})

        # 3) score them
        raw_scores, factor_scores = self._calculate_scores(firms, request)

        # Pick top N
        top_indices = raw_scores.sort_values(ascending=False).head(request.top_n).index
        result_df = firms.loc[top_indices].copy().reset_index(drop=True)

        # Attach a percent score for display
        result_df["score"] = (raw_scores.loc[top_indices] * 100).round(1).values

        # ADD DEBUG PRINTS HERE
        print("DEBUG: result_df columns:", result_df.columns.tolist())
        print("DEBUG: First row sample:", result_df.iloc[0].to_dict() if not result_df.empty else "Empty DataFrame")
        print("DEBUG: firms DataFrame columns:", firms.columns.tolist())

        # Also attach factor scores for explanation
        match_factors = {}
        for idx, row in result_df.iterrows():
            company_id = row['comp_id']  # CHANGED FROM row['id']
            factors = {}
            for factor_name, factor_series in factor_scores.items():
                if company_id in firms['comp_id'].values:  # CHANGED FROM firms['id'].values
                    company_idx = firms[firms['comp_id'] == company_id].index[
                        0]  # CHANGED FROM firms[firms['id'] == company_id]
                    if company_idx in factor_series.index:
                        factors[factor_name] = float(factor_series.loc[company_idx] * 100)
            match_factors[idx] = factors

        # Add match factors to the result dataframe
        result_df["match_factors"] = [match_factors.get(idx, {}) for idx in range(len(result_df))]

        # Build a simple scores dict (row-index → score)
        scores_dict = dict(zip(range(len(result_df)), result_df["score"].tolist()))

        metadata = {
            "request_id": str(uuid.uuid4()),
            "ml_model_used": self.ml_model is not None,
            "clustering_used": request.size_bucket in self.cluster_models
        }

        return RecommendationResult(companies=result_df, scores=scores_dict, metadata=metadata)
