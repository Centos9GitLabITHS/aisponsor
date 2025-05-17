#!/usr/bin/env python3
"""
sponsor_match/core/config.py
-----------------------------
Application configuration loaded from environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load variables from .env into the environment (if present)
load_dotenv()


@dataclass(frozen=True)
class Config:
    """
    Configuration parameters for SponsorMatch AI.
    Values are read from environment variables with sensible defaults.
    """

    # Database connection
    db_host: str = os.getenv("MYSQL_HOST", "localhost")
    db_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    db_user: str = os.getenv("MYSQL_USER", "sponsor_user")
    db_password: str = os.getenv("MYSQL_PASSWORD", "")
    db_name: str = os.getenv("MYSQL_DB", "sponsor_registry")

    # Project paths
    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = project_root / "data"
    models_dir: Path = project_root / "models"

    # KMeans parameters
    kmeans_clusters: int = int(os.getenv("KMEANS_CLUSTERS", "8"))
    kmeans_batch_size: int = int(os.getenv("KMEANS_BATCH_SIZE", "256"))

    # Business rules for bucketing
    size_buckets: dict = field(
        default_factory=lambda: {
            "revenue": [0, 5_000_000, 50_000_000, float("inf")],
            "members": [0, 100, 500, float("inf")],
        }
    )

    # Geocoding settings
    geocoding_delay: float = float(os.getenv("GEOCODING_DELAY", "1.1"))
    geocoding_timeout: int = int(os.getenv("GEOCODING_TIMEOUT", "10"))


# Instantiate a single, immutable config object for the app to use
config = Config()
