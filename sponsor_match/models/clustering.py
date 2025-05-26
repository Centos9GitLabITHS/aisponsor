# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
sponsor_match/models/clustering.py

Enhanced clustering implementation with multiple algorithms, validation metrics,
and proper integration with geocoded data. This replaces the basic K-means
with a more sophisticated approach.
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from sponsor_match.core.config import DATA_DIR, MODELS_DIR, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_N_CLUSTERS = 5
DBSCAN_MIN_SAMPLES = 5
MODEL_VERSION = "2.0"  # Track model versions for compatibility


@dataclass
class ClusteringMetrics:
    """Store clustering quality metrics."""
    silhouette_score: float
    calinski_harabasz_score: float
    davies_bouldin_score: float
    n_clusters: int
    n_noise_points: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @property
    def quality_score(self) -> float:
        """
        Combined quality score (0-1 range).
        Higher silhouette and calinski_harabasz are better.
        Lower davies_bouldin is better.
        """
        # Normalize each metric to 0-1 range
        sil_norm = (self.silhouette_score + 1) / 2  # -1 to 1 -> 0 to 1

        # Calinski-Harabasz doesn't have a fixed range, use sigmoid
        ch_norm = 1 / (1 + np.exp(-self.calinski_harabasz_score / 1000))

        # Davies-Bouldin: lower is better, typical range 0-2
        db_norm = 1 - min(self.davies_bouldin_score / 2, 1)

        # Weighted average
        return 0.5 * sil_norm + 0.3 * ch_norm + 0.2 * db_norm


class GeographicClusteringModel:
    """
    Advanced clustering model for geographic sponsor-association matching.

    This class implements multiple clustering algorithms optimized for
    geographic data, with proper validation and metric tracking.
    """

    def __init__(
            self,
            algorithm: str = 'kmeans',
            n_clusters: int = DEFAULT_N_CLUSTERS,
            random_state: int = 42
    ):
        """
        Initialize clustering model.

        Args:
            algorithm: One of 'kmeans', 'dbscan', 'hierarchical'
            n_clusters: Number of clusters (ignored for DBSCAN)
            random_state: Random seed for reproducibility
        """
        self.algorithm = algorithm
        self.n_clusters = n_clusters
        self.random_state = random_state

        self.scaler = StandardScaler()
        self.model = None
        self.metrics_ = None
        self.feature_names_ = None
        self.model_metadata_ = {
            'version': MODEL_VERSION,
            'algorithm': algorithm,
            'trained': False
        }

    def fit(self, X: Union[np.ndarray, pd.DataFrame],
            feature_names: Optional[List[str]] = None) -> 'GeographicClusteringModel':
        """
        Fit the clustering model with automatic parameter optimization.

        Args:
            X: Feature matrix (n_samples, n_features)
            feature_names: Optional list of feature names

        Returns:
            Self for method chaining
        """
        # Convert to numpy array if needed
        if isinstance(X, pd.DataFrame):
            if feature_names is None:
                feature_names = X.columns.tolist()
            X = X.values

        self.feature_names_ = feature_names or [f'feature_{i}' for i in range(X.shape[1])]

        # Validate input
        if X.shape[0] < 2:
            raise ValueError("Need at least 2 samples for clustering")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model based on algorithm
        if self.algorithm == 'kmeans':
            self._fit_kmeans(X_scaled)
        elif self.algorithm == 'dbscan':
            self._fit_dbscan(X_scaled)
        elif self.algorithm == 'hierarchical':
            self._fit_hierarchical(X_scaled)
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")

        # Calculate metrics
        self._calculate_metrics(X_scaled)

        # Update metadata
        self.model_metadata_['trained'] = True
        self.model_metadata_['n_samples'] = X.shape[0]
        self.model_metadata_['n_features'] = X.shape[1]

        logger.info(f"Trained {self.algorithm} model - Quality score: {self.metrics_.quality_score:.3f}")

        return self

    def _fit_kmeans(self, X_scaled: np.ndarray):
        """Fit K-means with optimal parameters."""
        # Determine optimal number of clusters if not specified
        if self.n_clusters == 'auto':
            self.n_clusters = self._find_optimal_clusters(X_scaled)

        self.model = KMeans(
            n_clusters=min(self.n_clusters, X_scaled.shape[0]),
            init='k-means++',
            n_init=10,
            max_iter=300,
            random_state=self.random_state
        )
        self.model.fit(X_scaled)

    def _fit_dbscan(self, X_scaled: np.ndarray):
        """Fit DBSCAN with adaptive epsilon."""
        # Find optimal epsilon using k-nearest neighbors
        eps = self._find_optimal_eps(X_scaled)

        self.model = DBSCAN(
            eps=eps,
            min_samples=min(DBSCAN_MIN_SAMPLES, X_scaled.shape[0] // 10),
            metric='euclidean',
            n_jobs=-1
        )
        self.model.fit(X_scaled)

        # DBSCAN doesn't have n_clusters attribute
        unique_labels = set(self.model.labels_)
        self.n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)

    def _fit_hierarchical(self, X_scaled: np.ndarray):
        """Fit Agglomerative Clustering."""
        self.model = AgglomerativeClustering(
            n_clusters=min(self.n_clusters, X_scaled.shape[0]),
            linkage='ward'
        )
        self.model.fit(X_scaled)

    def _find_optimal_clusters(self, X_scaled: np.ndarray, max_k: int = 10) -> int:
        """
        Find optimal number of clusters using elbow method and silhouette score.
        """
        max_k = min(max_k, X_scaled.shape[0] - 1)

        scores = []
        for k in range(2, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=self.random_state)
            labels = kmeans.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            scores.append((k, score))

        # Find k with highest silhouette score
        optimal_k = max(scores, key=lambda x: x[1])[0]
        logger.info(f"Optimal clusters determined: {optimal_k}")

        return optimal_k

    def _find_optimal_eps(self, X_scaled: np.ndarray, n_neighbors: int = 5) -> float:
        """
        Find optimal DBSCAN epsilon using k-nearest neighbors.
        """
        nn = NearestNeighbors(n_neighbors=n_neighbors)
        nn.fit(X_scaled)
        distances, _ = nn.kneighbors(X_scaled)

        # Sort distances and find "elbow"
        sorted_distances = np.sort(distances[:, -1])

        # Use 90th percentile as epsilon
        eps = np.percentile(sorted_distances, 90)

        logger.info(f"Optimal epsilon determined: {eps:.4f}")
        return eps

    def _calculate_metrics(self, X_scaled: np.ndarray):
        """Calculate clustering quality metrics."""
        labels = self.predict_raw(X_scaled)

        # Count unique labels (excluding noise for DBSCAN)
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = np.sum(labels == -1)

        # Calculate metrics only if we have valid clusters
        if n_clusters < 2 or n_clusters >= len(labels):
            self.metrics_ = ClusteringMetrics(
                silhouette_score=0.0,
                calinski_harabasz_score=0.0,
                davies_bouldin_score=float('inf'),
                n_clusters=n_clusters,
                n_noise_points=n_noise
            )
        else:
            # Filter out noise points for metric calculation
            mask = labels != -1
            X_filtered = X_scaled[mask]
            labels_filtered = labels[mask]

            self.metrics_ = ClusteringMetrics(
                silhouette_score=silhouette_score(X_filtered, labels_filtered),
                calinski_harabasz_score=calinski_harabasz_score(X_filtered, labels_filtered),
                davies_bouldin_score=davies_bouldin_score(X_filtered, labels_filtered),
                n_clusters=n_clusters,
                n_noise_points=n_noise
            )

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Predict cluster labels for new data.

        Args:
            X: Feature matrix

        Returns:
            Array of cluster labels
        """
        if not self.model_metadata_['trained']:
            raise ValueError("Model must be fitted before prediction")

        # Convert to numpy array if needed
        if isinstance(X, pd.DataFrame):
            X = X.values

        # Scale features
        X_scaled = self.scaler.transform(X)

        return self.predict_raw(X_scaled)

    def predict_raw(self, X_scaled: np.ndarray) -> np.ndarray:
        """Predict on already-scaled data."""
        if self.algorithm == 'kmeans':
            return self.model.predict(X_scaled)
        elif self.algorithm == 'dbscan':
            # DBSCAN doesn't have predict, use fit_predict for new data
            # For consistency, return cluster of nearest core point
            return self._predict_dbscan(X_scaled)
        elif self.algorithm == 'hierarchical':
            # Hierarchical doesn't have predict, find nearest cluster center
            return self._predict_hierarchical(X_scaled)

    def _predict_dbscan(self, X_scaled: np.ndarray) -> np.ndarray:
        """Predict DBSCAN clusters for new points."""
        # Find nearest core points
        core_mask = np.zeros(len(self.model.labels_), dtype=bool)
        core_mask[self.model.core_sample_indices_] = True

        # Get core points
        core_points = X_scaled[core_mask]
        core_labels = self.model.labels_[core_mask]

        # For each new point, find nearest core point
        predictions = []
        for point in X_scaled:
            distances = np.linalg.norm(core_points - point, axis=1)
            nearest_idx = np.argmin(distances)

            # Check if within eps distance
            if distances[nearest_idx] <= self.model.eps:
                predictions.append(core_labels[nearest_idx])
            else:
                predictions.append(-1)  # Noise

        return np.array(predictions)

    def _predict_hierarchical(self, X_scaled: np.ndarray) -> np.ndarray:
        """Predict hierarchical clusters for new points."""
        # Compute cluster centers
        centers = []
        for i in range(self.n_clusters):
            mask = self.model.labels_ == i
            if np.any(mask):
                centers.append(X_scaled[mask].mean(axis=0))

        centers = np.array(centers)

        # Assign to nearest center
        predictions = []
        for point in X_scaled:
            distances = np.linalg.norm(centers - point, axis=1)
            predictions.append(np.argmin(distances))

        return np.array(predictions)

    def save(self, filepath: Union[str, Path]):
        """
        Save the complete model to disk.

        Args:
            filepath: Path to save the model
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'algorithm': self.algorithm,
            'n_clusters': self.n_clusters,
            'metrics': self.metrics_.to_dict() if self.metrics_ else None,
            'feature_names': self.feature_names_,
            'metadata': self.model_metadata_
        }

        joblib.dump(model_data, filepath)
        logger.info(f"Saved model to {filepath}")

        # Also save metrics as JSON for easy inspection
        metrics_path = filepath.with_suffix('.metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump({
                'algorithm': self.algorithm,
                'metrics': self.metrics_.to_dict() if self.metrics_ else None,
                'metadata': self.model_metadata_
            }, f, indent=2)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> 'GeographicClusteringModel':
        """
        Load a saved model from disk.

        Args:
            filepath: Path to the saved model

        Returns:
            Loaded model instance
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")

        model_data = joblib.load(filepath)

        # Handle version compatibility
        metadata = model_data.get('metadata', {})
        version = metadata.get('version', '1.0')

        if version != MODEL_VERSION:
            logger.warning(f"Loading model version {version}, current version is {MODEL_VERSION}")

        # Reconstruct model
        instance = cls(
            algorithm=model_data['algorithm'],
            n_clusters=model_data.get('n_clusters', DEFAULT_N_CLUSTERS)
        )

        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.feature_names_ = model_data.get('feature_names')
        instance.model_metadata_ = metadata

        # Reconstruct metrics if available
        metrics_dict = model_data.get('metrics')
        if metrics_dict:
            instance.metrics_ = ClusteringMetrics(**metrics_dict)

        return instance


def train_clustering_models_for_buckets():
    """
    Train separate clustering models for each size bucket using geocoded data.

    This function loads the geocoded CSVs and trains optimized models for
    different entity sizes (small, medium, large).
    """
    logger.info("Training clustering models with geocoded data...")

    # Load geocoded data
    associations_path = DATA_DIR / "associations_geocoded.csv"
    companies_path = DATA_DIR / "companies_geocoded.csv"

    if not associations_path.exists() or not companies_path.exists():
        logger.error("Geocoded CSV files not found. Please run geocoding first.")
        return

    # Load data
    associations_df = pd.read_csv(associations_path)
    companies_df = pd.read_csv(companies_path)

    # Rename columns for consistency
    if 'lat' in associations_df.columns:
        associations_df = associations_df.rename(columns={'lat': 'latitude', 'lon': 'longitude'})
    if 'lat' in companies_df.columns:
        companies_df = companies_df.rename(columns={'lat': 'latitude', 'lon': 'longitude'})

    # Combine all entities
    all_entities = pd.concat([
        associations_df[['latitude', 'longitude', 'size_bucket']],
        companies_df[['latitude', 'longitude', 'size_bucket']]
    ], ignore_index=True)

    # Filter valid coordinates
    valid_mask = (
            (all_entities['latitude'].between(-90, 90)) &
            (all_entities['longitude'].between(-180, 180))
    )
    all_entities = all_entities[valid_mask]

    logger.info(f"Total valid entities for clustering: {len(all_entities)}")

    # Train models for each size bucket
    models = {}

    for bucket in ['small', 'medium', 'large']:
        bucket_data = all_entities[all_entities['size_bucket'] == bucket]

        if len(bucket_data) < 5:
            logger.warning(f"Insufficient data for {bucket} bucket ({len(bucket_data)} entities)")
            continue

        logger.info(f"\nTraining {bucket} model with {len(bucket_data)} entities...")

        # Prepare features
        features = bucket_data[['latitude', 'longitude']].values

        # Try different algorithms and pick the best
        best_model = None
        best_score = -1

        for algorithm in ['kmeans', 'dbscan', 'hierarchical']:
            try:
                model = GeographicClusteringModel(
                    algorithm=algorithm,
                    n_clusters=min(10, len(bucket_data) // 5)
                )
                model.fit(features, feature_names=['latitude', 'longitude'])

                if model.metrics_.quality_score > best_score:
                    best_score = model.metrics_.quality_score
                    best_model = model

                logger.info(f"  {algorithm}: quality score = {model.metrics_.quality_score:.3f}")

            except Exception as e:
                logger.warning(f"  {algorithm} failed: {e}")

        if best_model:
            # Save the best model
            model_path = MODELS_DIR / f"clustering_{bucket}.joblib"
            best_model.save(model_path)
            models[bucket] = best_model

            logger.info(f"  Best model: {best_model.algorithm} (score: {best_score:.3f})")

    # Also train a combined "default" model for backward compatibility
    logger.info("\nTraining default combined model...")

    default_data = all_entities[all_entities['size_bucket'].isin(['small', 'medium'])]
    if len(default_data) >= 5:
        features = default_data[['latitude', 'longitude']].values

        default_model = GeographicClusteringModel(
            algorithm='kmeans',
            n_clusters=min(10, len(default_data) // 10)
        )
        default_model.fit(features, feature_names=['latitude', 'longitude'])
        default_model.save(MODELS_DIR / "kmeans.joblib")

        logger.info(f"Default model trained with {len(default_data)} entities")

    return models


def analyze_clustering_quality():
    """
    Analyze and report on the quality of existing clustering models.

    This function loads saved models and provides detailed quality metrics.
    """
    logger.info("Analyzing clustering model quality...")

    models_to_check = [
        ('Default', MODELS_DIR / "kmeans.joblib"),
        ('Small', MODELS_DIR / "clustering_small.joblib"),
        ('Medium', MODELS_DIR / "clustering_medium.joblib"),
        ('Large', MODELS_DIR / "clustering_large.joblib"),
    ]

    results = []

    for name, path in models_to_check:
        if not path.exists():
            logger.warning(f"{name} model not found at {path}")
            continue

        try:
            model = GeographicClusteringModel.load(path)

            if model.metrics_:
                results.append({
                    'name': name,
                    'algorithm': model.algorithm,
                    'n_clusters': model.n_clusters,
                    'quality_score': model.metrics_.quality_score,
                    'silhouette': model.metrics_.silhouette_score,
                    'n_noise': model.metrics_.n_noise_points
                })

                logger.info(f"\n{name} Model:")
                logger.info(f"  Algorithm: {model.algorithm}")
                logger.info(f"  Clusters: {model.n_clusters}")
                logger.info(f"  Quality Score: {model.metrics_.quality_score:.3f}")
                logger.info(f"  Silhouette: {model.metrics_.silhouette_score:.3f}")

                if model.metrics_.n_noise_points > 0:
                    logger.info(f"  Noise Points: {model.metrics_.n_noise_points}")

        except Exception as e:
            logger.error(f"Failed to analyze {name} model: {e}")

    # Summary
    if results:
        avg_quality = np.mean([r['quality_score'] for r in results])
        logger.info(f"\nOverall average quality score: {avg_quality:.3f}")

        if avg_quality < 0.5:
            logger.warning("Low clustering quality detected. Consider retraining with different parameters.")

    return results


# Main execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clustering model management")
    parser.add_argument('--train', action='store_true', help='Train new models')
    parser.add_argument('--analyze', action='store_true', help='Analyze existing models')
    parser.add_argument('--algorithm', choices=['kmeans', 'dbscan', 'hierarchical'],
                        default='kmeans', help='Algorithm to use for training')

    args = parser.parse_args()

    if args.train:
        train_clustering_models_for_buckets()
    elif args.analyze:
        analyze_clustering_quality()
    else:
        parser.print_help()
