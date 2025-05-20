#!/usr/bin/env python3
"""
sponsor_match/core/config.py
-----------------------------
Application configuration loaded from Streamlit Secrets or environment variables.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from dataclasses import dataclass, field
from pathlib import Path

# 1) Load .env from project root (if present)
load_dotenv()

# 2) Compute project root once
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 3) Pull MySQL creds from Streamlit Secrets (if you deployed them under [mysql])
mysql_secrets = st.secrets.get("mysql", {})

# 4) Module‐level defaults: secrets → env → hard‐coded
_DEFAULT_DB_HOST     = mysql_secrets.get("host",     os.getenv("MYSQL_HOST",     "localhost"))
_DEFAULT_DB_PORT     = int(      mysql_secrets.get("port",     os.getenv("MYSQL_PORT",     "3306")))
_DEFAULT_DB_USER     = mysql_secrets.get("user",     os.getenv("MYSQL_USER",     ""))
_DEFAULT_DB_PASSWORD = mysql_secrets.get("password", os.getenv("MYSQL_PASSWORD", ""))
_DEFAULT_DB_NAME     = mysql_secrets.get("database", os.getenv("MYSQL_DB",       ""))

@dataclass(frozen=True)
class Config:
    """
    Configuration parameters for SponsorMatch AI.
    Values are read (in order) from Streamlit Secrets → environment variables → defaults.
    """

    # MySQL connection
    db_host:     str = _DEFAULT_DB_HOST
    db_port:     int = _DEFAULT_DB_PORT
    db_user:     str = _DEFAULT_DB_USER
    db_password: str = _DEFAULT_DB_PASSWORD
    db_name:     str = _DEFAULT_DB_NAME

    # Paths
    project_root: Path = _PROJECT_ROOT
    data_dir:     Path = _PROJECT_ROOT / "data"
    models_dir:   Path = _PROJECT_ROOT / "models"

    # Clustering parameters
    kmeans_clusters:   int   = int(os.getenv("KMEANS_CLUSTERS",    "8"))
    kmeans_batch_size: int   = int(os.getenv("KMEANS_BATCH_SIZE", "256"))

    # Business‐rule buckets
    size_buckets: dict = field(default_factory=lambda: {
        "revenue": [0, 5_000_000, 50_000_000, float("inf")],
        "members": [0,   100,       500,   float("inf")],
    })

    # Geocoding settings
    geocoding_delay:   float = float(os.getenv("GEOCODING_DELAY",   "1.1"))
    geocoding_timeout: int   = int(os.getenv("GEOCODING_TIMEOUT", "10"))

    @property
    def db_url(self) -> str:
        """
        Return the SQLAlchemy URL, using MYSQL_URL_OVERRIDE if set,
        otherwise composing from the Config fields.
        """
        # First, allow a full-URL override (can also be set in Streamlit Secrets
        # under a key mysql.url_override, or as env var MYSQL_URL_OVERRIDE)
        override = (
            mysql_secrets.get("url_override")
            or os.getenv("MYSQL_URL_OVERRIDE")
        )
        if override:
            return override

        return (
            f"mysql+mysqlconnector://"
            f"{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/"
            f"{self.db_name}"
        )

# Instantiate a single, shared config object
config = Config()

# Expose uppercase DB_* attributes on the Config class for convenience
Config.DB_HOST     = Config.db_host
Config.DB_PORT     = Config.db_port
Config.DB_USER     = Config.db_user
Config.DB_PASSWORD = Config.db_password
Config.DB_NAME     = Config.db_name
