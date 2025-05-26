# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
Enrich association data with size categories using multiple strategies.
"""
import numpy as np
import pandas as pd


def categorize_by_name_patterns(name):
    """
    Use name patterns to infer association size.
    Major clubs often have simpler, well-known names.
    """
    if pd.isna(name):
        return 'medium'
    
    name_upper = name.upper()
    
    # Well-known large associations in Gothenburg
    large_patterns = [
        'IFK GÖTEBORG', 'GAIS', 'ÖRGRYTE', 'HÄCKEN',
        'FRÖLUNDA', 'INDIEN', 'GÖTEBORG FC'
    ]
    
    for pattern in large_patterns:
        if pattern in name_upper:
            return 'large'
    
    # Youth or junior associations tend to be smaller
    if any(word in name_upper for word in ['UNGDOM', 'JUNIOR', 'POJK', 'FLICK', 'U21', 'U19']):
        return 'small'
    
    # Company sports associations are usually medium
    if 'FÖRETAG' in name_upper or 'AB' in name_upper:
        return 'medium'
    
    # Local neighborhood associations tend to be small
    if any(word in name_upper for word in ['BYALAG', 'LOKALFÖRENING', 'KVARTER']):
        return 'small'
    
    return 'medium'  # Default

def categorize_by_geography(lat, lon, district):
    """
    Use geographic location as a proxy for size.
    Central urban associations tend to be larger.
    """
    if pd.isna(lat) or pd.isna(lon):
        return 'medium'
    
    # Distance from Gothenburg city center
    city_center = (57.7089, 11.9746)
    distance = np.sqrt((lat - city_center[0])**2 + (lon - city_center[1])**2)
    
    # Convert to approximate kilometers (1 degree ≈ 111 km at this latitude)
    distance_km = distance * 111
    
    if distance_km < 5:  # Central city
        return 'large'
    elif distance_km < 15:  # Greater urban area
        return 'medium'
    else:  # Suburban/rural
        return 'small'

def create_size_distribution(df, method='hybrid'):
    """
    Create a realistic size distribution.
    In reality, most associations are small to medium.
    """
    n = len(df)
    
    if method == 'realistic':
        # Realistic distribution based on typical patterns
        # 60% small, 30% medium, 10% large
        sizes = np.random.choice(
            ['small', 'medium', 'large'],
            size=n,
            p=[0.6, 0.3, 0.1]
        )
    elif method == 'hybrid':
        # Combine multiple indicators
        sizes = []
        for _, row in df.iterrows():
            name_size = categorize_by_name_patterns(row.get('Namn', ''))
            geo_size = categorize_by_geography(
                row.get('lat'), 
                row.get('lon'), 
                row.get('district')
            )
            
            # Combine assessments with weighted logic
            if name_size == 'large' or geo_size == 'large':
                sizes.append('large')
            elif name_size == 'small' and geo_size == 'small':
                sizes.append('small')
            else:
                sizes.append('medium')
    else:
        # Simple random
        sizes = ['medium'] * n
    
    return sizes

def prepare_associations_for_clustering():
    """
    Prepare associations data with intelligent size categorization.
    """
    print("Loading associations data...")
    df = pd.read_csv('data/associations_geocoded.csv')
    
    print(f"Processing {len(df)} associations...")
    
    # Add size categories using hybrid method
    df['size_bucket'] = create_size_distribution(df, method='hybrid')
    
    # Ensure proper column names for clustering
    if 'lat' in df.columns and 'latitude' not in df.columns:
        df['latitude'] = df['lat']
    if 'lon' in df.columns and 'longitude' not in df.columns:
        df['longitude'] = df['lon']
    
    # Add association ID if missing
    if 'id' not in df.columns:
        df['id'] = range(1, len(df) + 1)
    
    # Report distribution
    print("\nSize distribution:")
    print(df['size_bucket'].value_counts())
    print(f"\nSample categorizations:")
    sample = df[['Namn', 'size_bucket']].head(10)
    for _, row in sample.iterrows():
        name = row['Namn'][:40] if len(row['Namn']) > 40 else row['Namn']
        print(f"  {name:<40} -> {row['size_bucket']}")
    
    # Save prepared data
    output_path = 'data/associations_geocoded_prepared.csv'
    df.to_csv(output_path, index=False)
    print(f"\nSaved prepared data to {output_path}")
    
    return df

if __name__ == "__main__":
    prepare_associations_for_clustering()
