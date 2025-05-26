#!/usr/bin/env python3
"""
sponsor_match/core/config.py
----------------------------
Application configuration and constants.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

def get_database_url():
    """Construct the database URL with proper encoding for the password."""
    mysql_user = os.getenv("MYSQL_USER", "sponsor_user")
    mysql_password = os.getenv("MYSQL_PASSWORD", "Sports-2025?!")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_db   = os.getenv("MYSQL_DB", "sponsor_registry")

    # URL-encode the password to handle special characters
    encoded_password = quote_plus(mysql_password)
    return f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_db}"

# Database URL constant
DATABASE_URL = get_database_url()

# Application constants
APP_TITLE          = os.getenv("APP_TITLE", "SponsorMatch AI")
LOGO_PATH          = os.getenv("LOGO_PATH", str(BASE_DIR / "assets" / "logo.png"))
STREAMLIT_PAGE_ICON = "⚽"

# Logging and model settings
LOG_LEVEL         = os.getenv("LOG_LEVEL", "INFO")
N_CLUSTERS        = int(os.getenv("N_CLUSTERS", 5))
RANDOM_STATE      = int(os.getenv("CLUSTER_RANDOM_STATE", 42))
