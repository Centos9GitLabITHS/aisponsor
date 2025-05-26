#!/usr/bin/env python3
"""
sponsor_match/ml/pipeline.py

Complete ML Pipeline with geocoded data support, proper scoring normalization,
and enhanced clustering capabilities. This replaces the existing pipeline.py
with full support for the new geocoded CSV files.
"""

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from sponsor_match.core.db import get_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model paths
MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DEFAULT_KMEANS = MODELS_DIR / "kmeans.joblib"
LARGE_KMEANS = MODELS_DIR / "kmeans_large.joblib"

# Data paths for geocoded files
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ASSOCIATIONS_GEOCODED = DATA_DIR / "associations_geocoded.csv"
COMPANIES_GEOCODED = DATA_DIR / "companies_geocoded.csv"


@dataclass
class ScoringWeights:
    """Weights for different scoring components. Must sum to 1.0."""
    distance: float = 0.4
    size_match: float = 0.3
    cluster_match: float = 0.2
    industry_affinity: float = 0.1

    def __post_init__(self):
        """Validate that weights sum to 1.0."""
        total = self.distance + self.size_match + self.cluster_match + self.industry_affinity
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance (km) between two points.

    This function calculates the shortest distance between two points on Earth's
    surface, accounting for the spherical nature of the planet.
    """
    R = 6371.0  # Earth's radius in kilometers

    # Convert degrees to radians
    phi1, lam1, phi2, lam2 = map(math.radians, (lat1, lon1, lat2, lon2))

    # Haversine formula
    dphi = phi2 - phi1
    dlam = lam2 - lam1
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)

    return 2 * R * math.asin(math.sqrt(a))


def size_bucket_to_numeric(size_bucket: str) -> int:
    """Convert size bucket to numeric value for calculations."""
    mapping = {"small": 0, "medium": 1, "large": 2}
    return mapping.get(size_bucket, 1)


def validate_coordinates(lat: float, lon: float, entity_name: str = "") -> bool:
    """
    Validate that coordinates are within valid ranges.

    Returns True if valid, logs warning and returns False if invalid.
    """
    if lat is None or lon is None:
        logger.warning(f"Missing coordinates for {entity_name}")
        return False

    if not (-90 <= lat <= 90):
        logger.warning(f"Invalid latitude {lat} for {entity_name}")
        return False

    if not (-180 <= lon <= 180):
        logger.warning(f"Invalid longitude {lon} for {entity_name}")
        return False

    return True


def load_geocoded_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load geocoded CSV files with validation and fallback to database if needed.

    Returns tuple of (associations_df, companies_df) with validated coordinates.
    """
    try:
        # Try loading geocoded CSV files first
        if ASSOCIATIONS_GEOCODED.exists() and COMPANIES_GEOCODED.exists():
            logger.info("Loading geocoded CSV files...")

            # Load associations
            associations_df = pd.read_csv(ASSOCIATIONS_GEOCODED)
            # Rename columns if needed for consistency
            if 'lat' in associations_df.columns:
                associations_df = associations_df.rename(columns={'lat': 'latitude', 'lon': 'longitude'})

            # Load companies
            companies_df = pd.read_csv(COMPANIES_GEOCODED)
            if 'lat' in companies_df.columns:
                companies_df = companies_df.rename(columns={'lat': 'latitude', 'lon': 'longitude'})

            # Validate and filter
            valid_assoc = associations_df.apply(
                lambda row: validate_coordinates(row['latitude'], row['longitude'], row['name']),
                axis=1
            )
            valid_comp = companies_df.apply(
                lambda row: validate_coordinates(row['latitude'], row['longitude'], row['name']),
                axis=1
            )

            associations_df = associations_df[valid_assoc]
            companies_df = companies_df[valid_comp]

            logger.info(
                f"Loaded {len(associations_df)} associations and {len(companies_df)} companies from geocoded CSVs")
            return associations_df, companies_df

    except Exception as e:
        logger.warning(f"Failed to load geocoded CSVs: {e}. Falling back to database...")

    # Fallback to database
    engine = get_engine()
    with engine.connect() as conn:
        associations_df = pd.read_sql(
            "SELECT * FROM associations WHERE lat IS NOT NULL AND lon IS NOT NULL",
            conn
        )
        companies_df = pd.read_sql(
            "SELECT * FROM companies WHERE lat IS NOT NULL AND lon IS NOT NULL",
            conn
        )

    return associations_df, companies_df


def load_models() -> Optional[Dict[str, any]]:
    """Load clustering models with enhanced error handling."""
    try:
        models = {}

        if DEFAULT_KMEANS.exists():
            model_data = joblib.load(DEFAULT_KMEANS)
            # Handle both old format (direct model) and new format (dict with scaler)
            if isinstance(model_data, dict):
                models["default"] = model_data
            else:
                # Legacy format - wrap in dict
                models["default"] = {
                    'kmeans': model_data,
                    'scaler': StandardScaler()  # Create default scaler
                }

        if LARGE_KMEANS.exists():
            model_data = joblib.load(LARGE_KMEANS)
            if isinstance(model_data, dict):
                models["large"] = model_data
            else:
                models["large"] = {
                    'kmeans': model_data,
                    'scaler': StandardScaler()
                }

        return models if models else None

    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        return None


def calculate_distance_score(distance_km: float, max_distance: float = 50.0) -> float:
    """
    Calculate normalized distance score (1.0 = very close, 0.0 = far away).

    Uses exponential decay to prioritize closer matches.
    """
    if distance_km >= max_distance:
        return 0.0

    # Exponential decay with configurable rate
    decay_rate = 2.0  # Adjust to control how quickly score drops with distance
    return math.exp(-decay_rate * distance_km / max_distance)


def calculate_size_match_score(assoc_size: str, comp_size: str) -> float:
    """
    Calculate size compatibility score.

    Perfect match = 1.0, adjacent size = 0.5, opposite ends = 0.0
    """
    size_map = {"small": 0, "medium": 1, "large": 2}

    assoc_val = size_map.get(assoc_size, 1)
    comp_val = size_map.get(comp_size, 1)

    diff = abs(assoc_val - comp_val)

    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.5
    else:
        return 0.0


def calculate_industry_affinity(association: pd.Series, company: pd.Series) -> float:
    """
    Calculate industry-association affinity score.

    This is a simplified version - in production, you'd want a more sophisticated
    mapping based on historical sponsorship data.
    """
    # Simple rule-based affinities
    affinities = {
        ('sports', 'retail'): 0.8,
        ('sports', 'finance'): 0.7,
        ('sports', 'technology'): 0.6,
        ('cultural', 'finance'): 0.9,
        ('cultural', 'retail'): 0.7,
        ('youth', 'education'): 0.9,
        ('youth', 'technology'): 0.8,
    }

    # Extract categories (simplified - you'd parse from actual data)
    assoc_type = 'sports'  # Default for this implementation
    comp_industry = company.get('industry', 'other').lower()

    return affinities.get((assoc_type, comp_industry), 0.5)


def predict_cluster_safe(model_data: Dict, features: List[float]) -> Optional[int]:
    """
    Safely predict cluster with proper feature handling and validation.
    """
    try:
        if 'scaler' in model_data and 'kmeans' in model_data:
            # Scale features
            features_scaled = model_data['scaler'].transform([features[:2]])  # Use only lat/lon
            # Predict cluster
            return model_data['kmeans'].predict(features_scaled)[0]
        elif hasattr(model_data, 'predict'):
            # Legacy format
            return model_data.predict([features[:2]])[0]
    except Exception as e:
        logger.debug(f"Cluster prediction failed: {e}")
        return None


def score_and_rank(
        association_id: int,
        bucket: str,
        max_distance: float = 50.0,
        top_n: int = 10,
        weights: Optional[ScoringWeights] = None
) -> List[Dict]:
    """
    Score and rank potential sponsors with proper normalization and validation.

    This is the main function that orchestrates the matching process:
    1. Loads association and company data
    2. Calculates multiple scoring components
    3. Combines scores with validated weights
    4. Returns top N matches with normalized scores
    """
    if weights is None:
        weights = ScoringWeights()

    # Load data (prefer geocoded CSVs)
    associations_df, companies_df = load_geocoded_data()

    # Find the target association
    if 'id' in associations_df.columns:
        assoc_mask = associations_df['id'] == association_id
    else:
        # Fallback for CSV data without ID column
        assoc_mask = associations_df.index == association_id

    if not assoc_mask.any():
        logger.warning(f"Association {association_id} not found")
        return []

    association = associations_df[assoc_mask].iloc[0]

    # Get association coordinates
    assoc_lat = association.get('latitude', association.get('lat'))
    assoc_lon = association.get('longitude', association.get('lon'))

    if not validate_coordinates(assoc_lat, assoc_lon, f"Association {association_id}"):
        return []

    # Load models for clustering
    models = load_models()
    assoc_cluster = None

    if models:
        model_key = "large" if bucket == "large" else "default"
        model = models.get(model_key)

        if model:
            assoc_features = [assoc_lat, assoc_lon]
            assoc_cluster = predict_cluster_safe(model, assoc_features)

    # Score each company
    recommendations = []

    for _, company in companies_df.iterrows():
        try:
            # Get company coordinates
            comp_lat = company.get('latitude', company.get('lat'))
            comp_lon = company.get('longitude', company.get('lon'))

            if not validate_coordinates(comp_lat, comp_lon, company.get('name', 'Unknown')):
                continue

            # Calculate distance
            distance_km = haversine(assoc_lat, assoc_lon, comp_lat, comp_lon)

            # Skip if beyond max distance
            if distance_km > max_distance:
                continue

            # Calculate component scores
            distance_score = calculate_distance_score(distance_km, max_distance)
            size_score = calculate_size_match_score(
                association.get('size_bucket', bucket),
                company.get('size_bucket', 'medium')
            )

            # Cluster matching score
            cluster_score = 0.5  # Default neutral score
            if models and assoc_cluster is not None:
                model_key = "large" if company.get('size_bucket') == "large" else "default"
                model = models.get(model_key)
                if model:
                    comp_features = [comp_lat, comp_lon]
                    comp_cluster = predict_cluster_safe(model, comp_features)
                    if comp_cluster is not None and comp_cluster == assoc_cluster:
                        cluster_score = 1.0

            # Industry affinity
            industry_score = calculate_industry_affinity(association, company)

            # Combine scores with validated weights
            final_score = (
                    weights.distance * distance_score +
                    weights.size_match * size_score +
                    weights.cluster_match * cluster_score +
                    weights.industry_affinity * industry_score
            )

            # Ensure score is in valid range [0, 1]
            final_score = np.clip(final_score, 0.0, 1.0)

            recommendations.append({
                "id": int(company.get('id', 0)),
                "name": str(company.get('name', 'Unknown Company')),
                "lat": float(comp_lat),
                "lon": float(comp_lon),
                "distance": round(distance_km, 2),
                "score": round(final_score, 4),
                "components": {
                    "distance_score": round(distance_score, 3),
                    "size_score": round(size_score, 3),
                    "cluster_score": round(cluster_score, 3),
                    "industry_score": round(industry_score, 3)
                }
            })

        except Exception as e:
            logger.error(f"Error processing company {company.get('name', 'unknown')}: {e}")
            continue

    # Sort by score and return top N
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations[:top_n]


def recalibrate_models():
    """
    Recalibrate clustering models using geocoded data.

    This function should be run periodically to update models with new data.
    """
    logger.info("Recalibrating models with geocoded data...")

    # Load geocoded data
    associations_df, companies_df = load_geocoded_data()

    # Combine all entities for clustering
    all_coords = pd.concat([
        associations_df[['latitude', 'longitude', 'size_bucket']].rename(
            columns={'latitude': 'lat', 'longitude': 'lon'}
        ),
        companies_df[['latitude', 'longitude', 'size_bucket']].rename(
            columns={'latitude': 'lat', 'longitude': 'lon'}
        )
    ], ignore_index=True)

    # Train separate models for different size buckets
    from sklearn.cluster import KMeans

    for bucket, model_path in [("default", DEFAULT_KMEANS), ("large", LARGE_KMEANS)]:
        if bucket == "default":
            data = all_coords[all_coords['size_bucket'].isin(['small', 'medium'])]
        else:
            data = all_coords[all_coords['size_bucket'] == 'large']

        if len(data) < 5:
            logger.warning(f"Insufficient data for {bucket} model")
            continue

        # Prepare features
        features = data[['lat', 'lon']].values

        # Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Train KMeans
        n_clusters = min(10, len(data) // 5)  # Adaptive cluster count
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(features_scaled)

        # Save model with scaler
        model_data = {
            'kmeans': kmeans,
            'scaler': scaler,
            'n_features': 2,
            'n_clusters': n_clusters
        }

        joblib.dump(model_data, model_path)
        logger.info(f"Saved {bucket} model with {n_clusters} clusters")


# Main entry point for testing
if __name__ == "__main__":
    # Test the pipeline
    results = score_and_rank(
        association_id=1,
        bucket="medium",
        max_distance=50,
        top_n=5
    )

    print(f"Found {len(results)} recommendations:")
    for i, rec in enumerate(results, 1):
        print(f"{i}. {rec['name']} - Score: {rec['score'] * 100:.1f}% - Distance: {rec['distance']}km")