#!/usr/bin/env python3
"""
train_clustering_models.py - Train clustering models with consistent features
"""

import logging
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text
from sponsor_match.core.db import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get proper project structure paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "sponsor_match" / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Feature configuration
FEATURES = ['lat', 'lon']  # Use only lat/lon for consistent features
N_CLUSTERS = {
    'default': 5,
    'large': 3
}


def load_data():
    """Load associations and companies from database."""
    engine = get_engine()

    with engine.connect() as conn:
        # Load associations
        associations = pd.read_sql(text("""
                                        SELECT id, name, lat, lon, size_bucket, member_count
                                        FROM associations
                                        WHERE lat IS NOT NULL
                                          AND lon IS NOT NULL
                                        """), conn)

        # Load companies
        companies = pd.read_sql(text("""
                                     SELECT id, name, lat, lon, size_bucket, revenue_ksek
                                     FROM companies
                                     WHERE lat IS NOT NULL
                                       AND lon IS NOT NULL
                                     """), conn)

    return associations, companies


def train_clustering_model(data, n_clusters, model_name):
    """Train a clustering model on the given data."""
    # Extract features
    X = data[FEATURES].values

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train KMeans
    kmeans = KMeans(n_clusters=min(n_clusters, len(data)), random_state=42)
    kmeans.fit(X_scaled)

    # Create model package with scaler
    model_package = {
        'scaler': scaler,
        'kmeans': kmeans,
        'features': FEATURES,
        'n_features': len(FEATURES)
    }

    # Save model
    model_path = MODELS_DIR / f"{model_name}.joblib"
    joblib.dump(model_package, model_path)
    logger.info(f"Saved {model_name} model to {model_path}")

    # Report cluster sizes
    labels = kmeans.labels_
    unique, counts = np.unique(labels, return_counts=True)
    for label, count in zip(unique, counts):
        logger.info(f"  Cluster {label}: {count} items")

    return model_package


def train_all_models():
    """Train all clustering models."""
    # Load data
    associations, companies = load_data()

    if associations.empty or companies.empty:
        logger.error("No data found. Run setup_database.py first.")
        return

    logger.info(f"Loaded {len(associations)} associations and {len(companies)} companies")

    # Combine all data for default model
    all_data = pd.concat([
        associations[FEATURES + ['size_bucket']],
        companies[FEATURES + ['size_bucket']]
    ], ignore_index=True)

    # Train default model (for small/medium entities)
    default_data = all_data[all_data['size_bucket'].isin(['small', 'medium'])]
    if len(default_data) > 0:
        logger.info(f"\nTraining default model with {len(default_data)} entities")
        train_clustering_model(default_data, N_CLUSTERS['default'], 'kmeans')

    # Train large model (for large entities)
    large_data = all_data[all_data['size_bucket'] == 'large']
    if len(large_data) > 0:
        logger.info(f"\nTraining large model with {len(large_data)} entities")
        train_clustering_model(large_data, N_CLUSTERS['large'], 'kmeans_large')

    # Create simplified models for backward compatibility
    create_backward_compatible_models()


def create_backward_compatible_models():
    """Create simplified models for backward compatibility."""
    # Load the model packages
    default_package = joblib.load(MODELS_DIR / "kmeans.joblib")
    large_package = joblib.load(MODELS_DIR / "kmeans_large.joblib")

    # Extract just the KMeans models
    joblib.dump(default_package['kmeans'], MODELS_DIR / "kmeans_simple.joblib")
    joblib.dump(large_package['kmeans'], MODELS_DIR / "kmeans_large_simple.joblib")

    logger.info("Created backward compatible models")


def test_models():
    """Test the trained models."""
    # Load a model
    model_path = MODELS_DIR / "kmeans.joblib"
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}. Run train_all_models() first.")
        return

    model_package = joblib.load(model_path)
    scaler = model_package['scaler']
    kmeans = model_package['kmeans']

    # Test points in Gothenburg area
    test_points = [
        [57.7089, 11.9746],  # Central Gothenburg
        [57.6523, 11.9118],  # Västra Frölunda
        [57.7654, 11.9457],  # Hisings Kärra
    ]

    logger.info("\nTesting model predictions:")
    for point in test_points:
        scaled_point = scaler.transform([point])
        cluster = kmeans.predict(scaled_point)[0]
        logger.info(f"  Point {point} -> Cluster {cluster}")


if __name__ == "__main__":
    train_all_models()
    test_models()
