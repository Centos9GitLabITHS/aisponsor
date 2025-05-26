#!/usr/bin/env python3
"""
sponsor_match/services/service.py
---------------------------------
OPTIMIZED service layer with cached data and efficient queries.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from sponsor_match.core.config import LOG_LEVEL
from sponsor_match.ml.pipeline import score_and_rank_optimized, ScoringWeights
from sponsor_match.models.entities import Base

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    Structured search result with validation.
    """
    id: int
    name: str
    type: str  # 'association' or 'company'
    address: Optional[str]
    latitude: float
    longitude: float
    score: float  # [0,1]
    metadata: Dict

    def __post_init__(self):
        # Ensure score is within [0,1]
        if not 0 <= self.score <= 1:
            logger.warning(f"Invalid score {self.score} for {self.name}, clamping to [0,1]")
            self.score = np.clip(self.score, 0.0, 1.0)


class SponsorMatchService:
    """
    Main service class for sponsor search and recommendations.
    """

    def __init__(self, db_engine):
        self.engine = db_engine
        self.Session = sessionmaker(bind=db_engine)
        Base.metadata.create_all(bind=db_engine)

        # Initialize scoring weights
        self.scoring_weights = ScoringWeights(
            distance=0.4,
            size_match=0.3,
            cluster_match=0.2,
            industry_affinity=0.1
        )

    def search(self, query: str, limit: int = 100) -> pd.DataFrame:
        """
        OPTIMIZED: Search only in database, no full data loading.
        """
        query_lower = query.lower().strip()
        if len(query_lower) < 2:
            return pd.DataFrame()  # Avoid trivial queries

        results = []

        with self.Session() as session:
            # Search associations using LIKE with index hint
            assocs = session.execute(text("""
                                          SELECT id, name, address, lat, lon, size_bucket, member_count
                                          FROM associations
                                          WHERE LOWER(name) LIKE :query LIMIT :limit
                                          """), {"query": f"%{query_lower}%", "limit": limit // 2}).fetchall()

            for assoc in assocs:
                name_lower = str(assoc[1]).lower()
                score = self._calculate_text_similarity(query_lower, name_lower)
                if score > 0.3:
                    results.append(SearchResult(
                        id=assoc[0],
                        name=assoc[1],
                        type='association',
                        address=assoc[2],
                        latitude=assoc[3] or 0,
                        longitude=assoc[4] or 0,
                        score=score,
                        metadata={
                            'size_bucket': assoc[5] or 'unknown',
                            'member_count': assoc[6] or 0
                        }
                    ))

            # Search companies - use indexed name search
            comps = session.execute(text("""
                                         SELECT id, name, lat, lon, size_bucket, industry
                                         FROM companies
                                         WHERE LOWER(name) LIKE :query LIMIT :limit
                                         """), {"query": f"%{query_lower}%", "limit": limit // 2}).fetchall()

            for comp in comps:
                name_lower = str(comp[1]).lower()
                score = self._calculate_text_similarity(query_lower, name_lower)
                if score > 0.3:
                    results.append(SearchResult(
                        id=comp[0],
                        name=comp[1],
                        type='company',
                        address=None,
                        latitude=comp[2] or 0,
                        longitude=comp[3] or 0,
                        score=score,
                        metadata={
                            'industry': comp[5] or 'unknown',
                            'size_bucket': comp[4] or 'unknown'
                        }
                    ))

        # Sort and return
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]

        df = pd.DataFrame([{
            'type': r.type,
            'id': r.id,
            'name': r.name,
            'address': r.address,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'score': r.score,
            'score_percentage': round(r.score * 100, 1),
            **r.metadata
        } for r in results])
        return df

    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """
        Calculate a similarity score between 0 and 1 for two text strings.
        """
        if not query or not text:
            return 0.0
        query = query.strip()
        text = text.strip()
        if query == text:
            return 1.0

        # Substring match score
        if query in text:
            substring_score = len(query) / len(text)
        else:
            substring_score = 0.0

        # Jaccard token overlap
        query_tokens = set(query.split())
        text_tokens = set(text.split())
        if query_tokens and text_tokens:
            intersection = query_tokens.intersection(text_tokens)
            union = query_tokens.union(text_tokens)
            jaccard_score = len(intersection) / len(union) if union else 0.0
        else:
            jaccard_score = 0.0

        # Character overlap
        char_overlap = sum(1 for c in query if c in text)
        char_score = char_overlap / max(len(query), len(text))

        # Combine with weights
        weights = {'substring': 0.5, 'jaccard': 0.3, 'char': 0.2}
        final_score = (
                substring_score * weights['substring'] +
                jaccard_score * weights['jaccard'] +
                char_score * weights['char']
        )
        return np.clip(final_score, 0.0, 1.0)

    def get_association_by_name(self, name: str) -> Optional[Dict]:
        """
        Find an association by exact name - direct DB query.
        """
        with self.Session() as session:
            result = session.execute(text("""
                                          SELECT id, name, lat, lon, size_bucket, member_count, address
                                          FROM associations
                                          WHERE name = :name LIMIT 1
                                          """), {"name": name}).fetchone()

            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'lat': float(result[2] or 0),
                    'lon': float(result[3] or 0),
                    'size_bucket': result[4] or 'medium',
                    'member_count': int(result[5] or 0),
                    'address': result[6] or ''
                }
        return None

    def recommend(self, association_name: str, top_n: int = 10, max_distance: float = 50.0) -> pd.DataFrame:
        """
        Get sponsor recommendations using optimized pipeline.
        """
        assoc = self.get_association_by_name(association_name)
        if not assoc:
            logger.warning(f"No association found matching '{association_name}'")
            return pd.DataFrame()

        try:
            # Use the optimized scoring function
            recommendations = score_and_rank_optimized(
                association_id=assoc['id'],
                bucket=assoc['size_bucket'],
                max_distance=max_distance,
                top_n=top_n,
                weights=self.scoring_weights
            )
            if not recommendations:
                logger.info("No recommendations found within criteria")
                return pd.DataFrame()

            df = pd.DataFrame(recommendations)
            df['score_percentage'] = df['score'].apply(lambda x: round(np.clip(x, 0, 1) * 100, 1))

            def get_match_quality(score):
                if score >= 0.8:
                    return 'Excellent'
                elif score >= 0.6:
                    return 'Good'
                elif score >= 0.4:
                    return 'Fair'
                else:
                    return 'Possible'

            df['match_quality'] = df['score'].apply(get_match_quality)
            df = df.sort_values('score', ascending=False).reset_index(drop=True)
            return df

        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return pd.DataFrame()


# Module-level convenience functions
_service_instance = None


def get_service(engine):
    """Get or create a SponsorMatchService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = SponsorMatchService(engine)
    return _service_instance


def search(engine, query: str) -> pd.DataFrame:
    """Search wrapper for backward compatibility."""
    service = get_service(engine)
    return service.search(query)


def recommend(engine, association_name: str, top_n: int = 10) -> pd.DataFrame:
    """Recommend wrapper for backward compatibility."""
    service = get_service(engine)
    return service.recommend(association_name, top_n)
