#!/usr/bin/env python3
"""
Transfer size_bucket data from associations_prepared.csv to associations_geocoded.csv
This will update associations_geocoded.csv to include the size information.
"""
import pandas as pd
from pathlib import Path
import sys


def transfer_sizes():
    """Transfer size_bucket from associations_prepared to associations_geocoded"""

    # File paths
    geocoded_path = Path("data/associations_geocoded.csv")
    prepared_path = Path("data/associations_prepared.csv")

    # Check if files exist
    if not geocoded_path.exists():
        print("❌ associations_geocoded.csv not found!")
        return False

    if not prepared_path.exists():
        print("❌ associations_prepared.csv not found!")
        return False

    # Load both files
    print("📂 Loading CSV files...")
    geocoded_df = pd.read_csv(geocoded_path)
    prepared_df = pd.read_csv(prepared_path)

    print(f"  - associations_geocoded.csv: {len(geocoded_df)} rows")
    print(f"  - associations_prepared.csv: {len(prepared_df)} rows")

    # Create a mapping from name to size_bucket
    name_to_size = dict(zip(prepared_df['name'], prepared_df['size_bucket']))

    # Check how many matches we can find
    matches_found = 0
    unmatched = []

    for idx, row in geocoded_df.iterrows():
        name = row['name']
        if name in name_to_size:
            matches_found += 1
        else:
            unmatched.append(name)

    print(f"\n📊 Matching statistics:")
    print(f"  - Matches found: {matches_found}/{len(geocoded_df)}")
    print(f"  - Unmatched: {len(unmatched)}")

    if unmatched and len(unmatched) <= 10:
        print(f"\n⚠️ Unmatched associations:")
        for name in unmatched[:10]:
            print(f"    - {name}")

    # Add size_bucket column
    geocoded_df['size_bucket'] = geocoded_df['name'].map(name_to_size)

    # For unmatched associations, set default to 'medium'
    geocoded_df['size_bucket'] = geocoded_df['size_bucket'].fillna('medium')

    # Show size distribution
    print(f"\n📈 Size distribution in updated file:")
    size_counts = geocoded_df['size_bucket'].value_counts()
    for size, count in size_counts.items():
        print(f"  - {size}: {count}")

    # Backup original file
    backup_path = geocoded_path.with_suffix('.csv.backup')
    print(f"\n💾 Creating backup: {backup_path}")
    geocoded_df_original = pd.read_csv(geocoded_path)
    geocoded_df_original.to_csv(backup_path, index=False)

    # Save updated file
    print(f"💾 Saving updated associations_geocoded.csv...")
    geocoded_df.to_csv(geocoded_path, index=False)

    print("\n✅ Successfully transferred size_bucket data!")
    print(f"   associations_geocoded.csv now has {len(geocoded_df.columns)} columns")
    print(f"   New columns: {list(geocoded_df.columns)}")

    return True


def verify_update():
    """Verify the update worked correctly"""
    geocoded_path = Path("data/associations_geocoded.csv")

    if not geocoded_path.exists():
        print("❌ File not found!")
        return

    df = pd.read_csv(geocoded_path)

    print("\n🔍 Verification:")
    print(f"  - Total rows: {len(df)}")
    print(f"  - Has size_bucket column: {'size_bucket' in df.columns}")

    if 'size_bucket' in df.columns:
        print(f"  - Size distribution: {df['size_bucket'].value_counts().to_dict()}")

        # Show some examples
        print("\n📋 Sample data:")
        sample = df[['name', 'size_bucket', 'latitude', 'longitude']].head(5)
        print(sample.to_string(index=False))


def main():
    print("🔄 Transfer Size Bucket Data Tool\n")

    # Ask for confirmation
    print("This will:")
    print("1. Add size_bucket column to associations_geocoded.csv")
    print("2. Create a backup of the original file")
    print("3. Map sizes from associations_prepared.csv by matching names")
    print("4. Set unmatched associations to 'medium' size")

    response = input("\nProceed? (y/n): ")

    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    # Transfer sizes
    if transfer_sizes():
        verify_update()
        print("\n🎉 Done! The app will now show correct sizes without code changes.")
    else:
        print("\n❌ Transfer failed!")


if __name__ == "__main__":
    main()
