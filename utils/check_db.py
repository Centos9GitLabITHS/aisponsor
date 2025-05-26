# Utility to verify database connectivity and inspect tables
# Detailed comments have been inserted in British English.

#!/usr/bin/env python3
"""
utils/check_db.py

Utility to verify database connectivity and inspect tables.
"""

# Standard library or third-party import
import logging
# Standard library or third-party import
import sys

# Standard library or third-party import
from dotenv import load_dotenv
# Standard library or third-party import
from sqlalchemy import inspect

# Standard library or third-party import
from sponsor_match.core.db import get_engine


# Definition of function 'main': explains purpose and parameters
def main():
    # Load environment variables (e.g. DATABASE_URL)
    load_dotenv()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # Create/get the SQLAlchemy engine
    try:
        engine = get_engine()
    except RuntimeError as e:
        logging.error(f"Could not create database engine: {e}")
        sys.exit(1)

    # Inspect the database
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if not tables:
        logging.warning("No tables found in the database.")
        return

    logging.info(f"Found tables: {tables}")

    # For each table, count rows
    for table in tables:
        try:
            with engine.connect() as conn:
                result = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
            logging.info(f"Table '{table}' has {count} records.")
        except Exception as e:
            logging.error(f"Error querying table '{table}': {e}")

# Entry point check: script execution starts here when run directly
if __name__ == "__main__":
    main()