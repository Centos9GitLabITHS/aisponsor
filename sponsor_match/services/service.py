#!/usr/bin/env python3
"""
sponsor_match/services/service.py
---------------------------------
OPTIMIZED service layer for Streamlit Cloud deployment.
Uses CSV files instead of database for better performance.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List

import numpy as np
import pandas as pd

from sponsor_match.ml.pipeline import score_and_rank_optimized, ScoringWeights

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# Cache for data
_data_cache = {}


@dataclass
class SearchResult:
    """Structured search result with validation."""
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
    """Main service class for sponsor search and recommendations."""

    def __init__(self, db_engine=None):
        # For Streamlit Cloud, we ignore db_engine and use CSV files
        self.engine = None
        self.Session = None

        # Load data into memory
        self._load_csv_data()

        # Initialize scoring weights
        self.scoring_weights = ScoringWeights(
            distance=0.4,
            size_match=0.3,
            cluster_match=0.2,
            industry_affinity=0.1
        )

    def _load_csv_data(self):
        """Load CSV data into memory if not already cached."""
        global _data_cache

        if 'associations' in _data_cache and 'companies' in _data_cache:
            self.associations_df = _data_cache['associations']
            self.companies_df = _data_cache['companies']
            return

        # Find data directory
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"

        # Load associations
        assoc_files = [
            "associations_geocoded.csv",
            "associations_prepared.csv",
            "gothenburg_associations.csv",
            "sample_associations.csv"
        ]

        for filename in assoc_files:
            filepath = data_dir / filename
            if filepath.exists():
                try:
                    self.associations_df = pd.read_csv(filepath)
                    # Ensure required columns
                    if 'latitude' in self.associations_df.columns and 'lat' not in self.associations_df.columns:
                        self.associations_df['lat'] = self.associations_df['latitude']
                    if 'longitude' in self.associations_df.columns and 'lon' not in self.associations_df.columns:
                        self.associations_df['lon'] = self.associations_df['longitude']
                    if 'id' not in self.associations_df.columns:
                        self.associations_df['id'] = range(1, len(self.associations_df) + 1)
                    logger.info(f"Loaded {len(self.associations_df)} associations from {filename}")
                    break
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

        # Load companies
        company_files = [
            "companies_prepared.csv",
            "municipality_of_goteborg.csv",
            "sample_companies.csv"
        ]

        for filename in company_files:
            filepath = data_dir / filename
            if filepath.exists():
                try:
                    self.companies_df = pd.read_csv(filepath)
                    # Ensure required columns
                    if 'latitude' in self.companies_df.columns and 'lat' not in self.companies_df.columns:
                        self.companies_df['lat'] = self.companies_df['latitude']
                    if 'longitude' in self.companies_df.columns and 'lon' not in self.companies_df.columns:
                        self.companies_df['lon'] = self.companies_df['longitude']
                    if 'id' not in self.companies_df.columns:
                        self.companies_df['id'] = range(1, len(self.companies_df) + 1)
                    logger.info(f"Loaded {len(self.companies_df)} companies from {filename}")
                    break
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

        # Cache the data
        _data_cache['associations'] = self.associations_df
        _data_cache['companies'] = self.companies_df

    def search(self, query: str, limit: int = 100) -> pd.DataFrame:
        """Search associations and companies by name with fuzzy matching."""
        query_lower = query.lower().strip()
        if len(query_lower) < 2:
            return pd.DataFrame()

        results = []

        # Search associations
        if hasattr(self, 'associations_df') and not self.associations_df.empty:
            for _, assoc in self.associations_df.iterrows():
                name_lower = str(assoc.get('name', '')).lower()
                score = self._calculate_text_similarity(query_lower, name_lower)
                if score > 0.3:
                    results.append(SearchResult(
                        id=int(assoc.get('id', 0)),
                        name=str(assoc.get('name', '')),
                        type='association',
                        address=str(assoc.get('address', '')),
                        latitude=float(assoc.get('lat', assoc.get('latitude', 0))),
                        longitude=float(assoc.get('lon', assoc.get('longitude', 0))),
                        score=score,
                        metadata={
                            'size_bucket': str(assoc.get('size_bucket', 'medium')),
                            'member_count': int(assoc.get('member_count', 0))
                        }
                    ))

        # Search companies
        if hasattr(self, 'companies_df') and not self.companies_df.empty:
            for _, comp in self.companies_df.iterrows():
                name_lower = str(comp.get('name', '')).lower()
                score = self._calculate_text_similarity(query_lower, name_lower)
                if score > 0.3:
                    results.append(SearchResult(
                        id=int(comp.get('id', 0)),
                        name=str(comp.get('name', '')),
                        type='company',
                        address=None,
                        latitude=float(comp.get('lat', comp.get('latitude', 0))),
                        longitude=float(comp.get('lon', comp.get('longitude', 0))),
                        score=score,
                        metadata={
                            'industry': str(comp.get('industry', 'Other')),
                            'size_bucket': str(comp.get('size_bucket', 'medium'))
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
        """Calculate a similarity score between 0 and 1 for two text strings."""
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
        """Find an association by exact name."""
        if not hasattr(self, 'associations_df') or self.associations_df.empty:
            return None

        match = self.associations_df[self.associations_df['name'] == name]
        if not match.empty:
            assoc = match.iloc[0]
            return {
                'id': int(assoc.get('id', 0)),
                'name': str(assoc.get('name', '')),
                'lat': float(assoc.get('lat', assoc.get('latitude', 0))),
                'lon': float(assoc.get('lon', assoc.get('longitude', 0))),
                'size_bucket': str(assoc.get('size_bucket', 'medium')),
                'member_count': int(assoc.get('member_count', 0)),
                'address': str(assoc.get('address', ''))
            }
        return None

    def recommend(self, association_name: str, top_n: int = 10, max_distance: float = 50.0) -> pd.DataFrame:
        """Get sponsor recommendations using optimized pipeline."""
        assoc = self.get_association_by_name(association_name)
        if not assoc:
            logger.warning(f"No association found matching '{association_name}'")
            return pd.DataFrame()

        try:
            # For Streamlit Cloud, we'll use a simplified scoring without database
            # This uses the CSV data directly
            recommendations = self._score_companies_csv(assoc, max_distance, top_n)

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
            # Fallback to using the original pipeline if available
            try:
                recommendations = score_and_rank_optimized(
                    association_id=assoc['id'],
                    bucket=assoc['size_bucket'],
                    max_distance=max_distance,
                    top_n=top_n,
                    weights=self.scoring_weights
                )
                if recommendations:
                    df = pd.DataFrame(recommendations)
                    df['score_percentage'] = df['score'].apply(lambda x: round(np.clip(x, 0, 1) * 100, 1))
                    return df
            except:
                pass

            return pd.DataFrame()

    def _score_companies_csv(self, association: Dict, max_distance: float, top_n: int) -> List[Dict]:
        """Score companies using CSV data directly."""
        if not hasattr(self, 'companies_df') or self.companies_df.empty:
            return []

        from sponsor_match.ml.pipeline import (
            haversine, calculate_distance_score,
            calculate_size_match_score, calculate_industry_affinity
        )

        assoc_lat = association['lat']
        assoc_lon = association['lon']
        assoc_size = association['size_bucket']

        recommendations = []

        for _, company in self.companies_df.iterrows():
            comp_lat = float(company.get('lat', company.get('latitude', 0)))
            comp_lon = float(company.get('lon', company.get('longitude', 0)))

            if comp_lat == 0 or comp_lon == 0:
                continue

            # Calculate distance
            distance_km = haversine(assoc_lat, assoc_lon, comp_lat, comp_lon)
            if distance_km > max_distance:
                continue

            # Calculate scores
            distance_score = calculate_distance_score(distance_km, max_distance)
            size_score = calculate_size_match_score(
                assoc_size,
                str(company.get('size_bucket', 'medium'))
            )
            industry_score = calculate_industry_affinity(
                str(company.get('industry', 'Other')),
                str(company.get('name', ''))
            )

            # Simple weighting without clustering
            final_score = (
                    0.5 * distance_score +
                    0.3 * size_score +
                    0.2 * industry_score
            )

            recommendations.append({
                "id": int(company.get('id', 0)),
                "name": str(company.get('name', '')),
                "lat": comp_lat,
                "lon": comp_lon,
                "latitude": comp_lat,
                "longitude": comp_lon,
                "distance": round(distance_km, 2),
                "distance_km": round(distance_km, 1),
                "score": round(final_score, 4),
                "size_bucket": str(company.get('size_bucket', 'medium')),
                "industry": str(company.get('industry', 'Other'))
            })

        # Sort by score and return top N
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:top_n]


# Module-level convenience functions
_service_instance = None


def get_service(engine=None):
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
