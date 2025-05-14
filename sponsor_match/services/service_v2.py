#!/usr/bin/env python3
"""
sponsor_match/services/service_v2.py
------------------------------------
Business‐logic layer (v2) for SponsorMatch AI.
Takes a RecommendationRequest and returns a RecommendationResult.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
from geopy.distance import geodesic

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

    def _get_club_by_id(self, club_id: int) -> pd.Series:
        """Fetch a single club row from the DB."""
        df = pd.read_sql(
            "SELECT * FROM clubs WHERE id = :id",
            self.db,
            params={"id": club_id}
        )
        if df.empty:
            raise ValueError(f"No club found with id={club_id}")
        return df.iloc[0]

    def _find_matching_companies(
        self, request: RecommendationRequest
    ) -> pd.DataFrame:
        """
        Pull all companies in the same size bucket, drop missing coords,
        and optionally filter to the nearest cluster.
        """
        firms = pd.read_sql(
            "SELECT * FROM companies WHERE size_bucket = :bucket",
            self.db,
            params={"bucket": request.size_bucket}
        )
        firms = firms.dropna(subset=["lat", "lon"]).reset_index(drop=True)

        model = self.cluster_models.get(request.size_bucket)
        if model is not None:
            # assign cluster label for the club’s location
            label = int(model.predict([[request.lat, request.lon]])[0])
            firms = firms.loc[model.labels_ == label].reset_index(drop=True)

        return firms

    @staticmethod
    def _calculate_scores(
            firms: pd.DataFrame,
        request: RecommendationRequest
    ) -> pd.Series:
        """
        Compute a composite score ∈ [0,1] for each row in `firms`:
          - distance decay: exp(−dist_km/50)
          - revenue per employee normalized
        Returns a Series indexed by `firms`’ index.
        """
        # 1) geodesic distance
        distances = firms.apply(
            lambda r: geodesic((r.lat, r.lon), (request.lat, request.lon)).km,
            axis=1
        )
        # 2) distance score
        dist_score = np.exp(-distances / 50)

        # 3) revenue per employee
        rev_per_emp = firms.revenue_ksek * 1000 / firms.employees.clip(lower=1)
        if rev_per_emp.std() > 0:
            rev_norm = (rev_per_emp - rev_per_emp.min()) / (rev_per_emp.max() - rev_per_emp.min())
        else:
            rev_norm = pd.Series(0.0, index=firms.index)

        # 4) composite (equal weights)
        composite = 0.5 * dist_score + 0.5 * rev_norm
        return composite

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

        if request.lat is None or request.lon is None:
            raise ValueError("Must provide either club_id or both lat and lon")

        # 2) get candidate firms
        firms = self._find_matching_companies(request)
        if firms.empty:
            logger.info("No candidate companies found for bucket '%s'", request.size_bucket)
            return RecommendationResult(companies=pd.DataFrame(), scores={}, metadata={})

        # 3) score them
        raw_scores = self._calculate_scores(firms, request)
        # pick top N
        top = raw_scores.sort_values(ascending=False).head(request.top_n)
        result_df = firms.loc[top.index].copy().reset_index(drop=True)
        # attach a percent score for display
        result_df["score"] = (top * 100).round(1).values

        # build a simple scores dict (row-index → score)
        scores_dict = dict(zip(range(len(result_df)), result_df["score"].tolist()))

        metadata = {"request_id": str(uuid.uuid4())}
        return RecommendationResult(companies=result_df, scores=scores_dict, metadata=metadata)

