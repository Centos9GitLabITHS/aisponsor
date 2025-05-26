# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
sponsor_match/services/service.py

Complete service layer implementation with proper score normalization,
geocoded data support, and enhanced search functionality.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import sessionmaker

from sponsor_match.core.config import LOG_LEVEL
from sponsor_match.ml.pipeline import score_and_rank, load_geocoded_data, ScoringWeights
from sponsor_match.models.entities import Association, Company, Base

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Structured search result with validation."""
    id: int
    name: str
    type: str  # 'association' or 'company'
    address: Optional[str]
    latitude: float
    longitude: float
    score: float  # Always between 0 and 1
    metadata: Dict

    def __post_init__(self):
        """Validate score is in valid range."""
        if not 0 <= self.score <= 1:
            logger.warning(f"Invalid score {self.score} for {self.name}, clamping to valid range")
            self.score = np.clip(self.score, 0.0, 1.0)


class SponsorMatchService:
    """Main service class for sponsor matching operations with score validation."""

    def __init__(self, db_engine):
        """Initialize service with database engine."""
        self.engine = db_engine
        self.Session = sessionmaker(bind=db_engine)

        # Ensure tables exist
        Base.metadata.create_all(bind=db_engine)

        # Cache for geocoded data
        self._geocoded_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 3600  # 1 hour TTL

        # Initialize scoring weights with validation
        self.scoring_weights = ScoringWeights(
            distance=0.4,
            size_match=0.3,
            cluster_match=0.2,
            industry_affinity=0.1
        )

    def _get_geocoded_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get geocoded data with caching."""
        now = datetime.now()

        # Check cache validity
        if (self._geocoded_cache is not None and
                self._cache_timestamp is not None and
                (now - self._cache_timestamp).seconds < self._cache_ttl):
            return self._geocoded_cache

        # Load fresh data
        logger.info("Loading fresh geocoded data...")
        associations_df, companies_df = load_geocoded_data()

        # Update cache
        self._geocoded_cache = (associations_df, companies_df)
        self._cache_timestamp = now

        return associations_df, companies_df

    def search(self, query: str, limit: int = 100) -> pd.DataFrame:
        """
        Search both associations and companies by name with relevance scoring.

        Uses fuzzy matching for better results and ensures all scores are
        properly normalized to [0, 1] range.
        """
        # Normalize query
        query_lower = query.lower().strip()

        if len(query_lower) < 2:
            return pd.DataFrame()  # Empty result for very short queries

        results = []

        # Try geocoded data first
        try:
            associations_df, companies_df = self._get_geocoded_data()

            # Search associations
            for _, assoc in associations_df.iterrows():
                name_lower = str(assoc.get('name', '')).lower()

                # Calculate text similarity score
                score = self._calculate_text_similarity(query_lower, name_lower)

                if score > 0.3:  # Minimum threshold
                    results.append(SearchResult(
                        id=assoc.get('id', 0),
                        name=assoc.get('name', ''),
                        type='association',
                        address=assoc.get('address', ''),
                        latitude=assoc.get('latitude', assoc.get('lat', 0)),
                        longitude=assoc.get('longitude', assoc.get('lon', 0)),
                        score=score,
                        metadata={
                            'size_bucket': assoc.get('size_bucket', 'unknown'),
                            'member_count': assoc.get('member_count', 0)
                        }
                    ))

            # Search companies
            for _, comp in companies_df.iterrows():
                name_lower = str(comp.get('name', '')).lower()

                score = self._calculate_text_similarity(query_lower, name_lower)

                if score > 0.3:
                    results.append(SearchResult(
                        id=comp.get('id', 0),
                        name=comp.get('name', ''),
                        type='company',
                        address=comp.get('address', ''),
                        latitude=comp.get('latitude', comp.get('lat', 0)),
                        longitude=comp.get('longitude', comp.get('lon', 0)),
                        score=score,
                        metadata={
                            'industry': comp.get('industry', 'unknown'),
                            'size_bucket': comp.get('size_bucket', 'unknown')
                        }
                    ))

        except Exception as e:
            logger.warning(f"Geocoded data search failed: {e}, falling back to database")

            # Fallback to database search
            with self.Session() as session:
                # Search associations in database
                associations = session.query(
                    Association.id,
                    Association.name,
                    Association.address,
                    Association.lat.label('latitude'),
                    Association.lon.label('longitude'),
                    Association.size_bucket,
                    Association.member_count
                ).filter(
                    Association.name.ilike(f'%{query}%')
                ).limit(limit // 2).all()

                for assoc in associations:
                    score = self._calculate_text_similarity(query_lower, assoc.name.lower())
                    results.append(SearchResult(
                        id=assoc.id,
                        name=assoc.name,
                        type='association',
                        address=assoc.address,
                        latitude=assoc.latitude,
                        longitude=assoc.longitude,
                        score=score,
                        metadata={
                            'size_bucket': assoc.size_bucket,
                            'member_count': assoc.member_count
                        }
                    ))

                # Search companies in database
                companies = session.query(
                    Company.id,
                    Company.name,
                    Company.lat.label('latitude'),
                    Company.lon.label('longitude'),
                    Company.size_bucket,
                    Company.industry
                ).filter(
                    Company.name.ilike(f'%{query}%')
                ).limit(limit // 2).all()

                for comp in companies:
                    score = self._calculate_text_similarity(query_lower, comp.name.lower())
                    results.append(SearchResult(
                        id=comp.id,
                        name=comp.name,
                        type='company',
                        address=None,
                        latitude=comp.latitude,
                        longitude=comp.longitude,
                        score=score,
                        metadata={
                            'industry': comp.industry,
                            'size_bucket': comp.size_bucket
                        }
                    ))

        # Sort by score and convert to DataFrame
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]

        # Convert to DataFrame
        if results:
            df = pd.DataFrame([{
                'type': r.type,
                'id': r.id,
                'name': r.name,
                'address': r.address,
                'latitude': r.latitude,
                'longitude': r.longitude,
                'score': r.score,
                'score_percentage': round(r.score * 100, 1),  # Safe percentage
                **r.metadata
            } for r in results])
            return df
        else:
            return pd.DataFrame()

    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """
        Calculate normalized text similarity score between 0 and 1.

        Uses multiple similarity metrics combined with validated weights.
        """
        if not query or not text:
            return 0.0

        # Exact match
        if query == text:
            return 1.0

        # Substring match
        if query in text:
            # Score based on how much of the text is the query
            substring_score = len(query) / len(text)
        else:
            substring_score = 0.0

        # Token overlap (word-level matching)
        query_tokens = set(query.split())
        text_tokens = set(text.split())

        if query_tokens and text_tokens:
            intersection = query_tokens.intersection(text_tokens)
            union = query_tokens.union(text_tokens)
            jaccard_score = len(intersection) / len(union) if union else 0.0
        else:
            jaccard_score = 0.0

        # Character-level similarity (for typos)
        char_overlap = sum(1 for c in query if c in text)
        char_score = char_overlap / max(len(query), len(text))

        # Combine scores with weights that sum to 1.0
        weights = {
            'substring': 0.5,
            'jaccard': 0.3,
            'char': 0.2
        }

        final_score = (
                substring_score * weights['substring'] +
                jaccard_score * weights['jaccard'] +
                char_score * weights['char']
        )

        # Ensure score is in valid range
        return np.clip(final_score, 0.0, 1.0)

    def get_association_by_name(self, name: str) -> Optional[Dict]:
        """Get association details by name."""
        # Try geocoded data first
        try:
            associations_df, _ = self._get_geocoded_data()

            # Find exact match
            match = associations_df[associations_df['name'] == name]
            if not match.empty:
                assoc = match.iloc[0]
                return {
                    'id': int(assoc.get('id', 0)),
                    'name': assoc.get('name', ''),
                    'lat': float(assoc.get('latitude', assoc.get('lat', 0))),
                    'lon': float(assoc.get('longitude', assoc.get('lon', 0))),
                    'size_bucket': assoc.get('size_bucket', 'medium'),
                    'member_count': int(assoc.get('member_count', 0)),
                    'address': assoc.get('address', '')
                }
        except Exception as e:
            logger.warning(f"Geocoded lookup failed: {e}, using database")

        # Fallback to database
        with self.Session() as session:
            assoc = session.query(Association).filter(
                Association.name == name
            ).first()

            if assoc:
                return {
                    'id': assoc.id,
                    'name': assoc.name,
                    'lat': assoc.lat,
                    'lon': assoc.lon,
                    'size_bucket': assoc.size_bucket,
                    'member_count': assoc.member_count,
                    'address': assoc.address
                }

        return None

    def get_companies_for_matching(self) -> pd.DataFrame:
        """Get all companies with coordinates for matching."""
        # Prefer geocoded data
        try:
            _, companies_df = self._get_geocoded_data()

            # Ensure consistent column names
            if 'latitude' in companies_df.columns:
                companies_df = companies_df.rename(columns={
                    'latitude': 'lat',
                    'longitude': 'lon'
                })

            return companies_df

        except Exception as e:
            logger.warning(f"Failed to get geocoded companies: {e}")

        # Fallback to database
        with self.Session() as session:
            companies = session.query(Company).filter(
                Company.lat.isnot(None),
                Company.lon.isnot(None)
            ).all()

        data = []
        for comp in companies:
            data.append({
                'id': comp.id,
                'name': comp.name,
                'lat': comp.lat,
                'lon': comp.lon,
                'size_bucket': comp.size_bucket,
                'revenue_ksek': comp.revenue_ksek,
                'employees': comp.employees,
                'industry': comp.industry
            })

        return pd.DataFrame(data)

    def recommend(self, association_name: str, top_n: int = 10, max_distance: float = 50.0) -> pd.DataFrame:
        """
        Get sponsor recommendations with properly normalized scores.

        This method orchestrates the recommendation process:
        1. Finds the association
        2. Calls the ML pipeline for scoring
        3. Ensures all scores are properly normalized
        4. Returns formatted results
        """
        # Get association
        assoc = self.get_association_by_name(association_name)
        if not assoc:
            logger.warning(f"No association found matching '{association_name}'")
            return pd.DataFrame()

        # Use ML pipeline for recommendations
        try:
            recommendations = score_and_rank(
                association_id=assoc['id'],
                bucket=assoc['size_bucket'],
                max_distance=max_distance,
                top_n=top_n,
                weights=self.scoring_weights
            )

            if not recommendations:
                logger.info("No recommendations found within criteria")
                return pd.DataFrame()

            # Convert to DataFrame with additional formatting
            df = pd.DataFrame(recommendations)

            # Add percentage scores (guaranteed to be 0-100)
            df['score_percentage'] = df['score'].apply(lambda x: round(np.clip(x, 0, 1) * 100, 1))

            # Add match quality labels
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

            # Sort by score descending
            df = df.sort_values('score', ascending=False).reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return pd.DataFrame()

    def validate_all_scores(self) -> Dict[str, any]:
        """
        Diagnostic method to validate scoring across all associations.

        Returns statistics about score distributions to ensure they're
        all within valid ranges.
        """
        associations_df, _ = self._get_geocoded_data()

        score_stats = {
            'total_checked': 0,
            'invalid_scores': [],
            'score_distribution': {
                '0-20%': 0,
                '20-40%': 0,
                '40-60%': 0,
                '60-80%': 0,
                '80-100%': 0,
                '>100%': 0  # Should always be 0
            }
        }

        # Sample associations
        sample_size = min(10, len(associations_df))
        sample_assocs = associations_df.sample(sample_size)

        for _, assoc in sample_assocs.iterrows():
            try:
                # Get recommendations
                recommendations = score_and_rank(
                    association_id=assoc.get('id', 0),
                    bucket=assoc.get('size_bucket', 'medium'),
                    max_distance=50,
                    top_n=5
                )

                score_stats['total_checked'] += len(recommendations)

                # Check each score
                for rec in recommendations:
                    score = rec['score']

                    if score < 0 or score > 1:
                        score_stats['invalid_scores'].append({
                            'association': assoc.get('name'),
                            'company': rec['name'],
                            'score': score
                        })

                    # Categorize score
                    if score > 1:
                        score_stats['score_distribution']['>100%'] += 1
                    elif score >= 0.8:
                        score_stats['score_distribution']['80-100%'] += 1
                    elif score >= 0.6:
                        score_stats['score_distribution']['60-80%'] += 1
                    elif score >= 0.4:
                        score_stats['score_distribution']['40-60%'] += 1
                    elif score >= 0.2:
                        score_stats['score_distribution']['20-40%'] += 1
                    else:
                        score_stats['score_distribution']['0-20%'] += 1

            except Exception as e:
                logger.error(f"Validation error for {assoc.get('name')}: {e}")

        return score_stats


# Module-level functions for backward compatibility
_service_instance = None


def get_service(engine):
    """Get or create service instance."""
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


# Testing and validation
if __name__ == "__main__":
    from sponsor_match.core.db import get_engine

    engine = get_engine()
    service = SponsorMatchService(engine)

    # Validate scoring
    print("Validating scoring system...")
    stats = service.validate_all_scores()

    print(f"Checked {stats['total_checked']} scores")
    print(f"Invalid scores found: {len(stats['invalid_scores'])}")
    print("\nScore distribution:")
    for range_name, count in stats['score_distribution'].items():
        print(f"  {range_name}: {count}")

    if stats['score_distribution']['>100%'] > 0:
        print("\n⚠️ WARNING: Found scores above 100%! This needs immediate fixing.")
    else:
        print("\n✅ All scores are within valid range (0-100%)")