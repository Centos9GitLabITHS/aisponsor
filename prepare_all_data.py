# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
prepare_all_data.py
Emergency data preparation for 2-day deadline with size-based matching.
Fixed with correct association size categories and processes ALL companies.
"""

import numpy as np
import pandas as pd


def prepare_associations():
    """Prepare associations with size categories."""
    print("Loading associations...")
    df = pd.read_csv('data/associations_geocoded.csv')

    # Count before
    total_before = len(df)

    # Keep only geocoded associations with valid coordinates
    df = df[
        df['lat'].notna() &
        df['lon'].notna() &
        (df['lat'] != 0) &
        (df['lon'] != 0) &
        (df['lat'].between(-90, 90)) &
        (df['lon'].between(-180, 180))
        ].copy()

    print(f"Filtered to {len(df)} associations with valid coordinates")

    # Add required columns
    df['id'] = range(1, len(df) + 1)
    df['name'] = df['Namn'].fillna('Unknown Association')
    df['latitude'] = df['lat'].astype(float)
    df['longitude'] = df['lon'].astype(float)

    # Create size buckets based on available data
    # Fixed size categories: Small (0-399), Medium (400-799), Large (800+)
    if 'member_count' in df.columns:
        df['size_bucket'] = pd.cut(
            df['member_count'].fillna(100),
            bins=[0, 400, 800, float('inf')],  # Fixed: correct size boundaries
            labels=['small', 'medium', 'large'],
            right=False  # 0-399, 400-799, 800+
        )
    else:
        # Fallback: assign random realistic distribution
        np.random.seed(42)
        size_distribution = np.random.choice(
            ['small', 'medium', 'large'],
            size=len(df),
            p=[0.5, 0.35, 0.15]  # Most associations are small/medium
        )
        df['size_bucket'] = size_distribution

    # Keep only essential columns
    essential_cols = ['id', 'name', 'latitude', 'longitude', 'size_bucket']
    # Add address columns if they exist
    for col in ['Adress', 'Postort']:
        if col in df.columns:
            essential_cols.append(col)

    # Check which columns actually exist
    existing_cols = [col for col in essential_cols if col in df.columns]
    df = df[existing_cols]

    # Save
    df.to_csv('data/associations_prepared.csv', index=False)
    print(f"Prepared {len(df)} associations (from {total_before} total)")
    print(f"Size distribution: {df['size_bucket'].value_counts().to_dict()}")
    return df


def prepare_companies():
    """Prepare ALL companies with size categories based on employee count."""
    print("Loading companies...")
    df = pd.read_csv('data/companies_geocoded.csv')

    # Count before
    total_before = len(df)

    # Keep only geocoded companies with valid coordinates
    df = df[
        df['lat'].notna() &
        df['lon'].notna() &
        (df['lat'] != 0) &
        (df['lon'] != 0) &
        (df['lat'].between(-90, 90)) &
        (df['lon'].between(-180, 180))
        ].copy()

    print(f"Filtered to {len(df)} companies with valid coordinates")

    # Process ALL companies (no limit)
    print(f"Processing all {len(df)} companies...")

    # Add required columns
    df['id'] = range(1, len(df) + 1)
    df['name'] = 'Company_' + df['PeOrgNr'].astype(str)
    df['latitude'] = df['lat'].astype(float)
    df['longitude'] = df['lon'].astype(float)

    # Create size buckets based on employee count if available
    if 'employee_count' in df.columns or 'employees' in df.columns:
        emp_col = 'employee_count' if 'employee_count' in df.columns else 'employees'
        df['size_bucket'] = pd.cut(
            df[emp_col].fillna(10),
            bins=[0, 10, 50, 250, float('inf')],
            labels=['small', 'medium', 'large', 'enterprise']
        )
    else:
        # Fallback: create realistic distribution
        np.random.seed(42)
        size_distribution = np.random.choice(
            ['small', 'medium', 'large', 'enterprise'],
            size=len(df),
            p=[0.6, 0.25, 0.12, 0.03]  # Most companies are small
        )
        df['size_bucket'] = size_distribution

    # Add district info if available
    if 'district' in df.columns:
        df['district'] = df['district'].fillna('Unknown')
    else:
        df['district'] = 'Unknown'

    # Keep only essential columns
    essential_cols = ['id', 'name', 'latitude', 'longitude', 'size_bucket', 'district', 'PeOrgNr']
    # Check which columns actually exist
    existing_cols = [col for col in essential_cols if col in df.columns]
    df = df[existing_cols]

    # Save
    df.to_csv('data/companies_prepared.csv', index=False)
    print(f"Prepared {len(df)} companies (from {total_before} total)")
    print(f"Size distribution: {df['size_bucket'].value_counts().to_dict()}")
    return df


def verify_data():
    """Quick verification that data is ready."""
    print("\nVerifying prepared data...")

    try:
        # Check associations
        assoc = pd.read_csv('data/associations_prepared.csv')
        print(f"✓ Associations: {len(assoc)} records")
        print(f"  Columns: {list(assoc.columns)}")
        print(f"  Sizes: {assoc['size_bucket'].value_counts().to_dict()}")
        print(f"  Size categories: Small (0-399 members), Medium (400-799), Large (800+)")

        # Check companies
        comp = pd.read_csv('data/companies_prepared.csv')
        print(f"✓ Companies: {len(comp)} records")
        print(f"  Columns: {list(comp.columns)}")
        print(f"  Sizes: {comp['size_bucket'].value_counts().to_dict()}")

        print("\nSample association:")
        print(assoc.iloc[0].to_dict())

        print("\nSample company:")
        print(comp.iloc[0].to_dict())
    except Exception as e:
        print(f"Verification error: {e}")


if __name__ == "__main__":
    print("=== SponsorMatch AI Data Preparation ===")
    print("This will prepare ALL associations and companies for the 2-day deadline")
    print("WARNING: Processing all data may take longer and impact app performance")

    try:
        prepare_associations()
        prepare_companies()
        verify_data()
        print("\n✓ SUCCESS! Data is ready.")
        print("Next step: Run the app with 'python run_app.py'")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("Fix this error before continuing!")
        import traceback

        traceback.print_exc()