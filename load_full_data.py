#!/usr/bin/env python3
"""
load_full_data.py - Load the complete datasets into the database
"""

import logging
import pandas as pd
from pathlib import Path
from sqlalchemy import text
import numpy as np

from golden_goal.core.db import get_engine
from golden_goal.models.entities import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_size_bucket(value):
    """Clean and validate size_bucket values."""
    if pd.isna(value) or value is None or value == '':
        return 'medium'  # Default value

    value_str = str(value).lower().strip()

    # Map common variations
    if value_str in ['small', 's']:
        return 'small'
    elif value_str in ['medium', 'm', 'mellan']:
        return 'medium'
    elif value_str in ['large', 'l', 'stor']:
        return 'large'
    else:
        # Default to medium for any unknown values
        return 'medium'


def load_full_associations(engine):
    """Load associations from the prepared CSV file."""
    data_dir = Path(__file__).parent / "data"

    # Try different possible file locations
    possible_files = [
        data_dir / "associations_prepared.csv",
        Path("data/associations_prepared.csv"),
        Path("golden_goal/data/associations_prepared.csv")
    ]

    associations_file = None
    for file_path in possible_files:
        if file_path.exists():
            associations_file = file_path
            break

    if not associations_file:
        logger.error("Could not find associations_prepared.csv")
        return False

    logger.info(f"Loading associations from {associations_file}")

    # Read the CSV
    df = pd.read_csv(associations_file)
    logger.info(f"Loaded {len(df)} associations from CSV")

    # Rename columns to match database schema
    df = df.rename(columns={
        'Adress': 'address',
        'latitude': 'lat',
        'longitude': 'lon'
    })

    # Clean size_bucket values
    df['size_bucket'] = df['size_bucket'].apply(clean_size_bucket)

    # Ensure required columns exist
    required_cols = ['id', 'name', 'lat', 'lon', 'size_bucket']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    # Add member_count based on size_bucket if not present
    if 'member_count' not in df.columns:
        size_to_members = {
            'small': 200,  # 0-399
            'medium': 600,  # 400-799
            'large': 1000  # 800+
        }
        df['member_count'] = df['size_bucket'].map(size_to_members).fillna(500)

    # Add founded_year if not present
    if 'founded_year' not in df.columns:
        df['founded_year'] = 2000  # Default value

    # Select only the columns we need
    cols_to_keep = ['id', 'name', 'address', 'lat', 'lon', 'size_bucket', 'member_count', 'founded_year']
    cols_to_keep = [col for col in cols_to_keep if col in df.columns]
    df = df[cols_to_keep]

    # Remove any rows with missing coordinates
    df = df.dropna(subset=['lat', 'lon'])

    with engine.begin() as conn:
        # Clear existing data
        conn.execute(text("DELETE FROM associations"))

        # Insert new data
        df.to_sql('associations', conn, if_exists='append', index=False)

    logger.info(f"Successfully loaded {len(df)} associations into database")
    return True


def load_full_companies(engine):
    """Load companies from the prepared CSV file."""
    data_dir = Path(__file__).parent / "data"

    # Try different possible file locations
    possible_files = [
        data_dir / "companies_prepared.csv",
        Path("data/companies_prepared.csv"),
        Path("golden_goal/data/companies_prepared.csv")
    ]

    companies_file = None
    for file_path in possible_files:
        if file_path.exists():
            companies_file = file_path
            break

    if not companies_file:
        logger.error("Could not find companies_prepared.csv")
        return False

    logger.info(f"Loading companies from {companies_file}")

    # Read the CSV in chunks due to large size
    chunk_size = 5000  # Reduced chunk size for better error handling
    total_loaded = 0
    failed_chunks = []

    # First, clear existing data
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM companies"))

    # Process in chunks
    for chunk_num, chunk in enumerate(pd.read_csv(companies_file, chunksize=chunk_size)):
        try:
            logger.info(f"Processing chunk {chunk_num + 1} ({len(chunk)} companies)")

            # Rename columns to match database schema
            chunk = chunk.rename(columns={
                'PeOrgNr': 'orgnr',
                'latitude': 'lat',
                'longitude': 'lon'
            })

            # Clean size_bucket values - CRITICAL FIX
            chunk['size_bucket'] = chunk['size_bucket'].apply(clean_size_bucket)

            # Ensure orgnr is string and limited to 10 characters
            if 'orgnr' in chunk.columns:
                chunk['orgnr'] = chunk['orgnr'].astype(str).str[:10]
            else:
                chunk['orgnr'] = chunk.index.astype(str)

            # Ensure name is not null
            if 'name' in chunk.columns:
                chunk['name'] = chunk['name'].fillna('Unknown Company')

            # Add missing columns with default values
            if 'revenue_ksek' not in chunk.columns:
                # Assign revenue based on size_bucket
                size_to_revenue = {
                    'small': 15000,
                    'medium': 50000,
                    'large': 200000
                }
                chunk['revenue_ksek'] = chunk['size_bucket'].map(size_to_revenue).fillna(30000)

            if 'employees' not in chunk.columns:
                # Assign employees based on size_bucket
                size_to_employees = {
                    'small': 25,
                    'medium': 100,
                    'large': 500
                }
                chunk['employees'] = chunk['size_bucket'].map(size_to_employees).fillna(50)

            if 'year' not in chunk.columns:
                chunk['year'] = 2023

            if 'industry' not in chunk.columns:
                # Assign industries based on district or random
                industries = ['Technology', 'Finance', 'Manufacturing', 'Retail', 'Healthcare', 'Services', 'Other']
                if 'district' in chunk.columns:
                    # Use district to vary industries
                    chunk['industry'] = chunk.apply(
                        lambda row: industries[hash(str(row.get('district', ''))) % len(industries)],
                        axis=1
                    )
                else:
                    chunk['industry'] = pd.Series([industries[i % len(industries)] for i in range(len(chunk))])

            # Select only the columns we need
            cols_to_keep = ['id', 'orgnr', 'name', 'revenue_ksek', 'employees', 'year',
                            'size_bucket', 'industry', 'lat', 'lon']
            cols_to_keep = [col for col in cols_to_keep if col in chunk.columns]
            chunk = chunk[cols_to_keep]

            # Remove any rows with missing coordinates
            chunk = chunk.dropna(subset=['lat', 'lon'])

            # Convert any remaining NaN values to None for SQL compatibility
            chunk = chunk.where(pd.notnull(chunk), None)

            # Insert this chunk
            with engine.begin() as conn:
                chunk.to_sql('companies', conn, if_exists='append', index=False)

            total_loaded += len(chunk)
            logger.info(f"Loaded {total_loaded} companies so far...")

        except Exception as e:
            logger.error(f"Error in chunk {chunk_num + 1}: {e}")
            failed_chunks.append(chunk_num + 1)
            # Continue with next chunk instead of failing completely
            continue

    if failed_chunks:
        logger.warning(f"Failed to load chunks: {failed_chunks}")

    logger.info(f"Successfully loaded {total_loaded} companies into database")
    return total_loaded > 0


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

        # Count by size bucket for companies
        comp_size_counts = conn.execute(text("""
                                             SELECT size_bucket, COUNT(*) as count
                                             FROM companies
                                             GROUP BY size_bucket
                                                 LIMIT 10
                                             """)).fetchall()

        logger.info("Company size distribution:")
        for size, count in comp_size_counts:
            logger.info(f"  {size}: {count} companies")

        # Count by industry
        industry_counts = conn.execute(text("""
                                            SELECT industry, COUNT(*) as count
                                            FROM companies
                                            GROUP BY industry
                                                LIMIT 10
                                            """)).fetchall()

        logger.info("Top industries:")
        for industry, count in industry_counts:
            logger.info(f"  {industry}: {count} companies")

        # Sample some data to verify coordinates
        sample_assocs = conn.execute(text("""
                                          SELECT name, lat, lon
                                          FROM associations
                                          WHERE lat IS NOT NULL
                                            AND lon IS NOT NULL LIMIT 5
                                          """)).fetchall()

        logger.info("\nSample associations with coordinates:")
        for name, lat, lon in sample_assocs:
            logger.info(f"  {name}: ({lat}, {lon})")


def main():
    """Load full datasets into the database."""
    logger.info("Loading full datasets into SponsorMatch AI database...")

    engine = get_engine()

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Load associations
    if not load_full_associations(engine):
        logger.error("Failed to load associations")
        return

    # Load companies
    if not load_full_companies(engine):
        logger.error("Failed to load companies")
        return

    # Verify the data
    verify_data(engine)

    logger.info("\n✅ Full dataset loading complete!")
    logger.info("\nNext steps:")
    logger.info("1. Retrain the clustering models: python golden_goal/utils/train_clustering_models.py")
    logger.info("2. Run the app: streamlit run golden_goal/ui/simple_app.py")


if __name__ == "__main__":
    main()
