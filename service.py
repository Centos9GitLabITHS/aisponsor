#!/usr/bin/env python3
"""
sponsor_match/services/service.py
---------------------------------
Complete service layer for SponsorMatch AI, with search and recommendation features.
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

        # Caching geocoded data
        self._geocoded_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 7200  # 2 hours

        # Initialize scoring weights
        self.scoring_weights = ScoringWeights(
            distance=0.4,
            size_match=0.3,
            cluster_match=0.2,
            industry_affinity=0.1
        )

    def _get_geocoded_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get associations and companies DataFrames, using cache for efficiency.
        """
        now = datetime.now()
        if (self._geocoded_cache is not None and
            self._cache_timestamp is not None and
            (now - self._cache_timestamp).seconds < self._cache_ttl):
            return self._geocoded_cache

        logger.info("Loading fresh geocoded data...")
        associations_df, companies_df = load_geocoded_data()
        self._geocoded_cache = (associations_df, companies_df)
        self._cache_timestamp = now
        return associations_df, companies_df

    def search(self, query: str, limit: int = 100) -> pd.DataFrame:
        """
        Search associations and companies by name with fuzzy matching.
        Returns a DataFrame of results sorted by relevance score.
        """
        query_lower = query.lower().strip()
        if len(query_lower) < 2:
            return pd.DataFrame()  # Avoid trivial queries

        results = []
        try:
            associations_df, companies_df = self._get_geocoded_data()

            # Search associations
            for _, assoc in associations_df.iterrows():
                name_lower = str(assoc.get('name', '')).lower()
                score = self._calculate_text_similarity(query_lower, name_lower)
                if score > 0.3:
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

            # Fallback: search using the database
            with self.Session() as session:
                # Search associations in DB
                assocs = session.query(
                    Association.id, Association.name, Association.address,
                    Association.lat.label('latitude'), Association.lon.label('longitude'),
                    Association.size_bucket, Association.member_count
                ).filter(Association.name.ilike(f'%{query}%')).limit(limit//2).all()
                for assoc in assocs:
                    score = self._calculate_text_similarity(query_lower, assoc.name.lower())
                    results.append(SearchResult(
                        id=assoc.id,
                        name=assoc.name,
                        type='association',
                        address=assoc.address,
                        latitude=assoc.latitude,
                        longitude=assoc.longitude,
                        score=score,
                        metadata={'size_bucket': assoc.size_bucket, 'member_count': assoc.member_count}
                    ))
                # Search companies in DB
                comps = session.query(
                    Company.id, Company.name,
                    Company.lat.label('latitude'), Company.lon.label('longitude'),
                    Company.size_bucket, Company.industry
                ).filter(Company.name.ilike(f'%{query}%')).limit(limit//2).all()
                for comp in comps:
                    score = self._calculate_text_similarity(query_lower, comp.name.lower())
                    results.append(SearchResult(
                        id=comp.id,
                        name=comp.name,
                        type='company',
                        address=None,
                        latitude=comp.latitude,
                        longitude=comp.longitude,
                        score=score,
                        metadata={'industry': comp.industry, 'size_bucket': comp.size_bucket}
                    ))

        # Sort and return
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]
        df = pd.DataFrame([{
            'type':   r.type,
            'id':     r.id,
            'name':   r.name,
            'address': r.address,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'score':  r.score,
            'score_percentage': round(r.score*100, 1),
            **r.metadata
        } for r in results])
        return df

    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """
        Calculate a similarity score between 0 and 1 for two text strings.
        Combines substring match, token overlap (Jaccard), and character overlap.
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
            jaccard_score   * weights['jaccard'] +
            char_score      * weights['char']
        )
        return np.clip(final_score, 0.0, 1.0)

    def get_association_by_name(self, name: str) -> Optional[Dict]:
        """
        Find an association by exact name.
        Returns a dict with its details or None.
        """
        try:
            associations_df, _ = self._get_geocoded_data()
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
        with self.Session() as session:
            assoc = session.query(Association).filter(Association.name == name).first()
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
        """
        Get all companies with coordinates for matching.
        Returns a DataFrame (with 'lat','lon' columns).
        """
        try:
            _, companies_df = self._get_geocoded_data()
            if 'latitude' in companies_df.columns:
                companies_df = companies_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
            return companies_df
        except Exception as e:
            logger.warning(f"Failed to get geocoded companies: {e}")

        with self.Session() as session:
            companies = session.query(Company).filter(
                Company.lat.isnot(None),
                Company.lon.isnot(None)
            ).all()
        data = []
        for comp in companies:
            data.append({
                'id': comp.id, 'name': comp.name,
                'lat': comp.lat, 'lon': comp.lon,
                'size_bucket': comp.size_bucket,
                'industry': comp.industry,
                'revenue_ksek': comp.revenue_ksek,
                'employees': comp.employees
            })
        return pd.DataFrame(data)

    def recommend(self, association_name: str, top_n: int = 10, max_distance: float = 50.0) -> pd.DataFrame:
        """
        Get sponsor recommendations (as DataFrame) for a given association name.
        Uses the ML pipeline internally and normalizes results.
        """
        assoc = self.get_association_by_name(association_name)
        if not assoc:
            logger.warning(f"No association found matching '{association_name}'")
            return pd.DataFrame()

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

            df = pd.DataFrame(recommendations)
            df['score_percentage'] = df['score'].apply(lambda x: round(np.clip(x,0,1)*100,1))

            def get_match_quality(score):
                if score >= 0.8: return 'Excellent'
                elif score >= 0.6: return 'Good'
                elif score >= 0.4: return 'Fair'
                else: return 'Possible'

            df['match_quality'] = df['score'].apply(get_match_quality)
            df = df.sort_values('score', ascending=False).reset_index(drop=True)
            return df

        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return pd.DataFrame()

    def validate_all_scores(self) -> Dict[str, any]:
        """
        Diagnostic: validate scoring across a sample of associations.
        Returns stats on score distributions and any invalid scores.
        """
        associations_df, _ = self._get_geocoded_data()
        stats = {
            'total_checked': 0,
            'invalid_scores': [],
            'score_distribution': {'0-20%':0, '20-40%':0, '40-60%':0, '60-80%':0, '80-100%':0, '>100%':0}
        }
        sample_size = min(10, len(associations_df))
        sample_assocs = associations_df.sample(sample_size)

        for _, assoc in sample_assocs.iterrows():
            try:
                recs = score_and_rank(
                    association_id=assoc.get('id', 0),
                    bucket=assoc.get('size_bucket','medium'),
                    max_distance=50,
                    top_n=5
                )
                stats['total_checked'] += len(recs)
                for rec in recs:
                    score = rec['score']
                    if score < 0 or score > 1:
                        stats['invalid_scores'].append({
                            'association': assoc.get('name'),
                            'company': rec['name'],
                            'score': score
                        })
                    if score > 1:
                        stats['score_distribution']['>100%'] += 1
                    elif score >= 0.8:
                        stats['score_distribution']['80-100%'] += 1
                    elif score >= 0.6:
                        stats['score_distribution']['60-80%'] += 1
                    elif score >= 0.4:
                        stats['score_distribution']['40-60%'] += 1
                    elif score >= 0.2:
                        stats['score_distribution']['20-40%'] += 1
                    else:
                        stats['score_distribution']['0-20%'] += 1
            except Exception as e:
                logger.error(f"Validation error for {assoc.get('name')}: {e}")

        return stats

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

if __name__ == "__main__":
    # Example validation test
    from sponsor_match.core.db import get_engine
    engine = get_engine()
    service = SponsorMatchService(engine)
    print("Validating scoring system...")
    stats = service.validate_all_scores()
    print(f"Checked {stats['total_checked']} scores")
    print(f"Invalid scores found: {len(stats['invalid_scores'])}")
    print("\nScore distribution:")
    for rng, cnt in stats['score_distribution'].items():
        print(f"  {rng}: {cnt}")
    if stats['score_distribution']['>100%'] > 0:
        print("\n⚠️ WARNING: Found scores above 100%! This needs immediate fixing.")
    else:
        print("\n✅ All scores are within valid range (0-100%)")
