#!/usr/bin/env python3
"""
sponsor_match/core/db.py
------------------------
Set up and return a SQLAlchemy Engine based on application configuration
and environment variables from a `.env` file.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# 1) Load .env from the project root (if present)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# 2) Read DB creds from environment (fallback to config)
from sponsor_match.core.config import config

DB_USER = os.getenv("MYSQL_USER", config.db_user)
DB_PWD = os.getenv("MYSQL_PASSWORD", config.db_password)
DB_HOST = os.getenv("MYSQL_HOST", config.db_host)
DB_PORT = os.getenv("MYSQL_PORT", str(config.db_port))
DB_NAME = os.getenv("MYSQL_DB", config.db_name)

# Configure module‐level logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

def get_engine(url: str | None = None, **kwargs) -> Engine:
    """
    Create and return a SQLAlchemy engine.
    - If `url` is provided, it is used verbatim.
    - Otherwise, environment vars (or config) are used to build the URL.
    """
    if url is None:
        if not DB_PWD:
            logger.error(
                "Database password not set. Please set MYSQL_PASSWORD in your environment."
            )
            raise ValueError(
                "Database password not set. Please set MYSQL_PASSWORD in your environment."
            )
        url = (
            f"mysql+mysqlconnector://{DB_USER}:"
            f"{DB_PWD}@"
            f"{DB_HOST}:{DB_PORT}/"
            f"{DB_NAME}"
        )

    logger.debug("Creating DB engine with URL: %s", url)
    return create_engine(url, pool_pre_ping=True, **kwargs)
