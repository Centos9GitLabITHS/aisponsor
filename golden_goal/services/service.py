#!/usr/bin/env python3
"""
golden_goal/services/service.py
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

from golden_goal.ml.pipeline import score_and_rank_optimized, ScoringWeights

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


class GoldenGoalService:
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
            "associations_geocoded_prepared.csv",
            "gothenburg_associations.csv",
            "sample_associations.csv"
        ]

        for filename in assoc_files:
            filepath = data_dir / filename
            if filepath.exists():
                try:
                    self.associations_df = pd.read_csv(filepath)

                    # Standardize column names
                    column_mapping = {
                        'Föreningsnamn': 'name',
                        'Association Name': 'name',
                        'latitude': 'lat',
                        'longitude': 'lon',
                        'Latitude': 'lat',
                        'Longitude': 'lon',
                        'Adress': 'address',
                        'Address': 'address',
                        'gatuadress': 'address',
                        'Gatuadress': 'address',
                        'Medlemsantal': 'member_count',
                        'Member Count': 'member_count',
                        'Members': 'member_count',
                        'Postort': 'city',
                        'postort': 'city',
                        'Stad': 'city',
                        'stad': 'city',
                        'Postnummer': 'postal_code',
                        'postnummer': 'postal_code',
                        'Post Nr': 'postal_code'  # Added this for space-separated postal code
                    }

                    # Rename columns if they exist
                    for old_name, new_name in column_mapping.items():
                        if old_name in self.associations_df.columns:
                            self.associations_df.rename(columns={old_name: new_name}, inplace=True)

                    # Ensure required columns exist
                    if 'id' not in self.associations_df.columns:
                        self.associations_df['id'] = range(1, len(self.associations_df) + 1)

                    if 'size_bucket' not in self.associations_df.columns:
                        # Determine size bucket based on member count
                        if 'member_count' in self.associations_df.columns:
                            self.associations_df['size_bucket'] = self.associations_df['member_count'].apply(
                                lambda x: 'small' if x < 400 else 'medium' if x < 800 else 'large'
                            )
                        else:
                            self.associations_df['size_bucket'] = 'medium'

                    # Fill missing addresses
                    if 'address' not in self.associations_df.columns:
                        self.associations_df['address'] = ''

                    logger.info(f"Loaded {len(self.associations_df)} associations from {filename}")
                    logger.info(f"Columns: {list(self.associations_df.columns)}")
                    # Debug: show first row to see actual data
                    if len(self.associations_df) > 0:
                        first_row = self.associations_df.iloc[0]
                        logger.info(f"First association name: {first_row.get('name', 'NO NAME')}")
                        logger.info(f"First association address: '{first_row.get('address', 'NO ADDRESS')}'")
                        logger.info(
                            f"First association city: '{first_row.get('city', first_row.get('Postort', 'NO CITY'))}'")
                    break
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

        # Load companies
        company_files = [
            "companies_complete.csv",  # Add this line
            "companies_prepared.csv",
            "municipality_of_goteborg.csv",
            "companies_geocoded.csv",
            "sample_companies.csv"
        ]

        for filename in company_files:
            filepath = data_dir / filename
            if filepath.exists():
                try:
                    self.companies_df = pd.read_csv(filepath)

                    # Standardize column names
                    column_mapping = {
                        'latitude': 'lat',
                        'longitude': 'lon',
                        'Latitude': 'lat',
                        'Longitude': 'lon',
                        'Företagsnamn': 'name',
                        'Company Name': 'name',
                        'Bransch': 'industry',
                        'Industry': 'industry'
                    }

                    # Rename columns if they exist
                    for old_name, new_name in column_mapping.items():
                        if old_name in self.companies_df.columns:
                            self.companies_df.rename(columns={old_name: new_name}, inplace=True)

                    # Ensure required columns
                    if 'id' not in self.companies_df.columns:
                        self.companies_df['id'] = range(1, len(self.companies_df) + 1)

                    if 'size_bucket' not in self.companies_df.columns:
                        self.companies_df['size_bucket'] = 'medium'

                    if 'industry' not in self.companies_df.columns:
                        self.companies_df['industry'] = 'Other'

                    logger.info(f"Loaded {len(self.companies_df)} companies from {filename}")
                    logger.info(f"Columns: {list(self.companies_df.columns)}")
                    break
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

        # Cache the data
        _data_cache['associations'] = self.associations_df
        _data_cache['companies'] = self.companies_df

    def _get_address_parts(self, row):
        """Extract address parts from a dataframe row with multiple fallbacks."""
        parts = []

        # Try multiple possible address fields
        for field in ['address', 'Address', 'Adress', 'street_address', 'gatuadress']:
            if field in row and pd.notna(row[field]) and str(row[field]).strip():
                parts.append(str(row[field]).strip())
                break

        # Add city/postal info
        for field in ['city', 'City', 'Postort', 'postort', 'stad']:
            if field in row and pd.notna(row[field]) and str(row[field]).strip():
                parts.append(str(row[field]).strip())
                break

        # Add postal code if available
        for field in ['postal_code', 'postnummer', 'Postnummer', 'Post Nr', 'zip']:
            if field in row and pd.notna(row[field]) and str(row[field]).strip():
                parts.append(str(row[field]).strip())
                break

        return parts

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
                    # Get address using the new helper method
                    addr_parts = self._get_address_parts(assoc)
                    address_str = ", ".join(addr_parts) if addr_parts else "Address not available"

                    results.append(SearchResult(
                        id=int(assoc.get('id', 0)),
                        name=str(assoc.get('name', '')),
                        type='association',
                        address=address_str,
                        latitude=float(assoc.get('lat', assoc.get('latitude', 0))),
                        longitude=float(assoc.get('lon', assoc.get('longitude', 0))),
                        score=score,
                        metadata={
                            'size_bucket': str(assoc.get('size_bucket', 'medium')),
                            'member_count': int(assoc.get('member_count', 0)),
                            'city': str(assoc.get('city', ''))
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

        # Convert to DataFrame and include all metadata fields
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
            # Get address using the helper method
            addr_parts = self._get_address_parts(assoc)
            address_str = ", ".join(addr_parts) if addr_parts else ""

            return {
                'id': int(assoc.get('id', 0)),
                'name': str(assoc.get('name', '')),
                'lat': float(assoc.get('lat', assoc.get('latitude', 0))),
                'lon': float(assoc.get('lon', assoc.get('longitude', 0))),
                'size_bucket': str(assoc.get('size_bucket', 'medium')),
                'member_count': int(assoc.get('member_count', 0)),
                'address': address_str
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

        from golden_goal.ml.pipeline import (
            haversine, calculate_distance_score,
            calculate_size_match_score, calculate_industry_affinity
        )

        assoc_lat = association['lat']
        assoc_lon = association['lon']
        assoc_size = association['size_bucket']

        recommendations = []

        # Debug: Check first company
        if len(self.companies_df) > 0:
            first_company = self.companies_df.iloc[0]
            logger.info(
                f"First company in scoring: name='{first_company.get('name', 'NO NAME')}', id={first_company.get('id', 'NO ID')}")

        for idx, company in self.companies_df.iterrows():
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

            # Get company name with better fallback
            company_name = str(company.get('name', ''))
            if not company_name or company_name == 'nan':
                company_name = f"Company_{company.get('id', idx)}"

            # Debug first few companies
            if len(recommendations) < 3:
                logger.info(
                    f"Adding company: name='{company_name}', id={company.get('id', 'NO ID')}, score={final_score:.3f}")

            recommendations.append({
                "id": int(company.get('id', 0)),
                "name": company_name,
                "lat": comp_lat,
                "lon": comp_lon,
                "latitude": comp_lat,
                "longitude": comp_lon,
                "distance": round(distance_km, 2),
                "distance_km": round(distance_km, 1),
                "score": round(final_score, 4),
                "size_bucket": str(company.get('size_bucket', 'medium')),
                "industry": str(company.get('industry', 'Other')),
                "display_name": company_name
            })

        # Sort by score and return top N
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Returning {len(recommendations[:top_n])} recommendations")
        return recommendations[:top_n]


# Module-level convenience functions
_service_instance = None


def get_service(engine=None):
    """Get or create a GoldenGoalService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = GoldenGoalService(engine)
    return _service_instance


def search(engine, query: str) -> pd.DataFrame:
    """Search wrapper for backward compatibility."""
    service = get_service(engine)
    return service.search(query)


def recommend(engine, association_name: str, top_n: int = 10) -> pd.DataFrame:
    """Recommend wrapper for backward compatibility."""
    service = get_service(engine)
    return service.recommend(association_name, top_n)