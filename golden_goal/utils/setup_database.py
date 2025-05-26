# Script to set up database tables and load sample data
# Detailed comments have been inserted in British English.

#!/usr/bin/env python3
"""
setup_database.py - Complete database setup for SponsorMatch AI
Ensures both associations and companies are properly loaded.
"""

# Standard library or third-party import
import logging

# Standard library or third-party import
import pandas as pd
# Standard library or third-party import
from sqlalchemy import text

# Standard library or third-party import
from golden_goal.core.db import get_engine
# Standard library or third-party import
from golden_goal.models.entities import Base

# Standard library or third-party import

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Definition of function 'setup_database': explains purpose and parameters
def setup_database():
    """Set up the complete database with sample data."""
    engine = get_engine()

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Created database tables")

    # Load associations
    load_sample_associations(engine)

    # Load companies
    load_sample_companies(engine)

    # Verify data
    verify_data(engine)


# Definition of function 'load_sample_associations': explains purpose and parameters
def load_sample_associations(engine):
    """Load sample associations with realistic Gothenburg data."""
    associations = [
        # Large clubs
        {'name': 'IFK Göteborg', 'address': 'Kamratgårdsvägen 50, 416 55 Göteborg',
         'lat': 57.706547, 'lon': 11.980125, 'size_bucket': 'large', 'member_count': 1500, 'founded_year': 1904},
        {'name': 'GAIS', 'address': 'Gamla Boråsvägen 75, 412 76 Göteborg',
         'lat': 57.687932, 'lon': 11.989746, 'size_bucket': 'large', 'member_count': 1200, 'founded_year': 1894},
        {'name': 'BK Häcken', 'address': 'Entreprenadvägen 6, 417 05 Göteborg',
         'lat': 57.705891, 'lon': 11.936847, 'size_bucket': 'large', 'member_count': 1000, 'founded_year': 1940},
        {'name': 'Örgryte IS', 'address': 'Skånegatan 5, 412 51 Göteborg',
         'lat': 57.693734, 'lon': 11.996542, 'size_bucket': 'large', 'member_count': 900, 'founded_year': 1887},

        # Medium clubs
        {'name': 'Qviding FIF', 'address': 'Härlanda Park 6B, 416 52 Göteborg',
         'lat': 57.703456, 'lon': 12.015234, 'size_bucket': 'medium', 'member_count': 400, 'founded_year': 1987},
        {'name': 'Västra Frölunda IF', 'address': 'Klubbvägen 19, 421 47 Västra Frölunda',
         'lat': 57.652341, 'lon': 11.928765, 'size_bucket': 'medium', 'member_count': 350, 'founded_year': 1947},
        {'name': 'Kärra KIF', 'address': 'Burmans gata 3, 425 33 Hisings Kärra',
         'lat': 57.765432, 'lon': 11.945678, 'size_bucket': 'medium', 'member_count': 300, 'founded_year': 1970},
        {'name': 'Sävedalens IF', 'address': 'Hultvägen 2, 433 64 Sävedalen',
         'lat': 57.709876, 'lon': 12.057891, 'size_bucket': 'medium', 'member_count': 450, 'founded_year': 1948},

        # Small clubs
        {'name': 'Majorna BK', 'address': 'Karl Johansgatan 152, 414 51 Göteborg',
         'lat': 57.689012, 'lon': 11.914567, 'size_bucket': 'small', 'member_count': 120, 'founded_year': 1990},
        {'name': 'Lundby IF', 'address': 'Munkedalsgatan 10, 417 16 Göteborg',
         'lat': 57.719234, 'lon': 11.942345, 'size_bucket': 'small', 'member_count': 100, 'founded_year': 2005},
        {'name': 'Gamlestaden FF', 'address': 'Artillerigatan 33, 415 02 Göteborg',
         'lat': 57.725678, 'lon': 12.005432, 'size_bucket': 'small', 'member_count': 80, 'founded_year': 2010},
        {'name': 'Kortedala IK', 'address': 'Julaftonsgatan 58, 415 44 Göteborg',
         'lat': 57.737890, 'lon': 12.026789, 'size_bucket': 'small', 'member_count': 90, 'founded_year': 1969},
    ]

    df = pd.DataFrame(associations)

    with engine.begin() as conn:
        # Clear existing data
        conn.execute(text("DELETE FROM associations"))

        # Insert new data
        df.to_sql('associations', conn, if_exists='append', index=False)

    logger.info(f"Loaded {len(df)} associations")


# Definition of function 'load_sample_companies': explains purpose and parameters
def load_sample_companies(engine):
    """Load sample companies in Gothenburg area."""
    companies = []

    # Technology companies (10-char orgnr format)
    companies.extend([
        {'name': 'Volvo Tech AB', 'orgnr': '5560123456', 'revenue_ksek': 150000, 'employees': 200,
         'year': 2023, 'size_bucket': 'large', 'industry': 'Technology', 'lat': 57.708765, 'lon': 11.965432},
        {'name': 'Ericsson Göteborg', 'orgnr': '5560234567', 'revenue_ksek': 200000, 'employees': 300,
         'year': 2023, 'size_bucket': 'large', 'industry': 'Technology', 'lat': 57.695432, 'lon': 11.987654},
        {'name': 'IT Solutions AB', 'orgnr': '5560345678', 'revenue_ksek': 25000, 'employees': 50,
         'year': 2023, 'size_bucket': 'medium', 'industry': 'Technology', 'lat': 57.712345, 'lon': 11.998765},
    ])

    # Finance companies
    companies.extend([
        {'name': 'Nordea Göteborg', 'orgnr': '5560456789', 'revenue_ksek': 300000, 'employees': 150,
         'year': 2023, 'size_bucket': 'large', 'industry': 'Finance', 'lat': 57.701234, 'lon': 11.975432},
        {'name': 'SEB Private Banking', 'orgnr': '5560567890', 'revenue_ksek': 180000, 'employees': 80,
         'year': 2023, 'size_bucket': 'large', 'industry': 'Finance', 'lat': 57.698765, 'lon': 11.968901},
        {'name': 'Finanskonsult AB', 'orgnr': '5560678901', 'revenue_ksek': 15000, 'employees': 20,
         'year': 2023, 'size_bucket': 'small', 'industry': 'Finance', 'lat': 57.715678, 'lon': 11.945678},
    ])

    # Manufacturing companies
    companies.extend([
        {'name': 'SKF Sverige AB', 'orgnr': '5560789012', 'revenue_ksek': 500000, 'employees': 1000,
         'year': 2023, 'size_bucket': 'large', 'industry': 'Manufacturing', 'lat': 57.721234, 'lon': 11.890123},
        {'name': 'Göteborg Mekaniska', 'orgnr': '5560890123', 'revenue_ksek': 45000, 'employees': 100,
         'year': 2023, 'size_bucket': 'medium', 'industry': 'Manufacturing', 'lat': 57.735678, 'lon': 11.912345},
        {'name': 'Precision Tools AB', 'orgnr': '5560901234', 'revenue_ksek': 30000, 'employees': 60,
         'year': 2023, 'size_bucket': 'medium', 'industry': 'Manufacturing', 'lat': 57.745678, 'lon': 11.923456},
    ])

    # Retail companies
    companies.extend([
        {'name': 'ICA Maxi Göteborg', 'orgnr': '5561012345', 'revenue_ksek': 120000, 'employees': 150,
         'year': 2023, 'size_bucket': 'large', 'industry': 'Retail', 'lat': 57.689012, 'lon': 11.934567},
        {'name': 'Systembolaget City', 'orgnr': '5561123456', 'revenue_ksek': 80000, 'employees': 50,
         'year': 2023, 'size_bucket': 'medium', 'industry': 'Retail', 'lat': 57.705678, 'lon': 11.967890},
        {'name': 'Sportbutiken AB', 'orgnr': '5561234567', 'revenue_ksek': 18000, 'employees': 25,
         'year': 2023, 'size_bucket': 'small', 'industry': 'Retail', 'lat': 57.698765, 'lon': 11.956789},
    ])

    # Healthcare companies
    companies.extend([
        {'name': 'Sahlgrenska Life', 'orgnr': '5561345678', 'revenue_ksek': 250000, 'employees': 400,
         'year': 2023, 'size_bucket': 'large', 'industry': 'Healthcare', 'lat': 57.683456, 'lon': 11.962345},
        {'name': 'Vårdcentral Väst', 'orgnr': '5561456789', 'revenue_ksek': 35000, 'employees': 45,
         'year': 2023, 'size_bucket': 'medium', 'industry': 'Healthcare', 'lat': 57.654321, 'lon': 11.923456},
        {'name': 'Hälsokliniken', 'orgnr': '5561567890', 'revenue_ksek': 12000, 'employees': 15,
         'year': 2023, 'size_bucket': 'small', 'industry': 'Healthcare', 'lat': 57.712345, 'lon': 11.989012},
    ])

    # Add more companies spread around Gothenburg
# Standard library or third-party import
    import random
    for i in range(20):
        lat = 57.65 + random.uniform(0, 0.1)
        lon = 11.9 + random.uniform(0, 0.15)
        revenue = random.randint(5000, 100000)

        size = 'small' if revenue < 20000 else 'medium' if revenue < 100000 else 'large'

        companies.append({
            'name': f'Local Business {i + 1} AB',
            'orgnr': f'556{200 + i:03d}{1000 + i:04d}',  # Format: 10 digits, no hyphen
            'revenue_ksek': revenue,
            'employees': random.randint(5, 200),
            'year': 2023,
            'size_bucket': size,
            'industry': random.choice(['Technology', 'Finance', 'Manufacturing', 'Retail', 'Healthcare']),
            'lat': lat,
            'lon': lon
        })

    df = pd.DataFrame(companies)

    with engine.begin() as conn:
        # Clear existing data
        conn.execute(text("DELETE FROM companies"))

        # Insert new data
        df.to_sql('companies', conn, if_exists='append', index=False)

    logger.info(f"Loaded {len(df)} companies")


# Definition of function 'verify_data': explains purpose and parameters
def verify_data(engine):
    """Verify the loaded data."""
    with engine.connect() as conn:
        # Count associations
        assoc_count = conn.execute(text("SELECT COUNT(*) FROM associations")).scalar()
        logger.info(f"Total associations: {assoc_count}")

        # Count by size bucket
        size_counts = conn.execute(text("""
            SELECT size_bucket, COUNT(*) as count 
            FROM associations 
            GROUP BY size_bucket
        """)).fetchall()

        for size, count in size_counts:
            logger.info(f"  {size}: {count} associations")

        # Count companies
        comp_count = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
        logger.info(f"Total companies: {comp_count}")

        # Count by industry
        industry_counts = conn.execute(text("""
            SELECT industry, COUNT(*) as count 
            FROM companies 
            GROUP BY industry
        """)).fetchall()

        for industry, count in industry_counts:
            logger.info(f"  {industry}: {count} companies")


# Entry point check: script execution starts here when run directly
if __name__ == "__main__":
    setup_database()