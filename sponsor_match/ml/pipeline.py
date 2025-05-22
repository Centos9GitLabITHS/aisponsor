import math
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import text

from sponsor_match.core.db import get_engine

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DEFAULT_KMEANS = MODELS_DIR / "kmeans.joblib"
LARGE_KMEANS = MODELS_DIR / "kmeans_large.joblib"


def haversine(lat1, lon1, lat2, lon2):
    """Compute great-circle distance (km) between two points."""
    R = 6371.0
    phi1, lam1, phi2, lam2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dphi = phi2 - phi1
    dlam = lam2 - lam1
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def size_bucket_to_numeric(size_bucket):
    """Convert size bucket to numeric value."""
    mapping = {"small": 0, "medium": 1, "large": 2}
    return mapping.get(size_bucket, 1)


def load_models():
    """Load clustering models with error handling."""
    try:
        models = {}
        if DEFAULT_KMEANS.exists():
            models["default"] = joblib.load(DEFAULT_KMEANS)
        if LARGE_KMEANS.exists():
            models["large"] = joblib.load(LARGE_KMEANS)
        return models if models else None
    except Exception as e:
        print(f"Warning: Could not load models: {e}")
        return None


def safe_predict_cluster(model, features):
    """Safely predict cluster with dimension checking."""
    try:
        # Check model's expected feature count
        expected_features = getattr(model, 'n_features_in_', None)
        if expected_features is None and hasattr(model, 'cluster_centers_'):
            expected_features = model.cluster_centers_.shape[1]

        if expected_features and len(features) != expected_features:
            print(f"Feature mismatch: model expects {expected_features}, got {len(features)}")
            # Pad or truncate features to match
            if len(features) < expected_features:
                features = features + [0] * (expected_features - len(features))
            else:
                features = features[:expected_features]

        return model.predict([features])[0]
    except Exception as e:
        print(f"Clustering prediction failed: {e}")
        return None


def score_and_rank(association_id, bucket, max_distance=50.0, top_n=10):
    """Score and rank potential sponsors with robust error handling."""
    engine = get_engine()

    try:
        with engine.connect() as conn:
            # Get association
            assoc_df = pd.read_sql(
                text("SELECT id,name,lat,lon,size_bucket,member_count FROM associations WHERE id=:i"),
                conn, params={"i": association_id}
            )

            # Get companies
            comps_df = pd.read_sql(
                "SELECT id,name,lat,lon,size_bucket FROM companies WHERE lat IS NOT NULL AND lon IS NOT NULL",
                conn
            )
    except Exception as e:
        print(f"Database error: {e}")
        return []

    if assoc_df.empty:
        return []

    club = assoc_df.iloc[0]

    # Load models
    models = load_models()
    cluster_bonus = 1.0  # Default if clustering fails

    if models:
        model_key = "large" if bucket == "large" else "default"
        model = models.get(model_key)

        if model:
            # Try clustering with fallback
            club_features = [club.lat, club.lon]
            # Add size feature if model expects 3 features
            if hasattr(model, 'cluster_centers_') and model.cluster_centers_.shape[1] == 3:
                club_features.append(size_bucket_to_numeric(getattr(club, 'size_bucket', bucket)))

            club_cluster = safe_predict_cluster(model, club_features)

    recommendations = []
    for _, company in comps_df.iterrows():
        try:
            distance = haversine(club.lat, club.lon, company.lat, company.lon)
            if distance > max_distance:
                continue

            # Size matching bonus
            size_bonus = 1.2 if company.size_bucket == bucket else 1.0

            # Cluster matching bonus (if clustering worked)
            comp_cluster_bonus = 1.0
            if models and club_cluster is not None:
                model_key = "large" if bucket == "large" else "default"
                model = models.get(model_key)
                if model:
                    comp_features = [company.lat, company.lon]
                    if hasattr(model, 'cluster_centers_') and model.cluster_centers_.shape[1] == 3:
                        comp_features.append(size_bucket_to_numeric(company.size_bucket))

                    comp_cluster = safe_predict_cluster(model, comp_features)
                    if comp_cluster is not None and comp_cluster == club_cluster:
                        comp_cluster_bonus = 1.3

            # Calculate final score
            score = (1.0 / (1.0 + distance)) * size_bonus * comp_cluster_bonus

            recommendations.append({
                "id": int(company.id),
                "name": company.name,
                "lat": float(company.lat),
                "lon": float(company.lon),
                "distance": round(distance, 2),
                "score": round(score, 3)
            })

        except Exception as e:
            print(f"Error processing company {company.get('name', 'unknown')}: {e}")
            continue

    # Sort by score and return top N
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations[:top_n]
