#!/usr/bin/env python3
"""
sponsor_match/models/clustering.py

Defines clustering logic for SponsorMatch AI: training, saving, loading, and inference.
"""
import os
import pickle
import logging
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans

from sponsor_match.core.config import DATA_DIR, MODELS_DIR, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(message)s"
)

# Constants
MODEL_FILE = MODELS_DIR / os.getenv("CLUSTER_MODEL_FILE", "kmeans.pkl")
N_CLUSTERS = int(os.getenv("N_CLUSTERS", 5))
RANDOM_STATE = int(os.getenv("CLUSTER_RANDOM_STATE", 42))
FEATURE_COLUMNS = ["latitude", "longitude"]


def train(
    input_csv: Path = None,
    model_file: Path = None,
    n_clusters: int = N_CLUSTERS,
    random_state: int = RANDOM_STATE,
):
    """
    Train a KMeans clustering model on the association data and save the model to disk.
    """
    if input_csv is None:
        input_csv = DATA_DIR / "associations_goteborg_with_coords.csv"
    if model_file is None:
        model_file = MODEL_FILE

    if not Path(input_csv).exists():
        logging.error(f"Input CSV not found: {input_csv}")
        return

    # Load data
    df = pd.read_csv(input_csv)
    if not all(col in df.columns for col in FEATURE_COLUMNS):
        logging.error(f"Required columns not found in CSV: {FEATURE_COLUMNS}")
        return
    features = df[FEATURE_COLUMNS].dropna()
    if features.empty:
        logging.error("No valid feature data available for clustering.")
        return

    # Train model
    model = KMeans(n_clusters=n_clusters, random_state=random_state)
    model.fit(features)

    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Save model
    with open(model_file, "wb") as f:
        pickle.dump(model, f)
    logging.info(f"Trained KMeans ({n_clusters} clusters) and saved to {model_file}")


def load_model(model_file: Path = None):
    """
    Load the clustering model from disk.
    """
    if model_file is None:
        model_file = MODEL_FILE
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")
    with open(model_file, "rb") as f:
        model = pickle.load(f)
    return model


def predict(lat: float, lon: float, model=None):
    """
    Predict the cluster label for a given latitude and longitude.
    """
    if model is None:
        model = load_model()
    cluster = model.predict([[lat, lon]])
    return int(cluster[0])


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Train or retrain the clustering model.")
    parser.add_argument("--input-csv", type=Path, help="Path to associations CSV")
    parser.add_argument("--output-model", type=Path, help="Path to save trained model")
    parser.add_argument("--n-clusters", type=int, default=N_CLUSTERS, help="Number of clusters")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE, help="Random seed")
    args = parser.parse_args()

    train(
        input_csv=args.input_csv,
        model_file=args.output_model,
        n_clusters=args.n_clusters,
        random_state=args.random_state,
    )
