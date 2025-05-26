#!/usr/bin/env python3
"""
sponsor_match/core/db.py
-------------------------
Database engine factory using SQLAlchemy.
"""

import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()
_engine = None

def get_engine():
    """
    Get or create the global database engine.
    Reads the URL from sponsor_match.core.config.DATABASE_URL.
    """
    global _engine
    if _engine is None:
        from sponsor_match.core.config import DATABASE_URL

        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL not configured")

        try:
            _engine = create_engine(
                DATABASE_URL,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )
            logging.info("Database engine created successfully")
        except SQLAlchemyError as e:
            logging.error(f"Failed to create database engine: {e}")
            raise
    return _engine
