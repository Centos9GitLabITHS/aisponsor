#!/usr/bin/env python3
"""
sponsor_match/models/clustering.py
----------------------------------
Train MiniBatchKMeans models on club geocoordinates,
one per size bucket, and persist them to disk.
"""

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import MiniBatchKMeans

from sponsor_match.core.db import get_engine
from sponsor_match.core.config import config

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

MODEL_DIR: Path = config.models_dir
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def train_kmeans_for_bucket(size_bucket: str) -> None:
    logger.info("Loading clubs in bucket '%s'", size_bucket)
    engine = get_engine()

    # Inline the bucket value for compatibility
    sql = f"SELECT lat, lon FROM clubs WHERE size_bucket = '{size_bucket}'"
    df = pd.read_sql(sql, engine)

    coords = df.dropna(subset=["lat", "lon"]).to_numpy()
    if coords.size == 0:
        logger.warning("No coordinates found for bucket '%s'; skipping", size_bucket)
        return

    logger.info(
        "Training MiniBatchKMeans (n_clusters=%d, batch_size=%d) on %d points",
        config.kmeans_clusters,
        config.kmeans_batch_size,
        len(coords),
    )
    km = MiniBatchKMeans(
        n_clusters=config.kmeans_clusters,
        batch_size=config.kmeans_batch_size,
        random_state=42
    )
    km.fit(coords)

    out_path = MODEL_DIR / f"kmeans_{size_bucket}.joblib"
    joblib.dump(km, out_path)
    logger.info("Saved KMeans model to %s", out_path)

def main() -> None:
    for bucket in ["small", "medium", "large"]:
        train_kmeans_for_bucket(bucket)

if __name__ == "__main__":
    main()
