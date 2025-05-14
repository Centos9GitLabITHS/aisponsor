#!/usr/bin/env python3
"""
sponsor_match/core/db.py
------------------------
Set up and return a SQLAlchemy Engine based on application configuration.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from sponsor_match.core.config import config

# Configure module‐level logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

def get_engine() -> Engine:
    """
    Create and return a SQLAlchemy engine using parameters from the global config.
    Raises if the database password is not set.
    """
    if not config.db_password:
        logger.error(
            "Database password not set. Please set MYSQL_PASSWORD in your environment."
        )
        raise ValueError(
            "Database password not set. Please set MYSQL_PASSWORD in your environment."
        )

    url = (
        f"mysql+mysqlconnector://{config.db_user}:"
        f"{config.db_password}@"
        f"{config.db_host}:{config.db_port}/"
        f"{config.db_name}"
    )
    logger.debug("Creating DB engine with URL: %s", url)
    return create_engine(url, pool_pre_ping=True)
