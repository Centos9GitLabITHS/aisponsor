import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        # Get URL from config
        from sponsor_match.core.config import DATABASE_URL

        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL not configured")

        try:
            _engine = create_engine(
                DATABASE_URL,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                pool_pre_ping=True,  # Test connections before use
                echo=False,
            )
            logging.info("Database engine created successfully")
        except SQLAlchemyError as e:
            logging.error(f"Failed to create database engine: {e}")
            raise
    return _engine
