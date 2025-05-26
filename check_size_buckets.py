#!/usr/bin/env python3
"""
check_size_buckets.py - Check what values are in the size_bucket column
"""

import pandas as pd
from pathlib import Path


def check_size_bucket_values():
    """Check unique values in size_bucket columns."""
    data_dir = Path("data")

    # Check associations
    print("🔍 Checking associations_prepared.csv...")
    assoc_df = pd.read_csv(data_dir / "associations_prepared.csv")
    print(f"Total rows: {len(assoc_df)}")
    print(f"Size bucket values: {assoc_df['size_bucket'].value_counts().to_dict()}")
    print(f"Null values: {assoc_df['size_bucket'].isna().sum()}")

    print("\n🔍 Checking companies_prepared.csv...")
    # Check first 1000 rows to find the issue
    comp_df = pd.read_csv(data_dir / "companies_prepared.csv", nrows=1000)
    print(f"Size bucket values in first 1000 rows: {comp_df['size_bucket'].value_counts().to_dict()}")
    print(f"Null values: {comp_df['size_bucket'].isna().sum()}")

    # Check for any non-standard values
    valid_values = ['small', 'medium', 'large']
    invalid_mask = ~comp_df['size_bucket'].isin(valid_values + [None])
    if invalid_mask.any():
        print(f"\n⚠️ Found invalid size_bucket values:")
        print(comp_df[invalid_mask][['id', 'name', 'size_bucket']].head(20))

    # Check around row 70 specifically
    print("\n🔍 Checking around row 70 (where error occurred)...")
    comp_df_specific = pd.read_csv(data_dir / "companies_prepared.csv", skiprows=range(1, 65), nrows=20)
    print(comp_df_specific[['id', 'size_bucket']].to_string())


if __name__ == "__main__":
    check_size_bucket_values()
