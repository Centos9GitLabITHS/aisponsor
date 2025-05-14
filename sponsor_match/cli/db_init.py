#!/usr/bin/env python3
"""
sponsor_match/db_init.py
------------------------
Create (if needed) the `clubs` and `companies` tables in MySQL.

Usage:
    python -m sponsor_match.db_init
"""

import logging
from argparse import ArgumentParser
from textwrap import dedent
from sponsor_match.core.db import get_engine

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DDL = dedent("""
    CREATE TABLE IF NOT EXISTS clubs (
        id           INT PRIMARY KEY AUTO_INCREMENT,
        name         VARCHAR(120),
        size_bucket  ENUM('small','medium','large'),
        lat          DOUBLE,
        lon          DOUBLE
    ) CHARACTER SET utf8mb4;

    CREATE TABLE IF NOT EXISTS companies (
        id            INT PRIMARY KEY AUTO_INCREMENT,
        orgnr         CHAR(10),
        name          VARCHAR(200),
        revenue_ksek  DOUBLE,
        employees     INT,
        year          INT,
        rev_per_emp   DOUBLE,
        size_bucket   ENUM('small','medium','large'),
        industry      VARCHAR(120),
        lat           DOUBLE,
        lon           DOUBLE
    ) CHARACTER SET utf8mb4;
""")

def main(dry_run: bool = False) -> None:
    """
    Execute the DDL statements to ensure tables exist.
    If dry_run is True, only logs the statements without executing.
    """
    engine = get_engine()
    logger.info("Connecting to database")
    if dry_run:
        logger.info("Dry run mode: the following statements would be executed:\n%s", DDL)
        return

    try:
        with engine.begin() as conn:
            for stmt in DDL.strip().split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                conn.exec_driver_sql(stmt)
                logger.info("Executed DDL: %s", stmt.splitlines()[0])
        logger.info("✅ Tables `clubs` and `companies` are ready")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
        raise

if __name__ == "__main__":
    parser = ArgumentParser(description="Initialize MySQL tables for SponsorMatch")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show DDL without executing"
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
