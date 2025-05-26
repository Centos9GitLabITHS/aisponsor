# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

# Fix 1: Update sponsor_match/core/config.py
# The password has special characters that need proper URL encoding

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"


# Database configuration - Fixed
def get_database_url():
    mysql_user = os.getenv("MYSQL_USER", "sponsor_user")
    mysql_password = os.getenv("MYSQL_PASSWORD", "Sports-2025?!")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_db = os.getenv("MYSQL_DB", "sponsor_registry")

    # URL encode password to handle special characters
    encoded_password = quote_plus(mysql_password)

    return f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_db}"


DATABASE_URL = get_database_url()

# App constants
APP_TITLE = os.getenv("APP_TITLE", "SponsorMatch AI")
LOGO_PATH = os.getenv("LOGO_PATH", str(BASE_DIR / "assets" / "logo.png"))
STREAMLIT_PAGE_ICON = "⚽"

# Other settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
N_CLUSTERS = int(os.getenv("N_CLUSTERS", 5))
RANDOM_STATE = int(os.getenv("CLUSTER_RANDOM_STATE", 42))