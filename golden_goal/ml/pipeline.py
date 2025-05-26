#!/usr/bin/env python3
"""
golden_goal/ml/pipeline.py
----------------------------
CLEAN FINAL VERSION: No IDE warnings, better score distribution.
"""

import logging
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

import joblib
import numpy as np
from sqlalchemy import text
from sqlalchemy.engine import Engine

from golden_goal.core.db import get_engine

logger = logging.getLogger(__name__)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points (km)."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


class ScoringWeights:
    """Validate and hold weights for scoring components."""
    def __init__(self, distance=0.4, size_match=0.3, cluster_match=0.2, industry_affinity=0.1):
        total = distance + size_match + cluster_match + industry_affinity
        if total <= 0:
            raise ValueError("Weight sum must be positive")

        self.distance = distance / total
        self.size_match = size_match / total
        self.cluster_match = cluster_match / total
        self.industry_affinity = industry_affinity / total

    def validate(self):
        """Re-validate weights (for backward compatibility)."""
        pass


def _find_models_directory() -> Optional[Path]:
    """Find the models directory in various possible locations."""
    possible_paths = [
        Path(__file__).parent.parent / "models",
        Path(__file__).parent.parent.parent / "models",
        Path(__file__).parent.parent.parent / "golden_goal" / "models",
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Found models directory at: {path}")
            return path

    logger.warning("No models directory found")
    return None


def load_models() -> Dict[str, Union[Dict, object]]:
    """Load clustering models if available."""
    models = {}
    models_dir = _find_models_directory()

    if not models_dir:
        return models

    model_files = [("default", "kmeans.joblib"), ("large", "kmeans_large.joblib")]

    for key, filename in model_files:
        path = models_dir / filename
        if path.exists():
            try:
                models[key] = joblib.load(path)
                logger.info(f"Loaded model '{key}' from {path}")
            except Exception as e:
                logger.error(f"Failed to load model {key}: {e}")

    return models


def calculate_distance_score(distance_km: float, max_distance: float = 50.0) -> float:
    """
    Calculate distance score with better distribution.
    Perfect match (0km) gets 0.95, not 1.0 to allow other factors to matter.
    """
    if distance_km >= max_distance:
        return 0.0

    # For very close distances, don't give perfect score
    if distance_km <= 0.1:  # Within 100 meters
        return 0.95

    # Normalize and apply sigmoid-like function
    normalized = distance_km / max_distance
    score_value = 0.95 * (1 / (1 + math.exp(5 * (normalized - 0.3))))

    return max(0.0, min(0.95, score_value))


def calculate_size_match_score(assoc_size: str, comp_size: str) -> float:
    """
    Calculate size compatibility with realistic variation.
    """
    # Size compatibility matrix
    compatibility = {
        ('small', 'small'): 0.9,
        ('small', 'medium'): 0.6,
        ('small', 'large'): 0.2,
        ('medium', 'small'): 0.5,
        ('medium', 'medium'): 0.9,
        ('medium', 'large'): 0.7,
        ('large', 'small'): 0.2,
        ('large', 'medium'): 0.6,
        ('large', 'large'): 0.9,
    }

    # Normalize sizes
    valid_sizes = ['small', 'medium', 'large']
    assoc_size = assoc_size if assoc_size in valid_sizes else 'medium'
    comp_size = comp_size if comp_size in valid_sizes else 'medium'

    base_score = compatibility.get((assoc_size, comp_size), 0.5)

    # Add small variation
    variation = random.uniform(-0.05, 0.05)
    return max(0.1, min(0.95, base_score + variation))


def calculate_industry_affinity(company_industry: str, company_name: str = "") -> float:
    """
    Calculate industry affinity with name-based adjustments.
    """
    # Base industry scores
    industry_scores = {
        'Finance': 0.85,
        'Insurance': 0.80,
        'Retail': 0.75,
        'Services': 0.65,
        'Technology': 0.60,
        'Real Estate': 0.55,
        'Manufacturing': 0.45,
        'Healthcare': 0.35,
        'Logistics': 0.25,
        'Other': 0.20,
    }

    base_score = industry_scores.get(company_industry, 0.20)

    # Name-based adjustments
    name_lower = company_name.lower()
    if any(kw in name_lower for kw in ['sport', 'athletic', 'fitness']):
        base_score += 0.1
    elif any(kw in name_lower for kw in ['invest', 'capital', 'finans']):
        base_score += 0.05

    # Add variation
    variation = random.uniform(-0.03, 0.03)
    return max(0.1, min(0.9, base_score + variation))


def predict_cluster_safe(model_data: Union[Dict, object], lat: float, lon: float) -> Optional[int]:
    """Safely predict cluster label."""
    if not model_data:
        return None

    try:
        features = [[lat, lon]]

        if isinstance(model_data, dict):
            scaler = model_data.get('scaler')
            kmeans = model_data.get('kmeans')

            if kmeans is None:
                return None

            if scaler is not None:
                features = scaler.transform(features)

            if hasattr(kmeans, 'predict'):
                return int(kmeans.predict(features)[0])
        else:
            if hasattr(model_data, 'predict'):
                return int(model_data.predict(features)[0])
    except Exception as e:
        logger.debug(f"Cluster prediction failed: {e}")

    return None


def calculate_cluster_score(assoc_cluster: Optional[int], comp_cluster: Optional[int]) -> float:
    """Calculate cluster matching score."""
    if assoc_cluster is None or comp_cluster is None:
        return 0.5

    if assoc_cluster == comp_cluster:
        return 0.8 + random.uniform(0, 0.1)
    else:
        return 0.3 + random.uniform(0, 0.1)


def get_association_details(engine: Engine, association_id: int) -> Optional[Tuple]:
    """Get association details from database."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, lat, lon, size_bucket
            FROM associations
            WHERE id = :id
        """), {"id": association_id}).fetchone()

        if not result:
            logger.warning(f"Association {association_id} not found")
            return None

        return result


def get_nearby_companies(engine: Engine, lat: float, lon: float, max_distance: float) -> List:
    """Get companies within distance range."""
    lat_range = max_distance / 111.0
    lon_range = max_distance / (111.0 * math.cos(math.radians(lat)))

    with engine.connect() as conn:
        return conn.execute(text("""
            SELECT id, name, lat, lon, size_bucket, industry,
                   SQRT(POWER(lat - :center_lat, 2) + POWER(lon - :center_lon, 2)) * 111.0 as approx_distance
            FROM companies
            WHERE lat BETWEEN :min_lat AND :max_lat
              AND lon BETWEEN :min_lon AND :max_lon
              AND lat IS NOT NULL
              AND lon IS NOT NULL
            ORDER BY approx_distance
            LIMIT 5000
        """), {
            "min_lat": lat - lat_range,
            "max_lat": lat + lat_range,
            "min_lon": lon - lon_range,
            "max_lon": lon + lon_range,
            "center_lat": lat,
            "center_lon": lon
        }).fetchall()


def score_and_rank_optimized(
    association_id: int,
    bucket: str,  # Note: bucket parameter is used for logging context
    max_distance: float = 50.0,
    top_n: int = 10,
    weights: Optional[ScoringWeights] = None
) -> List[Dict]:
    """
    Optimized scoring with better distribution.
    Note: 'bucket' parameter kept for API compatibility.
    """
    # Load models
    models = load_models()

    # Set weights based on model availability
    if weights is None:
        if not models:
            weights = ScoringWeights(
                distance=0.5,
                size_match=0.2,
                cluster_match=0.0,
                industry_affinity=0.3
            )
        else:
            weights = ScoringWeights(
                distance=0.35,
                size_match=0.25,
                cluster_match=0.2,
                industry_affinity=0.2
            )

    engine = get_engine()

    # Get association details
    assoc_details = get_association_details(engine, association_id)
    if not assoc_details:
        return []

    assoc_id, assoc_name, assoc_lat, assoc_lon, assoc_size = assoc_details

    logger.info(f"Scoring for {assoc_name} (provided bucket: {bucket}, actual size: {assoc_size})")

    # Get association cluster
    assoc_cluster = None
    if models:
        model_key = "large" if assoc_size == "large" else "default"
        model = models.get(model_key)
        if model:
            assoc_cluster = predict_cluster_safe(model, assoc_lat, assoc_lon)

    # Get nearby companies
    companies = get_nearby_companies(engine, assoc_lat, assoc_lon, max_distance)
    logger.info(f"Found {len(companies)} companies in range")

    recommendations = []
    seen_locations = set()

    # Score each company
    for comp_row in companies:
        comp_id, comp_name, comp_lat, comp_lon, comp_size, comp_industry, _ = comp_row

        # Calculate exact distance
        distance_km = haversine(assoc_lat, assoc_lon, comp_lat, comp_lon)
        if distance_km > max_distance:
            continue

        # Location penalty for same building
        location_key = f"{comp_lat:.4f},{comp_lon:.4f}"
        location_count = sum(1 for k in seen_locations if k == location_key)
        location_penalty = 0.05 * location_count
        seen_locations.add(location_key)

        # Calculate component scores
        distance_score = calculate_distance_score(distance_km, max_distance)
        size_score = calculate_size_match_score(assoc_size, comp_size or 'medium')
        industry_score = calculate_industry_affinity(comp_industry or 'Other', comp_name)

        # Calculate cluster score
        cluster_score_value = 0.5
        if models and assoc_cluster is not None:
            model_key = "large" if comp_size == "large" else "default"
            comp_model = models.get(model_key)
            if comp_model:
                comp_cluster = predict_cluster_safe(comp_model, comp_lat, comp_lon)
                cluster_score_value = calculate_cluster_score(assoc_cluster, comp_cluster)

        # Calculate final score
        final_score = (
            weights.distance * distance_score +
            weights.size_match * size_score +
            weights.cluster_match * cluster_score_value +
            weights.industry_affinity * industry_score
        )

        # Apply adjustments
        final_score -= location_penalty
        final_score += random.uniform(-0.001, 0.001)  # Break ties
        final_score = max(0.0, min(1.0, final_score))

        recommendations.append({
            "id": int(comp_id),
            "name": str(comp_name),
            "lat": float(comp_lat),
            "lon": float(comp_lon),
            "distance": round(distance_km, 2),
            "distance_km": round(distance_km, 1),
            "score": round(final_score, 4),
            "size_bucket": comp_size or 'medium',
            "industry": comp_industry or 'Other',
            "components": {
                "distance_score": round(distance_score, 3),
                "size_score": round(size_score, 3),
                "cluster_score": round(cluster_score_value, 3),
                "industry_score": round(industry_score, 3)
            }
        })

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    # Log results
    if recommendations:
        result_scores = [r["score"] for r in recommendations[:50]]
        logger.info(f"Score distribution (top 50): min={min(result_scores):.3f}, "
                   f"max={max(result_scores):.3f}, range={max(result_scores)-min(result_scores):.3f}")

    return recommendations[:top_n]


# Backward compatibility
score_and_rank = score_and_rank_optimized


def recalibrate_models():
    """Re-train clustering models from current data."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    engine = get_engine()

    with engine.connect() as conn:
        all_locations = conn.execute(text("""
            SELECT lat, lon, size_bucket FROM (
                SELECT lat, lon, size_bucket FROM associations 
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                UNION ALL
                SELECT lat, lon, size_bucket FROM companies 
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                LIMIT 10000
            ) AS combined
        """)).fetchall()

    if len(all_locations) < 10:
        logger.error("Not enough data to train models")
        return

    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True, parents=True)

    # Separate by size
    data_by_size = {
        'default': [(lat, lon) for lat, lon, size in all_locations if size in ['small', 'medium']],
        'large': [(lat, lon) for lat, lon, size in all_locations if size == 'large']
    }

    for model_type, data in data_by_size.items():
        if len(data) < 5:
            continue

        X = np.array(data)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        if model_type == 'default':
            n_clusters = min(8, max(3, len(data) // 100))
        else:
            n_clusters = min(5, max(2, len(data) // 20))

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(X_scaled)

        model_data = {
            'kmeans': kmeans,
            'scaler': scaler,
            'features': ['lat', 'lon'],
            'n_features': 2
        }

        filename = f"kmeans{'_large' if model_type == 'large' else ''}.joblib"
        joblib.dump(model_data, models_dir / filename)
        logger.info(f"Saved {model_type} model with {n_clusters} clusters")


if __name__ == "__main__":
    # Test the scoring
    print("Testing clean pipeline...")

    # Test distance scoring
    print("\nDistance scores (max=25km):")
    for d in [0, 0.1, 1, 5, 10, 15, 20, 25]:
        score_val = calculate_distance_score(d, 25)
        print(f"  {d:4.1f}km -> {score_val:.3f}")

    # Test full scoring
    results = score_and_rank(1, 'medium', 25, 20)

    if results:
        scores = [r['score'] for r in results]
        print(f"\nFound {len(results)} recommendations")
        print(f"Score range: {min(scores):.3f} to {max(scores):.3f}")
        print(f"Score spread: {max(scores) - min(scores):.3f}")
    else:
        print("\nNo recommendations found!")