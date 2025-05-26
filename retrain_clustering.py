# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
Retrain clustering models with consistent features.
Run this to fix the feature dimension mismatch.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import KMeans

from sponsor_match.core.db import get_engine


def size_bucket_to_numeric(size_bucket):
    """Convert size bucket to numeric value."""
    mapping = {"small": 0, "medium": 1, "large": 2}
    return mapping.get(size_bucket, 1)


def retrain_models():
    """Retrain clustering models with correct features."""

    # Load associations data
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql("""
            SELECT lat, lon, size_bucket, member_count 
            FROM associations 
            WHERE lat IS NOT NULL AND lon IS NOT NULL
        """, conn)

    if df.empty:
        print("No association data found!")
        return

    # Convert size_bucket to numeric
    df['size_numeric'] = df['size_bucket'].apply(size_bucket_to_numeric)

    # Prepare features - using lat, lon, size_numeric (3 features)
    features = df[['lat', 'lon', 'size_numeric']].values

    # Create models directory
    models_dir = Path(__file__).resolve().parents[0] / "models"
    models_dir.mkdir(exist_ok=True)

    # Train default model (for small/medium)
    default_data = df[df['size_bucket'].isin(['small', 'medium'])]

    if len(default_data) > 5:
        default_features = default_data[['lat', 'lon', 'size_numeric']].values
        default_kmeans = KMeans(n_clusters=min(5, len(default_data)), random_state=42)
        default_kmeans.fit(default_features)
        joblib.dump(default_kmeans, models_dir / "kmeans.joblib")
        print(f"Saved default model with {len(default_data)} associations")
    else:
        # Create fallback model with all data
        default_kmeans = KMeans(n_clusters=min(3, len(df)), random_state=42)
        default_kmeans.fit(features)
        joblib.dump(default_kmeans, models_dir / "kmeans.joblib")
        print(f"Saved fallback default model with {len(df)} associations")

    # Train large model
    large_data = df[df['size_bucket'] == 'large']
    if len(large_data) > 3:
        large_features = large_data[['lat', 'lon', 'size_numeric']].values
        large_kmeans = KMeans(n_clusters=min(3, len(large_data)), random_state=42)
        large_kmeans.fit(large_features)
        joblib.dump(large_kmeans, models_dir / "kmeans_large.joblib")
        print(f"Saved large model with {len(large_data)} associations")
    else:
        # Use default model for large too
        joblib.dump(default_kmeans, models_dir / "kmeans_large.joblib")
        print("Using default model for large clusters (insufficient large associations)")


if __name__ == "__main__":
    retrain_models()
    print("Models retrained successfully!")