"""
Service for handling search-related functionality.
Acts as a bridge between UI and business logic.
"""
import logging
import pandas as pd

from sponsor_match.core.db import get_engine
from sponsor_match.services.recommendation import RecommendationService
from sponsor_match.services.service_v2 import RecommendationRequest

logger = logging.getLogger(__name__)

# Global instances
_engine = None
_recommendation_service = None
_clubs_df = None

def _ensure_initialized():
    """Ensure service components are initialized."""
    global _engine, _recommendation_service, _clubs_df

    if _engine is None:
        try:
            _engine = get_engine()
            logger.info("Database engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")

    if _recommendation_service is None:
        try:
            _recommendation_service = RecommendationService()
            logger.info("Recommendation service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize recommendation service: {e}")

    if _clubs_df is None:
        _load_clubs()

def _load_clubs():
    """Load club data from database or fallback to sample data."""
    global _clubs_df

    try:
        if _engine:
            _clubs_df = pd.read_sql("SELECT * FROM clubs", _engine)
            logger.info(f"Loaded {len(_clubs_df)} clubs from database")
        else:
            raise Exception("No database engine available")
    except Exception as e:
        logger.warning(f"Failed to load clubs from database: {e}")
        # Create sample data as fallback
        _clubs_df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['IFK Göteborg', 'GAIS', 'BK Häcken'],
            'size_bucket': ['large', 'medium', 'medium'],
            'member_count': [500, 250, 300],
            'lat': [57.7089, 57.6969, 57.7209],
            'lon': [11.9746, 11.9789, 11.9390],
            'address': ['Göteborg', 'Göteborg', 'Göteborg']
        })
        logger.info("Using sample club data")

def search_clubs(query):
    """
    Search for clubs matching the query.

    Args:
        query: String to search for in club names

    Returns:
        DataFrame of matching clubs or None if error
    """
    _ensure_initialized()

    try:
        if _clubs_df is not None:
            # Filter clubs based on query
            filtered = _clubs_df[_clubs_df['name'].str.contains(query, case=False)]
            logger.info(f"Found {len(filtered)} clubs matching '{query}'")
            return filtered
    except Exception as e:
        logger.error(f"Error searching clubs: {e}")

    return None

def search_sponsors(club_id, top_n=10, filters=None):
    """
    Search for sponsors matching a club.

    Args:
        club_id: ID of the club to match
        top_n: Maximum number of results to return
        filters: Dictionary of filters to apply

    Returns:
        Tuple of (sponsors DataFrame, scores dictionary)
    """
    _ensure_initialized()

    try:
        if _recommendation_service:
            # Create recommendation request
            request = RecommendationRequest(
                club_id=club_id,
                top_n=top_n,
                filters=filters
            )

            # Get recommendations
            result = _recommendation_service.recommend(request)
            logger.info(f"Found {len(result.companies)} sponsors for club_id={club_id}")
            return result.companies, result.scores
    except Exception as e:
        logger.error(f"Error searching sponsors: {e}")

    # Return dummy data as fallback
    return _get_dummy_sponsors(), {}

def _get_dummy_sponsors():
    """Return dummy sponsor data for fallback."""
    return pd.DataFrame([
        {
            "id": 1,
            "name": "Nordic Bank",
            "description": "Vill stötta lokal ungdomsidrott.",
            "lat": 57.70,
            "lon": 11.97,
            "score": 0.75,
            "revenue_ksek": 50000,
            "employees": 120,
            "industry": "Finance",
            "size_bucket": "large"
        },
        {
            "id": 2,
            "name": "Energigruppen AB",
            "description": "Söker gröna partners.",
            "lat": 57.71,
            "lon": 11.98,
            "score": 0.50,
            "revenue_ksek": 25000,
            "employees": 45,
            "industry": "Energy",
            "size_bucket": "medium"
        },
        {
            "id": 3,
            "name": "Techify Solutions",
            "description": "Digital inkludering för unga.",
            "lat": 57.72,
            "lon": 11.99,
            "score": 0.90,
            "revenue_ksek": 15000,
            "employees": 30,
            "industry": "Technology",
            "size_bucket": "medium"
        }
    ])
