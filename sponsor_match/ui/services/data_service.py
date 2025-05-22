"""
Data service for handling data loading and initialization.
"""
import logging

import pandas as pd

from sponsor_match.core.db import get_engine
from sponsor_match.ui.utils.sessions import set_session_data

logger = logging.getLogger(__name__)

# Global caches
_engine = None
_clubs_df = None
_companies_df = None


def load_initial_data():
    """
    Load initial data needed by the application.
    This should be called once at startup.
    """
    try:
        # Initialize engine
        global _engine
        _engine = get_engine()
        logger.info("Database engine initialized")

        # Load clubs
        load_clubs()

        # Load only if needed in UI
        # load_companies()

        return True
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
        return False


def load_clubs():
    """
    Load clubs from database or use fallback data.

    Returns:
        DataFrame of clubs
    """
    global _clubs_df

    # Return cached data if available
    if _clubs_df is not None:
        return _clubs_df

    try:
        if _engine:
            _clubs_df = pd.read_sql("SELECT * FROM clubs", _engine)
            logger.info(f"Loaded {len(_clubs_df)} clubs from database")
            return _clubs_df
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

    return _clubs_df


def load_companies():
    """
    Load companies from database or use fallback data.

    Returns:
        DataFrame of companies
    """
    global _companies_df

    # Return cached data if available
    if _companies_df is not None:
        return _companies_df

    try:
        if _engine:
            _companies_df = pd.read_sql("SELECT * FROM companies", _engine)
            logger.info(f"Loaded {len(_companies_df)} companies from database")
            return _companies_df
    except Exception as e:
        logger.warning(f"Failed to load companies from database: {e}")

    # Create sample data as fallback
    _companies_df = pd.DataFrame([
        {
            "id": 1,
            "name": "Nordic Bank",
            "revenue_ksek": 50000,
            "employees": 120,
            "industry": "Finance",
            "size_bucket": "large",
            "lat": 57.70,
            "lon": 11.97
        },
        {
            "id": 2,
            "name": "Energigruppen AB",
            "revenue_ksek": 25000,
            "employees": 45,
            "industry": "Energy",
            "size_bucket": "medium",
            "lat": 57.71,
            "lon": 11.98
        }
    ])
    logger.info("Using sample company data")

    return _companies_df


def get_club_by_id(club_id):
    """
    Get a club by its ID.

    Args:
        club_id: Club ID to look up

    Returns:
        Club dictionary or None if not found
    """
    # Load clubs if needed
    clubs = load_clubs()

    # Find club by ID
    club_row = clubs[clubs['id'] == club_id]
    if len(club_row) > 0:
        return club_row.iloc[0].to_dict()

    return None


def save_club(club_data):
    """
    Save club data to database.
    This is a placeholder - in a real app, this would update the database.

    Args:
        club_data: Dictionary of club data to save

    Returns:
        True if successful, False otherwise
    """
    # In a real application, this would save to the database
    logger.info(f"Saving club data: {club_data}")

    # For now, just store in session state
    set_session_data("selected_club", club_data)

    # Pretend it was successful
    return True
