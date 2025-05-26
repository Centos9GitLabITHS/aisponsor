#!/usr/bin/env python3
"""
quick_train_models.py - Quick script to train/retrain ML models
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text

from golden_goal.core.db import get_engine


def train_models():
    """Train clustering models from scratch."""
    print("Training ML models...")

    engine = get_engine()

    # Create models directory
    models_dir = Path(__file__).parent.parent / "golden_goal" / "models"
    models_dir.mkdir(exist_ok=True, parents=True)
    print(f"Models directory: {models_dir}")

    with engine.connect() as conn:
        # Get all locations
        all_locations = conn.execute(text("""
                                          SELECT lat, lon, size_bucket
                                          FROM (SELECT lat, lon, size_bucket
                                                FROM associations
                                                WHERE lat IS NOT NULL
                                                  AND lon IS NOT NULL
                                                UNION ALL
                                                SELECT lat, lon, size_bucket
                                                FROM companies
                                                WHERE lat IS NOT NULL
                                                  AND lon IS NOT NULL) AS combined
                                          """)).fetchall()

    print(f"Found {len(all_locations)} locations")

    # Separate by size
    small_medium = [(lat, lon) for lat, lon, size in all_locations if size in ['small', 'medium']]
    large = [(lat, lon) for lat, lon, size in all_locations if size == 'large']

    # Train default model (small/medium)
    if len(small_medium) > 5:
        print(f"\nTraining default model with {len(small_medium)} points...")
        X = np.array(small_medium)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        n_clusters = min(5, len(small_medium) // 10)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(X_scaled)

        model_data = {
            'kmeans': kmeans,
            'scaler': scaler,
            'features': ['lat', 'lon'],
            'n_features': 2
        }

        path = models_dir / "kmeans.joblib"
        joblib.dump(model_data, path)
        print(f"✓ Saved default model to {path}")

    # Train large model
    if len(large) > 3:
        print(f"\nTraining large model with {len(large)} points...")
        X = np.array(large)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        n_clusters = min(3, len(large) // 5)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(X_scaled)

        model_data = {
            'kmeans': kmeans,
            'scaler': scaler,
            'features': ['lat', 'lon'],
            'n_features': 2
        }

        path = models_dir / "kmeans_large.joblib"
        joblib.dump(model_data, path)
        print(f"✓ Saved large model to {path}")

    print("\nModels trained successfully!")

    # Test loading
    from golden_goal.ml.pipeline import load_models
    models = load_models()
    print(f"\nVerification: Loaded {len(models)} models: {list(models.keys())}")


if __name__ == "__main__":
    train_models()
