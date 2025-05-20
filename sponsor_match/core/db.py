#!/usr/bin/env python3
"""
sponsor_match/core/db.py
------------------------
Set up and return a SQLAlchemy Engine based on application configuration
and environment variables from a `.env` file.
"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from sponsor_match.core.config import config

# 1) Load .env from the project root (if present)
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# 2) Configure module‐level logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

def get_engine(db_url: str | None = None, **kwargs) -> Engine:
    """
    Create and return a SQLAlchemy Engine.

    Parameters
    ----------
    db_url : Optional[str]
        If provided, used verbatim as the connection URL.
        Otherwise falls back to config.db_url (which may use
        MYSQL_URL_OVERRIDE or the individual MYSQL_* env vars).

    **kwargs : passed through to sqlalchemy.create_engine()

    Returns
    -------
    Engine
        A SQLAlchemy Engine, with pool_pre_ping, echo=False, and future=True by default.
    """
    url = db_url or config.db_url
    logger.debug("Creating DB engine with URL: %s", url)
    return create_engine(
        url,
        pool_pre_ping=True,
        echo=False,
        future=True,
        **kwargs
    )
