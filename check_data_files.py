#!/usr/bin/env python3
"""
check_data_files.py - Check which data files exist and their structure
"""

import pandas as pd
from pathlib import Path
import os

def check_data_directory():
    """Find and check all CSV files in the data directory."""
    print("🔍 Checking for data files...\n")
    
    # Look for data directory in various locations
    possible_dirs = [
        Path("data"),
        Path("sponsor_match/data"),
        Path(__file__).parent / "data",
        Path(__file__).parent / "sponsor_match" / "data"
    ]
    
    data_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists() and dir_path.is_dir():
            data_dir = dir_path
            break
    
    if not data_dir:
        print("❌ Could not find data directory!")
        print("Searched in:", [str(p) for p in possible_dirs])
        return
    
    print(f"✅ Found data directory: {data_dir.absolute()}\n")
    
    # List all CSV files
    csv_files = list(data_dir.glob("*.csv"))
    parquet_files = list(data_dir.glob("*.parquet"))
    
    all_files = csv_files + parquet_files
    
    if not all_files:
        print("❌ No data files found in directory!")
        return
    
    print(f"Found {len(all_files)} data files:\n")
    
    # Check each file
    for file_path in sorted(all_files):
        print(f"📄 {file_path.name}")
        print(f"   Size: {file_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        try:
            if file_path.suffix == '.csv':
                # Read first few rows
                df = pd.read_csv(file_path, nrows=5)
            else:  # parquet
                df = pd.read_parquet(file_path).head(5)
            
            print(f"   Rows: {len(pd.read_csv(file_path) if file_path.suffix == '.csv' else pd.read_parquet(file_path))}")
            print(f"   Columns: {list(df.columns)}")
            
            # Special checks for key files
            if 'associations' in file_path.name.lower() and 'prepared' in file_path.name:
                print("   ✨ This looks like the prepared associations file!")
                if 'lat' in df.columns or 'latitude' in df.columns:
                    print("   ✅ Has location data")
                if 'size_bucket' in df.columns:
                    print("   ✅ Has size buckets")
            
            if 'companies' in file_path.name.lower() and 'prepared' in file_path.name:
                print("   ✨ This looks like the prepared companies file!")
                if 'lat' in df.columns or 'latitude' in df.columns:
                    print("   ✅ Has location data")
                if 'size_bucket' in df.columns:
                    print("   ✅ Has size buckets")
            
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
        
        print()
    
    # Recommendations
    print("\n📊 Recommendations:")
    print("For loading the full dataset, use:")
    print("1. associations_prepared.csv - for associations")
    print("2. companies_prepared.csv - for companies")
    print("\nRun: python load_full_data.py")


if __name__ == "__main__":
    check_data_directory()
