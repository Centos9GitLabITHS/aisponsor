#!/usr/bin/env python3
"""
Quick script to verify your data files have the correct structure
Run from project root: python verify_data.py
"""
import pandas as pd
from pathlib import Path


def check_file(filepath, expected_cols):
    """Check if a file exists and has expected columns."""
    if not filepath.exists():
        print(f"❌ {filepath.name} - NOT FOUND")
        return False

    try:
        df = pd.read_csv(filepath)
        print(f"\n✅ {filepath.name}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")

        # Check for expected columns
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            print(f"   ⚠️  Missing columns: {missing}")

        # Show sample data for key columns
        for col in expected_cols:
            if col in df.columns:
                if col == 'size_bucket':
                    print(f"   {col} distribution: {df[col].value_counts().to_dict()}")
                elif col in ['name', 'company_name']:
                    sample = df[col].dropna().head(3).tolist()
                    print(f"   Sample {col}: {sample}")

        return True
    except Exception as e:
        print(f"❌ {filepath.name} - ERROR: {e}")
        return False


def main():
    data_dir = Path("data")

    print("=== Checking Association Files ===")

    # Check associations_prepared.csv (preferred)
    check_file(
        data_dir / "associations_prepared.csv",
        ['id', 'name', 'latitude', 'longitude', 'size_bucket']
    )

    # Check associations_geocoded.csv (fallback)
    check_file(
        data_dir / "associations_geocoded.csv",
        ['name', 'latitude', 'longitude', 'size_bucket']
    )

    print("\n=== Checking Company Files ===")

    # Check companies_complete.csv (preferred)
    check_file(
        data_dir / "companies_complete.csv",
        ['id', 'company_name', 'lat', 'lon', 'PeOrgNr']
    )

    # Check companies_prepared.csv (fallback)
    check_file(
        data_dir / "companies_prepared.csv",
        ['id', 'name', 'latitude', 'longitude']
    )


if __name__ == "__main__":
    main()
