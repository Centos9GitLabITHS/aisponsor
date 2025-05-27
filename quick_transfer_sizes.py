#!/usr/bin/env python3
"""
Quick script to automatically transfer sizes without prompts
Run: python quick_transfer_sizes.py
"""
import pandas as pd
from pathlib import Path

# Load both files
print("Loading files...")
geocoded = pd.read_csv("data/associations_geocoded.csv")
prepared = pd.read_csv("data/associations_prepared.csv")

# Create backup
print("Creating backup...")
geocoded.to_csv("data/associations_geocoded.csv.backup", index=False)

# Map sizes by name
name_to_size = dict(zip(prepared['name'], prepared['size_bucket']))
geocoded['size_bucket'] = geocoded['name'].map(name_to_size).fillna('medium')

# Add member_count if available
if 'member_count' in prepared.columns:
    name_to_members = dict(zip(prepared['name'], prepared['member_count']))
    geocoded['member_count'] = geocoded['name'].map(name_to_members).fillna(0)

# Save updated file
print("Saving updated file...")
geocoded.to_csv("data/associations_geocoded.csv", index=False)

# Show results
print(f"\n✅ Success! Added size_bucket to {len(geocoded)} associations")
print(f"Size distribution: {geocoded['size_bucket'].value_counts().to_dict()}")
print("\nNo code changes needed - the app will now show correct sizes!")
