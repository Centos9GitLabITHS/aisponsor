#!/usr/bin/env python3
"""
sponsor_match/services/recommendation.py
----------------------------------------
Facade for the v2 SponsorMatchService, exposing a simple RecommendationService API.
"""

import logging
from typing import Dict, Any

from sponsor_match.core.db import get_engine
from sponsor_match.services.service_v2 import (
    SponsorMatchService,
    RecommendationRequest,
    RecommendationResult,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

class RecommendationService:
    """
    Wraps SponsorMatchService to provide a simplified interface.
    """

    def __init__(self, cluster_models: Dict[str, Any] = None) -> None:
        """
        Args:
            cluster_models: optional mapping size_bucket → trained KMeans models
        """
        self.db = get_engine()
        self.cluster_models = cluster_models or {}
        self._service = SponsorMatchService(self.db, self.cluster_models)

    def recommend(self, request: RecommendationRequest) -> RecommendationResult:
        """
        Generate recommendations based on the given request.

        Parameters
        ----------
        request : RecommendationRequest
            Contains club_id or lat/lon, size_bucket, top_n, and any filters.

        Returns
        -------
        RecommendationResult
            DataFrame of top companies, score dict, and metadata.
        """
        logger.info(
            "Processing recommendation (club_id=%s, coords=(%s,%s), bucket=%s)",
            request.club_id, request.lat, request.lon, request.size_bucket
        )
        try:
            result = self._service.recommend(request)
            logger.info(
                "Produced %d matches (request_id=%s)",
                len(result.companies), result.metadata.get("request_id")
            )
            return result
        except Exception as e:
            logger.exception("RecommendationService.recommend failed: %s", e)
            raise
