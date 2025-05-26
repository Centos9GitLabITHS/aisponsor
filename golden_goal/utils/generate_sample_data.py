# Module to generate realistic sample data for SponsorMatch AI
# Detailed comments have been inserted in British English.

#!/usr/bin/env python3
"""Generate realistic sample data for SponsorMatch AI."""

# Standard library or third-party import
import random
# Standard library or third-party import
from pathlib import Path

# Standard library or third-party import
import numpy as np
# Standard library or third-party import
import pandas as pd
# Standard library or third-party import
from faker import Faker

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)
fake = Faker()
Faker.seed(42)


# Definition of function 'generate_sample_companies': explains purpose and parameters
def generate_sample_companies(n=50):
    """Generate realistic Swedish companies."""
    companies = []

    # Swedish company types and their characteristics
    industries = {
        'Technology': {'revenue_range': (10000, 500000), 'employee_range': (10, 200)},
        'Manufacturing': {'revenue_range': (50000, 1000000), 'employee_range': (50, 500)},
        'Finance': {'revenue_range': (25000, 750000), 'employee_range': (20, 300)},
        'Healthcare': {'revenue_range': (15000, 400000), 'employee_range': (15, 150)},
        'Retail': {'revenue_range': (20000, 300000), 'employee_range': (25, 100)},
    }

    # Swedish cities with coordinates
    cities = [
        ('Göteborg', 57.7089, 11.9746),
        ('Stockholm', 59.3293, 18.0686),
        ('Malmö', 55.6050, 13.0038),
        ('Uppsala', 59.8586, 17.6389),
        ('Linköping', 58.4108, 15.6214)
    ]

    for i in range(n):
        industry = random.choice(list(industries.keys()))
        city, base_lat, base_lon = random.choice(cities)

        # Add some randomness to coordinates
        lat = base_lat + random.uniform(-0.1, 0.1)
        lon = base_lon + random.uniform(-0.1, 0.1)

        revenue = random.randint(*industries[industry]['revenue_range'])
        employees = random.randint(*industries[industry]['employee_range'])

        # Determine size bucket
        if revenue < 50000:
            size_bucket = 'small'
        elif revenue < 250000:
            size_bucket = 'medium'
        else:
            size_bucket = 'large'

        company = {
            'id': i + 1,
            'orgnr': f"{random.randint(100000, 999999)}-{random.randint(1000, 9999)}",
            'name': f"{fake.company()} {random.choice(['AB', 'Ltd', 'Group'])}",
            'revenue_ksek': revenue,
            'employees': employees,
            'year': random.randint(2020, 2024),
            'size_bucket': size_bucket,
            'industry': industry,
            'lat': round(lat, 6),
            'lon': round(lon, 6)
        }
        companies.append(company)

    return pd.DataFrame(companies)


# Definition of function 'generate_sample_associations': explains purpose and parameters
def generate_sample_associations(n=30):
    """Generate realistic Swedish sports associations."""
    associations = []

    sports = ['Fotboll', 'Ishockey', 'Bandy', 'Handboll', 'Basket', 'Innebandy']
    cities = [
        ('Göteborg', 57.7089, 11.9746),
        ('Mölndal', 57.6554, 12.0134),
        ('Partille', 57.7394, 12.1065),
        ('Lerum', 57.7706, 12.2694),
        ('Kungälv', 57.8700, 11.9800)
    ]

    for i in range(n):
        sport = random.choice(sports)
        city, base_lat, base_lon = random.choice(cities)

        lat = base_lat + random.uniform(-0.05, 0.05)
        lon = base_lon + random.uniform(-0.05, 0.05)

        members = random.randint(50, 800)

        # Size bucket based on members
        if members < 150:
            size_bucket = 'small'
        elif members < 400:
            size_bucket = 'medium'
        else:
            size_bucket = 'large'

        association = {
            'id': i + 1,
            'name': f"{city} {sport}klub",
            'member_count': members,
            'address': f"{fake.street_address()}, {city}",
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'size_bucket': size_bucket,
            'founded_year': random.randint(1950, 2020)
        }
        associations.append(association)

    return pd.DataFrame(associations)


# Definition of function 'main': explains purpose and parameters
def main():
    """Generate and save sample data."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)

    # Generate data
    print("Generating sample companies...")
    companies = generate_sample_companies(50)
    companies.to_csv(data_dir / "sample_companies.csv", index=False)
    print(f"Generated {len(companies)} companies")

    print("Generating sample associations...")
    associations = generate_sample_associations(30)
    associations.to_csv(data_dir / "sample_associations.csv", index=False)
    print(f"Generated {len(associations)} associations")

    print(f"Data saved to {data_dir}")


# Entry point check: script execution starts here when run directly
if __name__ == "__main__":
    main()