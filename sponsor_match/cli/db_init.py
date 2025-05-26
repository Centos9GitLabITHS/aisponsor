# db_init.py
"""
Initialise MySQL tables `associations` and `companies` if they do not already exist.
"""
import logging  # For informative logs
from argparse import ArgumentParser  # CLI parsing
from textwrap import dedent  # For multi-line SQL

from sponsor_match.core.db import get_engine  # Database engine factory

# Configure root logger
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# DDL statements to create required tables
DDL = dedent("""
   CREATE TABLE IF NOT EXISTS associations (
        id             INT PRIMARY KEY AUTO_INCREMENT,
        name           VARCHAR(120),
        member_count   INT,
        address        TEXT,
        lat            DOUBLE,
        lon            DOUBLE,
        size_bucket    ENUM('small','medium','large'),
        founded_year   INT
   ) CHARACTER SET utf8mb4;

   CREATE TABLE IF NOT EXISTS companies (
       id           INT AUTO_INCREMENT PRIMARY KEY,
       orgnr        CHAR(10),
       name         VARCHAR(200),
       revenue_ksek DOUBLE,
       employees    INT,
       year         INT,
       size_bucket  ENUM('small','medium','large'),
       industry     VARCHAR(120),
       lat          DOUBLE,
       lon          DOUBLE
   ) CHARACTER SET utf8mb4;
""")


def main(dry_run: bool = False) -> None:
    """
    Execute the DDL statements. In dry-run mode, only logs the SQL without executing.
    """
    engine = get_engine()
    logger.info("Connecting to database")
    if dry_run:
        logger.info("Dry run mode:\n%s", DDL)
        return

    try:
        # Execute each SQL statement in a transaction
        with engine.begin() as conn:
            for stmt in DDL.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.exec_driver_sql(stmt)
                    logger.info("Executed DDL: %s", stmt.splitlines()[0])
        logger.info("✅ Tables `associations` and `companies` are ready")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
        raise


if __name__ == "__main__":
    parser = ArgumentParser(description="Initialize MySQL tables for SponsorMatch")
    parser.add_argument("--dry-run", action="store_true", help="Show DDL without executing")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
