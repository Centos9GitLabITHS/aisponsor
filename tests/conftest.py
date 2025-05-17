# tests/conftest.py
from pathlib import Path

import pytest


# No sys.path manipulation needed when package is properly installed

@pytest.fixture
def test_data_dir():
    """Provides path to test data directory"""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_companies_df():
    """Creates a sample companies DataFrame for testing"""
    import pandas as pd
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Tech AB', 'Sport Goods Ltd', 'Local Market'],
        'size': ['medium', 'large', 'small'],
        'employees': [50, 200, 10],
        'turnover': [5000000, 20000000, 500000],
        'latitude': [57.7089, 57.7200, 57.6900],
        'longitude': [11.9746, 11.9800, 11.9600]
    })


@pytest.fixture
def real_companies_df():
    """Loads real company data from CSV file"""
    import pandas as pd
    csv_path = Path(__file__).parent.parent / "data" / "bolag_1_500_sorted_with_year.csv"

    df = pd.read_csv(csv_path)

    # Rename columns to match expected field names in the application
    column_mapping = {
        'Företagsnamn': 'name',
        'Postadress': 'address',
        'Omsättning (tkr)': 'revenue_ksek',
        'Anställda': 'employees',
        'År': 'year'
    }

    df = df.rename(columns=column_mapping)
    return df


@pytest.fixture
def real_clubs_df():
    """Loads real club data from CSV file"""
    import pandas as pd
    csv_path = Path(__file__).parent.parent / "data" / "associations_goteborg_with_coords.csv"
    return pd.read_csv(csv_path)
