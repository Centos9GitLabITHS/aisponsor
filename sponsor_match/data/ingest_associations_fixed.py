#!/usr/bin/env python3
"""
Ingest Gothenburg associations with geocoding and proper data cleaning.
"""

import logging
import time
from pathlib import Path

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sqlalchemy import text

from sponsor_match.core.db import get_engine
from sponsor_match.models.entities import Base, Association

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_associations_data(df):
    """Clean and prepare associations data."""
    # Create full address
    df['full_address'] = df['Adress'].fillna('') + ', ' + \
                         df['Post Nr'].fillna('').astype(str) + ' ' + \
                         df['Postort'].fillna('')

    # Clean up whitespace
    df['full_address'] = df['full_address'].str.strip().str.replace('  ', ' ')

    # Add ", Sverige" for better geocoding
    df['full_address'] = df['full_address'] + ', Sverige'

    return df


def geocode_addresses(df, limit=50):
    """Geocode addresses with rate limiting."""
    geolocator = Nominatim(user_agent="sponsormatch_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    geocoded = []

    for idx, row in df.iterrows():
        if idx >= limit:  # Limit for testing
            break

        try:
            location = geocode(row['full_address'])
            if location:
                geocoded.append({
                    'name': row['Namn'],
                    'address': row['full_address'],
                    'lat': location.latitude,
                    'lon': location.longitude
                })
                logger.info(f"Geocoded: {row['Namn']} -> {location.latitude}, {location.longitude}")
            else:
                # Try with just city name
                location = geocode(f"{row['Postort']}, Sverige")
                if location:
                    geocoded.append({
                        'name': row['Namn'],
                        'address': row['full_address'],
                        'lat': location.latitude,
                        'lon': location.longitude
                    })
                    logger.info(f"Geocoded (city): {row['Namn']} -> {location.latitude}, {location.longitude}")
                else:
                    logger.warning(f"Could not geocode: {row['Namn']}")

        except Exception as e:
            logger.error(f"Geocoding error for {row['Namn']}: {e}")
            time.sleep(2)  # Extra delay on error

    return pd.DataFrame(geocoded)


def assign_size_buckets(df):
    """Assign size buckets based on name patterns and random distribution."""
    import random

    # Keywords that suggest size
    large_keywords = ['IFK', 'GAIS', 'BK Häcken', 'Örgryte']
    small_keywords = ['FF', 'Futsal', 'Ungdom']

    def get_size_bucket(name):
        name_upper = name.upper()

        # Check for large club indicators
        for keyword in large_keywords:
            if keyword.upper() in name_upper:
                return 'large'

        # Check for small club indicators
        for keyword in small_keywords:
            if keyword.upper() in name_upper:
                return 'small'

        # Random distribution for others
        rand = random.random()
        if rand < 0.3:
            return 'small'
        elif rand < 0.7:
            return 'medium'
        else:
            return 'large'

    df['size_bucket'] = df['name'].apply(get_size_bucket)

    # Assign member counts based on size
    def get_member_count(size):
        if size == 'small':
            return random.randint(50, 150)
        elif size == 'medium':
            return random.randint(151, 500)
        else:
            return random.randint(501, 1500)

    df['member_count'] = df['size_bucket'].apply(get_member_count)
    df['founded_year'] = [random.randint(1900, 2020) for _ in range(len(df))]

    return df


def main():
    """Main ingestion function."""
    # Read the CSV
    csv_path = Path("data/gothenburg_associations.csv")

    try:
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
            try:
                df = pd.read_csv(csv_path, encoding=encoding)
                logger.info(f"Successfully read CSV with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
    except Exception as e:
        logger.error(f"Could not read CSV: {e}")
        return

    # Filter out empty rows
    df = df[df['Namn'].notna()].copy()
    logger.info(f"Found {len(df)} associations")

    # Clean data
    df = clean_associations_data(df)

    # Geocode addresses (limited for testing)
    logger.info("Starting geocoding...")
    geocoded_df = geocode_addresses(df, limit=30)  # Limit to 30 for testing

    if geocoded_df.empty:
        logger.error("No addresses geocoded")
        return

    # Add size buckets and other fields
    geocoded_df = assign_size_buckets(geocoded_df)

    # Prepare for database
    geocoded_df['id'] = range(1, len(geocoded_df) + 1)

    # Insert into database
    engine = get_engine()

    # Create tables if needed
    Base.metadata.create_all(bind=engine)

    # Clear existing data
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM associations"))

        # Insert new data
        geocoded_df.to_sql(
            'associations',
            conn,
            if_exists='append',
            index=False,
            method='multi'
        )

    logger.info(f"Successfully loaded {len(geocoded_df)} associations")

    # Add some sample data for major clubs if not geocoded
    add_sample_major_clubs(engine)


def add_sample_major_clubs(engine):
    """Add well-known Gothenburg clubs with accurate coordinates."""
    major_clubs = [
        {
            'name': 'IFK Göteborg',
            'address': 'Kamratgårdsvägen 50, 416 55 Göteborg, Sverige',
            'lat': 57.706547,
            'lon': 11.980125,
            'size_bucket': 'large',
            'member_count': 1500,
            'founded_year': 1904
        },
        {
            'name': 'GAIS',
            'address': 'Gamla Boråsvägen 75, 412 76 Göteborg, Sverige',
            'lat': 57.687932,
            'lon': 11.989746,
            'size_bucket': 'large',
            'member_count': 1200,
            'founded_year': 1894
        },
        {
            'name': 'BK Häcken',
            'address': 'Entreprenadvägen 6, 417 05 Göteborg, Sverige',
            'lat': 57.705891,
            'lon': 11.936847,
            'size_bucket': 'large',
            'member_count': 1000,
            'founded_year': 1940
        }
    ]

    # Check if these already exist
    with engine.begin() as conn:
        for club in major_clubs:
            exists = conn.execute(
                text("SELECT 1 FROM associations WHERE name = :name"),
                {"name": club['name']}
            ).first()

            if not exists:
                conn.execute(
                    text("""
                        INSERT INTO associations 
                        (name, address, lat, lon, size_bucket, member_count, founded_year)
                        VALUES (:name, :address, :lat, :lon, :size_bucket, :member_count, :founded_year)
                    """),
                    club
                )
                logger.info(f"Added major club: {club['name']}")


if __name__ == "__main__":
    main()
